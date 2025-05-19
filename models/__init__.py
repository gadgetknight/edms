# models/__init__.py

"""
SQLAlchemy models for EDSI Veterinary Management System
"""

# Import Base first since other modules need it
from .base_model import Base, BaseModel

# Import other models in dependency order
from .user_models import User, SystemConfig, Role, UserRole
from .reference_models import (
    Species,
    StateProvince,
    ChargeCode,
    Veterinarian,
    Location,
    Transaction,
    TransactionDetail,
    Invoice,  # Generic Payment model removed
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
)
from .horse_models import Horse, HorseOwner, HorseLocation, HorseBilling
from .owner_models import (
    Owner,
    OwnerBillingHistory,
    OwnerPayment,
)  # OwnerPayment is the definitive one

# Make Base and all model classes available at package level
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "SystemConfig",
    "Role",
    "UserRole",
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
    "OwnerPayment",  # This is the one we are using for owner payments
    "Transaction",
    "TransactionDetail",
    # "Payment",        # Generic Payment removed from __all__
    "Invoice",
    "Procedure",
    "Drug",
    "TreatmentLog",
    "CommunicationLog",
    "Document",
    "Reminder",
    "Appointment",
]
