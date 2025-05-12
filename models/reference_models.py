# models/reference_models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class Species(BaseModel):
    """Species lookup table (Equine, Bovine, etc.)"""

    __tablename__ = "species"

    species_code = Column(String(10), primary_key=True)
    species_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)


class StateProvince(BaseModel):
    """States and provinces lookup table"""

    __tablename__ = "states_provinces"

    state_code = Column(String(10), primary_key=True)
    state_name = Column(String(100), nullable=False)
    country_code = Column(String(10), default="US")
    is_active = Column(Boolean, default=True)


class ChargeCode(BaseModel):
    """Charge codes for billing"""

    __tablename__ = "charge_codes"

    charge_code = Column(String(20), primary_key=True)
    category = Column(String(50))
    description = Column(String(255), nullable=False)
    default_units = Column(Float)
    default_amount = Column(Float)
    gl_account = Column(String(20))
    is_active = Column(Boolean, default=True)


class Veterinarian(BaseModel):
    """Veterinarians table"""

    __tablename__ = "veterinarians"

    vet_id = Column(String(20), primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    phone = Column(String(20))
    email = Column(String(100))


class Location(BaseModel):
    """Locations where horses are kept"""

    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String(100), nullable=False)
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state_code = Column(String(10), ForeignKey("states_provinces.state_code"))
    zip_code = Column(String(20))
    is_active = Column(Boolean, default=True)

    # Relationship
    state = relationship("StateProvince", back_populates="locations")


# Add the reverse relationship
StateProvince.locations = relationship("Location", back_populates="state")
