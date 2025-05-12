# models/horse_models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class Horse(BaseModel):
    """Basic horse information"""

    __tablename__ = "horses"

    horse_id = Column(Integer, primary_key=True, autoincrement=True)
    horse_name = Column(String(100), nullable=False)
    account_number = Column(String(20))
    species_code = Column(
        String(10), ForeignKey("species.species_code"), nullable=True
    )  # Made nullable
    breed = Column(String(50))
    color = Column(String(50))
    sex = Column(String(10))
    date_of_birth = Column(Date)
    registration_number = Column(String(50))
    microchip_id = Column(String(50))
    tattoo = Column(String(50))
    brand = Column(String(50))
    band_tag_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    current_location_id = Column(Integer, ForeignKey("locations.location_id"))
    created_by = Column(String(20), ForeignKey("users.user_id"))
    modified_by = Column(String(20), ForeignKey("users.user_id"))

    # Relationships
    species = relationship("Species")
    location = relationship("Location")
    created_user = relationship("User", foreign_keys=[created_by])
    modified_user = relationship("User", foreign_keys=[modified_by])
    owners = relationship("HorseOwner", back_populates="horse")
    location_history = relationship("HorseLocation", back_populates="horse")
    billing_records = relationship("HorseBilling", back_populates="horse")


class HorseOwner(BaseModel):
    """Horse ownership percentages"""

    __tablename__ = "horse_owners"

    horse_owner_id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    ownership_percentage = Column(Float)
    start_date = Column(Date)
    end_date = Column(Date)
    is_primary_contact = Column(Boolean, default=False)

    # Relationships
    horse = relationship("Horse", back_populates="owners")
    owner = relationship("Owner", back_populates="horses")


class HorseLocation(BaseModel):
    """Horse location history"""

    __tablename__ = "horse_locations"

    location_history_id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=False)
    arrival_date = Column(DateTime)
    departure_date = Column(DateTime)
    reason = Column(String(255))
    notes = Column(String(500))

    # Relationships
    horse = relationship("Horse", back_populates="location_history")
    location = relationship("Location")


class HorseBilling(BaseModel):
    """Horse billing records"""

    __tablename__ = "horse_billing"

    billing_id = Column(Integer, primary_key=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=False)
    charge_date = Column(DateTime)
    charge_code = Column(String(20), ForeignKey("charge_codes.charge_code"))
    description = Column(String(255))
    quantity = Column(Float)
    unit_price = Column(Float)
    total_amount = Column(Float)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"))
    billing_period = Column(String(20))
    is_reminder = Column(Boolean, default=False)
    reminder_type = Column(String(50))
    veterinarian_id = Column(String(20), ForeignKey("veterinarians.vet_id"))
    created_by = Column(String(20), ForeignKey("users.user_id"))

    # Relationships
    horse = relationship("Horse", back_populates="billing_records")
    charge = relationship("ChargeCode")
    owner = relationship("Owner")
    veterinarian = relationship("Veterinarian")
    created_user = relationship("User")
