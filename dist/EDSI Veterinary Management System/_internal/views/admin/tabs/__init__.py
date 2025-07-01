# views/admin/tabs/__init__.py
"""
EDSI Veterinary Management System - Admin Tabs Package
"""
# CORRECTED: Changed imports to point to the 'dialogs' subdirectory
from ..dialogs.add_edit_user_dialog import AddEditUserDialog
from ..dialogs.add_edit_location_dialog import AddEditLocationDialog
from ..dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog
from ..dialogs.add_edit_charge_code_category_dialog import (
    AddEditChargeCodeCategoryDialog,
)
from ..dialogs.add_edit_owner_dialog import AddEditOwnerDialog
from ..dialogs.company_profile_dialog import CompanyProfileDialog
from ..dialogs.add_edit_veterinarian_dialog import AddEditVeterinarianDialog
from .application_paths_tab import ApplicationPathsTab
from .backup_restore_tab import BackupRestoreTab  # NEW: Import the new BackupRestoreTab


__all__ = [
    "AddEditUserDialog",
    "AddEditLocationDialog",
    "AddEditChargeCodeDialog",
    "AddEditChargeCodeCategoryDialog",
    "AddEditOwnerDialog",
    "CompanyProfileDialog",
    "AddEditVeterinarianDialog",
    "ApplicationPathsTab",
    "BackupRestoreTab",  # NEW: Add the new tab to __all__
]
