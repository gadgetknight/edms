# models/horse_models.py
"""
EDSI Veterinary Management System - Horse Related SQLAlchemy Models
Version: 1.2.15
Purpose: Defines the data models for horses, owners, and their relationships.
         - Removed species_id column and species relationship from Horse model.
Last Updated: May 23, 2025
Author: Gemini

Changelog:
- v1.2.15 (2025-05-23):
    - Horse model: Removed `species_id` column.
    - Horse model: Removed `species` relationship.
- v1.2.14 (2025-05-23):
    - HorseOwner.owner: Ensured `back_populates` is "horse_associations"
      to correctly link with the `Owner.horse_associations` 1-M relationship
      in `owner_models.py`.
- v1.2.13 (2025-05-23):
    - HorseOwner.owner: Changed `back_populates` from "horse_associations" to "horses".
- v1.2.12 (2025-05-23):
    - HorseLocation.location_id: Changed ForeignKey from "locations.id" to "locations.location_id".
    - HorseLocation.location: Updated relationship to use `back_populates="current_horses"`.
    - Horse.species_id: Changed ForeignKey from "species.id" to "species.species_id".
    - Horse.current_location_id: Changed ForeignKey from "locations.id" to "locations.location_id".
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date

from .base_model import Base, BaseModel


class HorseOwner(Base):
    __tablename__ = "horse_owners"
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), primary_key=True)
    percentage_ownership = Column(Numeric(5, 2), nullable=True)

    horse = relationship("Horse", back_populates="owner_associations")
    owner = relationship("Owner", back_populates="horse_associations")


class HorseLocation(BaseModel):
    __tablename__ = "horse_locations"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    date_arrived = Column(Date, nullable=False, default=date.today)
    date_departed = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    horse = relationship("Horse", back_populates="location_history")
    location = relationship("Location", back_populates="current_horses")


class Horse(BaseModel):
    __tablename__ = "horses"

    horse_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_name = Column(String(255), nullable=False, index=True)
    account_number = Column(String(50), index=True, nullable=True)
    # REMOVED: species_id = Column(Integer, ForeignKey("species.species_id"), nullable=True)
    breed = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    sex = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    height_hands = Column(Numeric(4, 2), nullable=True)

    chip_number = Column(String(50), nullable=True, unique=True)
    tattoo_number = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    date_deceased = Column(Date, nullable=True)
    coggins_date = Column(Date, nullable=True)

    current_location_id = Column(
        Integer, ForeignKey("locations.location_id"), nullable=True
    )

    # REMOVED: species = relationship("Species")
    owner_associations = relationship(
        "HorseOwner", back_populates="horse", cascade="all, delete-orphan"
    )
    owners = relationship(
        "Owner", secondary="horse_owners", back_populates="horses", viewonly=True
    )

    location_history = relationship(
        "HorseLocation",
        back_populates="horse",
        order_by="desc(HorseLocation.date_arrived)",
        cascade="all, delete-orphan",
    )
    location = relationship("Location", foreign_keys=[current_location_id])

    @hybrid_property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None

    @validates("chip_number", "tattoo_number")
    def convert_empty_to_none(self, key, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value
