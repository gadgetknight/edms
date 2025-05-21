# views/admin/dialogs/add_edit_user_dialog.py
"""
EDSI Veterinary Management System - Add/Edit User Dialog
Version: 1.0.0
Purpose: Dialog for creating new users and editing existing user details.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-05-20):
    - Initial implementation.
    - Provides form fields for username, full_name, email, password, role, and is_active.
    - Handles both "add" and "edit" modes.
    - Includes basic validation (required fields, password match).
    - Interacts with UserController to save user data.
    - Styled for dark theme.
"""

import logging
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.user_controller import UserController
from models.user_models import User  # Assuming User model is in user_models.py
from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_BORDER,
    DARK_PRIMARY_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_SUCCESS_ACTION,
    DARK_HEADER_FOOTER,
    DEFAULT_FONT_FAMILY,
)


class AddEditUserDialog(QDialog):
    """Dialog for adding or editing user information."""

    USER_ROLES = ["admin", "vet", "staff", "owner"]  # Define available roles

    def __init__(
        self,
        parent_view,
        user_controller: UserController,
        current_user_object: Optional[User] = None,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.user_controller = user_controller
        self.current_user_object = (
            current_user_object  # User object if editing, None if adding
        )

        self.is_edit_mode = self.current_user_object is not None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} User")
        self.setMinimumWidth(450)

        self._setup_palette()
        self._setup_ui()

        if self.is_edit_mode and self.current_user_object:
            self._populate_fields()

        self.logger.info(
            f"AddEditUserDialog initialized. Edit mode: {self.is_edit_mode}"
        )

    def _setup_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_INPUT_FIELD_BACKGROUND))
        palette.setColor(
            QPalette.ColorRole.AlternateBase, QColor(DARK_WIDGET_BACKGROUND)
        )  # for combobox dropdown
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(
            QPalette.ColorRole.BrightText, QColor(Qt.GlobalColor.red)
        )  # For validation errors if needed
        palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        palette.setColor(
            QPalette.ColorRole.Highlight, QColor(DARK_PRIMARY_ACTION)
        )  # Selection in combobox
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _get_input_field_style(self) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px; /* Ensure fields are not too small */
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QComboBox QAbstractItemView {{ /* Style for the dropdown list */
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_PRIMARY_ACTION}70; /* Alpha for selection */
            }}
            QCheckBox {{
                color: {DARK_TEXT_PRIMARY};
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
        """

    def _get_dialog_button_style(self) -> str:
        return (
            f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight
        )  # Align labels to the right
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter unique username")
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Enter user's full name")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter user's email address")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(
            "Enter password (leave blank to keep current)"
        )
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")

        self.role_combo = QComboBox()
        self.role_combo.addItems(self.USER_ROLES)

        self.is_active_checkbox = QCheckBox("User is Active")
        self.is_active_checkbox.setChecked(True)  # Default for new users

        # Apply styles
        input_style = self._get_input_field_style()
        self.username_input.setStyleSheet(input_style)
        self.full_name_input.setStyleSheet(input_style)
        self.email_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)
        self.confirm_password_input.setStyleSheet(input_style)
        self.role_combo.setStyleSheet(input_style)
        self.is_active_checkbox.setStyleSheet(
            input_style
        )  # Checkbox style defined in input_style

        # Add rows to form layout
        form_layout.addRow(QLabel("Username*:"), self.username_input)
        form_layout.addRow(QLabel("Full Name*:"), self.full_name_input)
        form_layout.addRow(QLabel("Email:"), self.email_input)
        form_layout.addRow(
            QLabel("Password:" if self.is_edit_mode else "Password*:"),
            self.password_input,
        )
        form_layout.addRow(QLabel("Confirm Password:"), self.confirm_password_input)
        form_layout.addRow(QLabel("Role*:"), self.role_combo)
        form_layout.addRow(QLabel("Status:"), self.is_active_checkbox)

        # Styling for QLabel in QFormLayout (optional, could be global)
        for i in range(form_layout.rowCount()):
            label_widget = form_layout.labelForField(
                form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            )
            if label_widget:
                label_widget.setStyleSheet(
                    f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-top: 3px;"
                )

        layout.addLayout(form_layout)

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Save User" if self.is_edit_mode else "Add User")

        # Apply generic style and then override for OK button
        dialog_button_style = self._get_dialog_button_style()
        for button in self.button_box.buttons():
            button.setStyleSheet(dialog_button_style)
        ok_button.setStyleSheet(
            dialog_button_style
            + f"QPushButton {{ background-color: {DARK_SUCCESS_ACTION}; color: white; }}"
        )

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _populate_fields(self):
        """Populate fields if in edit mode."""
        if self.current_user_object:
            self.username_input.setText(self.current_user_object.username)
            self.username_input.setReadOnly(True)  # Username typically not editable
            self.username_input.setStyleSheet(
                self._get_input_field_style()
                + f"QLineEdit {{ background-color: {DARK_HEADER_FOOTER}; }}"
            )  # Visually indicate read-only
            self.full_name_input.setText(self.current_user_object.full_name or "")
            self.email_input.setText(self.current_user_object.email or "")
            # Password fields remain blank; only for setting new password
            role_index = self.role_combo.findText(
                self.current_user_object.role, Qt.MatchFlag.MatchExactly
            )
            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)
            else:
                self.logger.warning(
                    f"Role '{self.current_user_object.role}' not found in USER_ROLES. Defaulting."
                )
                self.role_combo.setCurrentIndex(0)  # Default to first role if not found
            self.is_active_checkbox.setChecked(self.current_user_object.is_active)

    def _validate_input(self) -> bool:
        """Performs basic validation on input fields."""
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        password = self.password_input.text()  # No strip, spaces might be intentional
        confirm_password = self.confirm_password_input.text()
        # email = self.email_input.text().strip() # Email validation can be complex

        if not username:
            QMessageBox.warning(self, "Validation Error", "Username cannot be empty.")
            self.username_input.setFocus()
            return False
        if not full_name:
            QMessageBox.warning(self, "Validation Error", "Full Name cannot be empty.")
            self.full_name_input.setFocus()
            return False

        if not self.is_edit_mode and not password:  # Password required for new user
            QMessageBox.warning(
                self, "Validation Error", "Password cannot be empty for new users."
            )
            self.password_input.setFocus()
            return False

        if password and password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            self.confirm_password_input.setFocus()
            return False

        # Basic email format check (very lenient)
        email = self.email_input.text().strip()
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            QMessageBox.warning(
                self, "Validation Error", "Please enter a valid email address."
            )
            self.email_input.setFocus()
            return False

        return True

    def get_user_data(self) -> Optional[Dict]:
        """Collects and returns user data from the form fields."""
        if not self._validate_input():
            return None

        data = {
            "username": self.username_input.text().strip(),
            "full_name": self.full_name_input.text().strip(),
            "email": self.email_input.text().strip()
            or None,  # Allow empty email if not required
            "role": self.role_combo.currentText(),
            "is_active": self.is_active_checkbox.isChecked(),
        }
        # Only include password if it's being set/changed
        password = self.password_input.text()
        if password:
            data["password"] = password  # Controller will hash it

        return data

    def _on_accept(self):
        """Handles the OK/Save button click."""
        user_data = self.get_user_data()
        if user_data is None:
            return  # Validation failed or data issue

        try:
            if self.is_edit_mode and self.current_user_object:
                self.logger.info(
                    f"Attempting to update user ID: {self.current_user_object.user_id}"
                )
                # Username is not in user_data if it's read-only, controller needs user_id
                success, message = self.user_controller.update_user(
                    self.current_user_object.user_id, user_data
                )
            else:
                self.logger.info(
                    f"Attempting to create new user: {user_data['username']}"
                )
                success, message, _ = self.user_controller.create_user(
                    user_data
                )  # create_user returns (success, msg, user_obj)

            if success:
                self.logger.info(f"User operation successful: {message}")
                self.accept()  # Closes the dialog with Accepted status
            else:
                self.logger.warning(f"User operation failed: {message}")
                QMessageBox.critical(self, "Operation Failed", message)
        except Exception as e:
            self.logger.error(f"Error during user save/update: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
