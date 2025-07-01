# models/horse_models.py
"""
EDSI Veterinary Management System - Horse Related SQLAlchemy Models
Version: 1.3.0
Purpose: Defines the data models for horses, owners, and their relationships.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v1.3.0 (2025-06-10):
    - Added missing columns to the Horse model: `reg_number`, `brand`, `band_tag`.
      This resolves warnings during horse creation and ensures all form data is saved.
- v1.2.17 (2025-05-25):
    - Reverted `back_populates` on HorseLocation.location relationship
      to "current_horses" to match expected relationship name on Location model.
- v1.2.16 (2025-05-25):
    - HorseLocation model: Added `is_current_location` (Boolean) column.
- v1.2.15 (2025-05-23):
    - Horse model: Removed `species_id` column and `species` relationship.
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
    is_current_location = Column(Boolean, default=False, nullable=False, index=True)

    horse = relationship("Horse", back_populates="location_history")
    location = relationship("Location", back_populates="current_horses")


class Horse(BaseModel):
    __tablename__ = "horses"

    horse_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_name = Column(String(255), nullable=False, index=True)
    account_number = Column(String(50), index=True, nullable=True)
    breed = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    sex = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    height_hands = Column(Numeric(4, 2), nullable=True)

    chip_number = Column(String(50), nullable=True, unique=True)
    tattoo_number = Column(String(50), nullable=True, unique=True)

    # ADDED Missing columns
    reg_number = Column(String(50), nullable=True)
    brand = Column(String(50), nullable=True)
    band_tag = Column(String(50), nullable=True)

    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    date_deceased = Column(Date, nullable=True)
    coggins_date = Column(Date, nullable=True)

    current_location_id = Column(
        Integer, ForeignKey("locations.location_id"), nullable=True
    )

    owner_associations = relationship(
        "HorseOwner", back_populates="horse", cascade="all, delete-orphan"
    )
    owners = relationship(
        "Owner",
        secondary="horse_owners",
        back_populates="horses",
        viewonly=True,
        lazy="selectin",
    )

    location_history = relationship(
        "HorseLocation",
        back_populates="horse",
        order_by="desc(HorseLocation.date_arrived)",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    location = relationship(
        "Location", foreign_keys=[current_location_id], lazy="joined"
    )

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
