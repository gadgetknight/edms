# models/__init__.py
"""
EDSI Veterinary Management System - Models Package Initializer
Version: 1.1.10
Purpose: Makes model classes available when the 'models' package is imported.
         - SystemConfig references fully removed to defer implementation.
Last Updated: May 23, 2025
Author: Gemini

Changelog:
- v1.1.10 (2025-05-23):
    - Removed SystemConfig from import from .reference_models as it's no longer defined there.
    - Removed SystemConfig from __all__ list.
- v1.1.9 (2025-05-23): (Previous attempt to clean up SystemConfig imports)
    - Removed SystemConfig from import from .reference_models.
    - Removed SystemConfig from __all__ list to defer its implementation.
- v1.1.0 (2025-05-19 - User Uploaded version):
    - Initial version importing various models.
"""

from .base_model import Base, BaseModel

from .user_models import User, Role, UserRole

# Importing all classes defined in reference_models.py (v1.1.13, which does NOT define SystemConfig)
from .reference_models import (
    Species,
    StateProvince,
    ChargeCode,
    Veterinarian,
    Location,
    Transaction,
    TransactionDetail,
    Invoice,
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
    # SystemConfig is NOT imported here.
)

from .horse_models import Horse, HorseOwner, HorseLocation
from .owner_models import Owner, OwnerBillingHistory, OwnerPayment

# If HorseBilling is defined in its own file (e.g., billing_models.py), import it here.
# from .billing_models import HorseBilling # Example

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Role",
    "UserRole",
    "Species",
    "StateProvince",
    "ChargeCode",
    "Veterinarian",
    "Location",
    "Transaction",
    "TransactionDetail",
    "Invoice",
    "Procedure",
    "Drug",
    "TreatmentLog",
    "CommunicationLog",
    "Document",
    "Reminder",
    "Appointment",
    "Horse",
    "HorseOwner",
    "HorseLocation",
    "Owner",
    "OwnerBillingHistory",
    "OwnerPayment",
    # "SystemConfig", # Explicitly NOT included for now
    # "HorseBilling", # Explicitly NOT included for now
]
