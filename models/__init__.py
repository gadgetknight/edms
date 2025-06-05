# models/__init__.py
"""
EDSI Veterinary Management System - Models Package
Version: (Adjust version as needed)
Purpose: Initializes the models package, making all data models accessible.
         Ensures definitive Transaction and Invoice models from financial_models are primary.
Last Updated: June 4, 2025
Author: Gemini

Changelog:
- (Date): Adjusted imports to prioritize Transaction and Invoice from financial_models.
          Removed direct import of placeholder Transaction from reference_models.
          Commented out placeholder Invoice from owner_models in __all__.
"""

from .base_model import Base, BaseModel
from .user_models import User, Role, UserRole
from .horse_models import Horse, HorseOwner, HorseLocation
from .owner_models import (
    Owner,
    OwnerBillingHistory,
    OwnerPayment,
)  # Invoice placeholder removed from this file directly
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
    # Placeholder Transaction and TransactionDetail removed from reference_models.py
)
from .financial_models import Transaction, Invoice  # Definitive financial models

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
    # Note: The placeholder Invoice from owner_models.py has been removed from that file.
    # The 'Invoice' in this list now unambiguously refers to the one from financial_models.
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
    # New Definitive Models
    "Transaction",
    "Invoice",
]
