# views/admin/dialogs/__init__.py
"""
Initialization file for the dialogs sub-package within the admin view.
This file makes dialog classes available for easier import by other modules,
notably the UserManagementScreen.
"""
# Ensure NO leading spaces/tabs on the following import lines

# Corrected to import from 'add_edit_change_code_dialog.py' as per user preference
from .add_edit_change_code_dialog import AddEditChargeCodeDialog
from .add_edit_location_dialog import AddEditLocationDialog

# Add other dialogs from this directory if they exist and need to be imported
# e.g.:
# from .another_dialog import AnotherDialog

__all__ = [
    "AddEditChargeCodeDialog",  # The class name itself remains the same
    "AddEditLocationDialog",
    # "AnotherDialog", # if you add more
]
# Ensure NO leading spaces/tabs on the __all__ list assignment
