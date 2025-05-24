# models/__init__.py
"""
EDSI Veterinary Management System - Models Package Initializer
Version: 1.1.11
Purpose: Initializes the models package, making models accessible.
         - Removed Species model import and from __all__ list.
Last Updated: May 23, 2025
Author: Your Name / Gemini

Changelog:
- v1.1.11 (2025-05-23):
    - Removed `Species` from imports from `.reference_models`.
    - Removed `Species` from `__all__` list.
- v1.1.10 (2025-05-18 - User Uploaded):
    - Added Veterinarian to imports and __all__.
    - SystemConfig explicitly not included.
- v1.0.0 (Date Unknown): Initial setup.
"""

from .base_model import Base, BaseModel
from .user_models import (
    User,
    Role,
    UserRole,
)  # SystemConfig is also in user_models.py v1.1.1

# If SystemConfig needs to be globally accessible via `from models import SystemConfig`, add it here.
# from .user_models import SystemConfig (Example if needed)

from .horse_models import Horse, HorseOwner, HorseLocation
from .owner_models import Owner, OwnerPayment, Invoice, OwnerBillingHistory
from .reference_models import (
    Location,
    Transaction,
    TransactionDetail,
    ChargeCode,
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
    StateProvince,
    Veterinarian,  # REMOVED Species
)


__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Role",
    "UserRole",
    # "SystemConfig", # Still commented out as per original __init__.py, though it exists in user_models.py v1.1.1
    "Horse",
    "HorseOwner",
    "HorseLocation",
    "Owner",
    "OwnerPayment",
    "Invoice",
    "OwnerBillingHistory",
    "Location",
    "Transaction",
    "TransactionDetail",
    "ChargeCode",
    "Procedure",
    "Drug",
    "TreatmentLog",
    "CommunicationLog",
    "Document",
    "Reminder",
    "Appointment",
    "StateProvince",
    # "Species", # REMOVED
    "Veterinarian",
]
