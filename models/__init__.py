# models/__init__.py

"""
SQLAlchemy models for EDSI Veterinary Management System
"""

# Import Base first since other modules need it
from .base_model import Base, BaseModel

# Import other models in dependency order
from .user_models import User, SystemConfig
from .reference_models import Species, StateProvince, ChargeCode, Veterinarian, Location
from .horse_models import Horse, HorseOwner, HorseLocation, HorseBilling
from .owner_models import Owner, OwnerBillingHistory, OwnerPayment

# Make Base available at package level
__all__ = [
    "Base",  # Make sure Base is exported
    "BaseModel",
    "User",
    "SystemConfig",
    "Species",
    "StateProvince",
    "ChargeCode",
    "Veterinarian",
    "Location",
    "Horse",
    "HorseOwner",
    "HorseLocation",
    "HorseBilling",
    "Owner",
    "OwnerBillingHistory",
    "OwnerPayment",
]
