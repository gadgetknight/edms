# views/admin/dialogs/__init__.py
"""
EDSI Veterinary Management System - Admin Dialogs Package
"""
from .add_edit_user_dialog import AddEditUserDialog
from .add_edit_location_dialog import AddEditLocationDialog
from .add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .add_edit_charge_code_category_dialog import AddEditChargeCodeCategoryDialog
from .add_edit_owner_dialog import AddEditOwnerDialog
from .company_profile_dialog import CompanyProfileDialog
from .add_edit_veterinarian_dialog import AddEditVeterinarianDialog

__all__ = [
    "AddEditUserDialog",
    "AddEditLocationDialog",
    "AddEditChargeCodeDialog",
    "AddEditChargeCodeCategoryDialog",
    "AddEditOwnerDialog",
    "CompanyProfileDialog",
    "AddEditVeterinarianDialog",
]
