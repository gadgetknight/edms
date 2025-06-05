# views/admin/dialogs/__init__.py
"""
EDSI Veterinary Management System - Admin Dialogs Package
Version: 1.0.1 (Example Version)
Purpose: Makes admin dialog classes easily importable.
Last Updated: June 4, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-06-04):
    - Added AddEditOwnerDialog to exports.
    - Ensured other existing dialogs are exported.
"""

from .add_edit_user_dialog import AddEditUserDialog
from .add_edit_location_dialog import AddEditLocationDialog
from .add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .add_edit_charge_code_category_dialog import AddEditChargeCodeCategoryDialog

# MODIFIED: Changed from AddEditMasterOwnerDialog to AddEditOwnerDialog
from .add_edit_owner_dialog import AddEditOwnerDialog


__all__ = [
    "AddEditUserDialog",
    "AddEditLocationDialog",
    "AddEditChargeCodeDialog",
    "AddEditChargeCodeCategoryDialog",
    "AddEditOwnerDialog",  # Ensure this matches the class name in the file
]
