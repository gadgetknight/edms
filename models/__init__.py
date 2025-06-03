# models/__init__.py
"""
Initializes the models package, making all data models accessible.
"""

from .base_model import Base, BaseModel
from .user_models import User, Role, UserRole
from .horse_models import Horse, HorseOwner, HorseLocation
from .owner_models import Owner, OwnerBillingHistory, OwnerPayment, Invoice
from .reference_models import (
    StateProvince,
    ChargeCodeCategory,  # ADDED
    ChargeCode,
    Veterinarian,
    Location,
    Transaction,
    TransactionDetail,
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
)

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Role",
    "UserRole",
    "Horse",
    "HorseOwner",
    "HorseLocation",
    "Owner",
    "OwnerBillingHistory",
    "OwnerPayment",
    "Invoice",
    "StateProvince",
    "ChargeCodeCategory",  # ADDED
    "ChargeCode",
    "Veterinarian",
    "Location",
    "Transaction",
    "TransactionDetail",
    "Procedure",
    "Drug",
    "TreatmentLog",
    "CommunicationLog",
    "Document",
    "Reminder",
    "Appointment",
]
