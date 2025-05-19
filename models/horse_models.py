# models/horse_models.py

"""
EDSI Veterinary Management System - Horse Related Models
Version: 1.1.0
Purpose: Defines SQLAlchemy models for Horse, HorseOwner (association),
         HorseLocation (history), and HorseBilling (placeholder).
         Corrected ForeignKey reference in Horse model to Species.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.0 (2025-05-18):
    - Corrected ForeignKey in Horse.species_id to reference 'species.species_id'
      instead of 'species.species_code'.
- v1.0.0 (Date Unknown): Initial definitions.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    Numeric,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime  # For default DateTime values

from .base_model import BaseModel

# Import related models for relationships if not already handled by SQLAlchemy's string resolution
# from .reference_models import Species, Location # Not strictly needed if using string refs for ForeignKey
# from .owner_models import Owner # Not strictly needed if using string refs for ForeignKey


class Horse(BaseModel):
    __tablename__ = "horses"

    horse_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_name = Column(String(100), nullable=False, index=True)
    account_number = Column(
        String(20), nullable=True, index=True
    )  # Can be owner's account or specific to horse

    # --- CORRECTED FOREIGN KEY ---
    # Assuming Species model has 'species_id' as its primary key.
    # The Species model in reference_models.py uses species_id.
    species_id = Column(
        Integer, ForeignKey("species.species_id"), nullable=True
    )  # Was 'species.species_code' implicitly
    # --- END CORRECTION ---

    breed = Column(String(50))
    color = Column(String(50))
    sex = Column(String(10))  # e.g., Male, Female, Gelding, Mare, Stallion
    date_of_birth = Column(Date)
    registration_number = Column(String(50), nullable=True, index=True)
    microchip_id = Column(String(50), nullable=True, unique=True, index=True)
    tattoo = Column(String(50), nullable=True)
    brand = Column(String(50), nullable=True)
    band_tag_number = Column(
        String(50), nullable=True
    )  # e.g. for wild horses or specific IDs

    current_location_id = Column(
        Integer, ForeignKey("locations.location_id"), nullable=True, index=True
    )

    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    species = relationship(
        "Species", backref="horses"
    )  # 'horses' will be collection on Species model
    location = relationship(
        "Location", backref="horses_at_location"
    )  # 'horses_at_location' on Location model

    # Many-to-many relationship with Owner through HorseOwner association table
    owners = relationship(
        "HorseOwner", back_populates="horse", cascade="all, delete-orphan"
    )

    # One-to-many for location history and billing records
    location_history = relationship(
        "HorseLocation", back_populates="horse", cascade="all, delete-orphan"
    )
    billing_records = relationship(
        "HorseBilling", back_populates="horse", cascade="all, delete-orphan"
    )

    # created_by and modified_by are inherited from BaseModel if that's where they are defined
    # If not, they would need to be added here. Assuming BaseModel handles them.

    def __repr__(self):
        return f"<Horse(horse_id={self.horse_id}, name='{self.horse_name}')>"


class HorseOwner(BaseModel):
    """Association table between Horse and Owner, including ownership percentage."""

    __tablename__ = "horse_owners"

    horse_id = Column(Integer, ForeignKey("horses.horse_id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), primary_key=True)
    ownership_percentage = Column(
        Numeric(5, 2), nullable=False, default=100.00
    )  # e.g., 100.00, 50.50
    start_date = Column(Date, default=datetime.utcnow)  # When this ownership started
    end_date = Column(Date, nullable=True)  # When this ownership ended, if applicable

    # Relationships to easily access Horse and Owner objects from this association
    horse = relationship("Horse", back_populates="owners")
    owner = relationship(
        "Owner", back_populates="horses"
    )  # 'horses' collection on Owner model

    # created_by, modified_by from BaseModel

    def __repr__(self):
        return f"<HorseOwner(horse_id={self.horse_id}, owner_id={self.owner_id}, percentage={self.ownership_percentage})>"


class HorseLocation(BaseModel):
    """Tracks the location history of a horse."""

    __tablename__ = "horse_locations"

    horse_location_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    horse_id = Column(
        Integer, ForeignKey("horses.horse_id"), nullable=False, index=True
    )
    location_id = Column(
        Integer, ForeignKey("locations.location_id"), nullable=False, index=True
    )
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True)  # Null if current location
    reason_for_move = Column(String(255), nullable=True)

    horse = relationship("Horse", back_populates="location_history")
    location = relationship(
        "Location"
    )  # No backref needed if Location doesn't need to list all HorseLocation entries directly

    # created_by, modified_by from BaseModel

    def __repr__(self):
        return f"<HorseLocation(horse_id={self.horse_id}, location_id={self.location_id}, start='{self.start_date}')>"


class HorseBilling(BaseModel):  # Placeholder - to be expanded
    """Placeholder for horse-specific billing records or settings."""

    __tablename__ = "horse_billing"

    horse_billing_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(
        Integer, ForeignKey("horses.horse_id"), nullable=False, index=True
    )
    # Example fields (these would need to be thought out for actual billing logic)
    billing_cycle_start_date = Column(Date)
    next_billing_date = Column(Date)
    special_notes = Column(Text)

    horse = relationship("Horse", back_populates="billing_records")

    def __repr__(self):
        return f"<HorseBilling(horse_id={self.horse_id})>"
