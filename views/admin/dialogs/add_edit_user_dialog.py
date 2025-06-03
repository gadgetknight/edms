# views/admin/dialogs/add_edit_user_dialog.py
"""
EDSI Veterinary Management System - Add/Edit User Dialog
Version: 1.0.4
Purpose: Dialog for creating new users and editing existing user details.
         Corrects attribute access in _populate_fields for User model.
Last Updated: May 29, 2025
Author: Gemini (Modified by User's AI Assistant)

Changelog:
- v1.0.4 (2025-05-29):
    - Corrected attribute access in _populate_fields method:
        - Changed self.current_user_object.username to self.current_user_object.user_id.
        - Changed self.current_user_object.full_name to self.current_user_object.user_name.
- v1.0.3 (2025-05-29):
    - Modified USER_ROLES list to ["ADMIN", "VETERINARIAN"] as per user request
      to limit roles available in the dialog dropdown.
- v1.0.2 (2025-05-29):
    - Refactored _get_dialog_button_style() to use a triple-quoted f-string
      to prevent potential syntax errors with string concatenation.
- v1.0.1 (2025-05-27):
    - Modified get_user_data() to return 'user_id' instead of 'username'
      and 'user_name' instead of 'full_name' to align with UserController.
    - Changed 'vet' to 'VETERINARIAN' in USER_ROLES list.
- v1.0.0 (2025-05-20):
    - Initial implementation.
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
from models.user_models import User  # User model needed for type hinting
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

    USER_ROLES = ["ADMIN", "VETERINARIAN"]

    def __init__(
        self,
        parent_view,  # Should be the UserManagementScreen instance
        user_controller: UserController,
        current_user_object: Optional[
            User
        ] = None,  # User object from models.user_models
    ):
        super().__init__(parent_view)  # parent_view is the QWidget parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = (
            parent_view  # Storing reference if needed for other interactions
        )
        self.user_controller = user_controller
        self.current_user_object = current_user_object

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
        )
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(Qt.GlobalColor.red))
        palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_PRIMARY_ACTION))
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
                min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_PRIMARY_ACTION}70;
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
        return f"""
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px;
                font-size: 12px; font-weight: 500; min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {DARK_BUTTON_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY};
            }}
        """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "Enter unique username (Login ID)"
        )  # Clarified placeholder
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText(
            "Enter user's full name (Display Name)"
        )  # Clarified placeholder
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
        self.is_active_checkbox.setChecked(True)

        input_style = self._get_input_field_style()
        self.username_input.setStyleSheet(input_style)
        self.full_name_input.setStyleSheet(input_style)
        self.email_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)
        self.confirm_password_input.setStyleSheet(input_style)
        self.role_combo.setStyleSheet(input_style)
        self.is_active_checkbox.setStyleSheet(input_style)

        form_layout.addRow(
            QLabel("Login ID*:"), self.username_input
        )  # Changed label for clarity
        form_layout.addRow(QLabel("Full Name*:"), self.full_name_input)
        form_layout.addRow(QLabel("Email:"), self.email_input)
        form_layout.addRow(
            QLabel("Password:" if self.is_edit_mode else "Password*:"),
            self.password_input,
        )
        form_layout.addRow(QLabel("Confirm Password:"), self.confirm_password_input)
        form_layout.addRow(QLabel("Role*:"), self.role_combo)
        form_layout.addRow(QLabel("Status:"), self.is_active_checkbox)

        for i in range(form_layout.rowCount()):
            label_widget = form_layout.labelForField(
                form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            )
            if label_widget:
                label_widget.setStyleSheet(
                    f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-top: 3px;"
                )

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Save User" if self.is_edit_mode else "Add User")

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
            # MODIFIED: Use user_id for username_input
            self.username_input.setText(self.current_user_object.user_id)
            self.username_input.setReadOnly(True)
            self.username_input.setStyleSheet(
                self._get_input_field_style()
                + f"QLineEdit {{ background-color: {DARK_HEADER_FOOTER}; }}"
            )
            # MODIFIED: Use user_name for full_name_input
            self.full_name_input.setText(self.current_user_object.user_name or "")
            self.email_input.setText(self.current_user_object.email or "")

            user_role_name_to_select = ""
            if self.current_user_object.roles:
                for role_obj in self.current_user_object.roles:
                    if role_obj.name in self.USER_ROLES:
                        user_role_name_to_select = role_obj.name
                        break
                if not user_role_name_to_select:
                    self.logger.warning(
                        f"User {self.current_user_object.user_id} has roles, but none match current dialog options: {[r.name for r in self.current_user_object.roles]}. Defaulting selection."
                    )

            role_index = -1
            if user_role_name_to_select:
                role_index = self.role_combo.findText(
                    user_role_name_to_select, Qt.MatchFlag.MatchExactly
                )

            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)
            else:
                self.logger.warning(
                    f"Role '{user_role_name_to_select}' for user '{self.current_user_object.user_id}' not found in USER_ROLES dropdown. Defaulting."
                )
                if self.role_combo.count() > 0:
                    self.role_combo.setCurrentIndex(0)
                else:
                    self.logger.error(
                        "USER_ROLES is empty, cannot set default role index."
                    )

            self.is_active_checkbox.setChecked(self.current_user_object.is_active)

    def _validate_input(self) -> bool:
        # username_input now corresponds to user_id
        login_id = self.username_input.text().strip()
        # full_name_input now corresponds to user_name
        user_name_val = self.full_name_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not login_id:
            QMessageBox.warning(self, "Validation Error", "Login ID cannot be empty.")
            self.username_input.setFocus()
            return False
        if not user_name_val:  # Changed from full_name to user_name_val
            QMessageBox.warning(self, "Validation Error", "Full Name cannot be empty.")
            self.full_name_input.setFocus()
            return False

        if not self.is_edit_mode and not password:
            QMessageBox.warning(
                self, "Validation Error", "Password cannot be empty for new users."
            )
            self.password_input.setFocus()
            return False

        if password and password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            self.confirm_password_input.setFocus()
            return False

        email = self.email_input.text().strip()
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            QMessageBox.warning(
                self, "Validation Error", "Please enter a valid email address."
            )
            self.email_input.setFocus()
            return False

        if self.role_combo.currentIndex() == -1 and self.USER_ROLES:
            QMessageBox.warning(self, "Validation Error", "A role must be selected.")
            self.role_combo.setFocus()
            return False

        return True

    def get_user_data(self) -> Optional[Dict]:
        if not self._validate_input():
            return None

        data = {
            "user_id": self.username_input.text().strip(),
            "user_name": self.full_name_input.text().strip(),
            "email": self.email_input.text().strip() or None,
            "role": self.role_combo.currentText(),
            "is_active": self.is_active_checkbox.isChecked(),
        }
        password = self.password_input.text()
        if password:
            data["password"] = password

        return data

    def _on_accept(self):
        user_data = self.get_user_data()
        if user_data is None:
            return

        try:
            current_admin_id = None
            if hasattr(self.parent_view, "current_user_id"):
                current_admin_id = self.parent_view.current_user_id

            if self.is_edit_mode and self.current_user_object:
                self.logger.info(
                    f"Attempting to update user ID: {self.current_user_object.user_id}"
                )
                success, message = self.user_controller.update_user(
                    self.current_user_object.user_id, user_data, current_admin_id
                )
            else:
                self.logger.info(
                    f"Attempting to create new user: {user_data['user_id']}"
                )
                success, message, _ = self.user_controller.create_user(
                    user_data, current_admin_id
                )

            if success:
                self.logger.info(f"User operation successful: {message}")
                self.accept()
            else:
                self.logger.warning(f"User operation failed: {message}")
                QMessageBox.critical(self, "Operation Failed", message)
        except Exception as e:
            self.logger.error(f"Error during user save/update: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
