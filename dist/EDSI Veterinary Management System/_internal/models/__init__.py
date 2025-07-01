# models/__init__.py
"""
EDSI Veterinary Management System - Models Package
"""

from .base_model import Base, BaseModel
from .user_models import User, Role, UserRole
from .horse_models import Horse, HorseOwner, HorseLocation
from .owner_models import Owner, OwnerBillingHistory, OwnerPayment
from .reference_models import (
    StateProvince,
    ChargeCodeCategory,
    ChargeCode,
    Veterinarian,
    Location,
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
)
from .financial_models import Transaction, Invoice
from .company_profile_model import CompanyProfile  # ADDED

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
    "StateProvince",
    "ChargeCodeCategory",
    "ChargeCode",
    "Veterinarian",
    "Location",
    "Procedure",
    "Drug",
    "TreatmentLog",
    "CommunicationLog",
    "Document",
    "Reminder",
    "Appointment",
    "Transaction",
    "Invoice",
    "CompanyProfile",  # ADDED
]
