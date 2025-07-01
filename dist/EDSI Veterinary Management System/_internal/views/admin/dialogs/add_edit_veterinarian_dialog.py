# views/admin/dialogs/add_edit_veterinarian_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Veterinarian Dialog
Version: 1.1.3
Purpose: UI dialog for creating and editing veterinarian records.
Last Updated: June 29, 2025
Author: Gemini

Changelog:
- v1.1.3 (2025-06-29):
    - **BUG FIX**: Applied correct styling to the "OK" (Save) and "Cancel" buttons
      in `_setup_ui` to match the EDMS Style Guide for size, colors, and borders,
      using `DARK_SUCCESS_ACTION` for OK and `DARK_BUTTON_BG` for Cancel.
- v1.1.2 (2025-06-28):
    - **BUG FIX**: Added missing `from PySide6.QtCore import Qt` import statement to resolve
      `NameError: name 'Qt' is not defined` when setting form layout alignment.
- v1.1.1 (2025-06-28):
    - **BUG FIX**: Modified `get_data` method to explicitly ensure the 'email' field
      is an empty string (or `None`) before returning, preventing `AttributeError: 'NoneType' object has no attribute 'strip'`
      in `VeterinarianController.validate_veterinarian_data` when the email field is empty.
- v1.1.0 (2025-06-09):
    - Replaced placeholder with a full UI implementation for data entry.
    - Added validation and interaction with VeterinarianController.
- v1.0.0 (2025-06-09):
    - Initial placeholder file created.
"""
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont

from controllers import VeterinarianController
from models import Veterinarian
from config.app_config import AppConfig


class AddEditVeterinarianDialog(QDialog):
    """A dialog for creating or editing veterinarian records."""

    def __init__(
        self,
        parent_view,
        controller: VeterinarianController,
        current_user_id: str,
        veterinarian: Optional[Veterinarian] = None,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.controller = controller
        self.current_user_id = current_user_id
        self.veterinarian = veterinarian
        self.is_edit_mode = veterinarian is not None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Veterinarian")
        self.setMinimumWidth(500)

        self._setup_palette()
        self._setup_ui()

        if self.is_edit_mode:
            self._populate_fields()

    def _setup_palette(self):
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _get_input_field_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
        """

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        input_style = self._get_input_field_style()

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.license_number_input = QLineEdit()
        self.specialty_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.is_active_checkbox = QCheckBox("Veterinarian is Active")
        self.is_active_checkbox.setChecked(True)

        for field in [
            self.first_name_input,
            self.last_name_input,
            self.license_number_input,
            self.specialty_input,
            self.phone_input,
            self.email_input,
        ]:
            field.setStyleSheet(input_style)

        form_layout.addRow("First Name*:", self.first_name_input)
        form_layout.addRow("Last Name*:", self.last_name_input)
        form_layout.addRow("License #*:", self.license_number_input)
        form_layout.addRow("Specialty:", self.specialty_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("", self.is_active_checkbox)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        # NEW: Apply button styling based on EDMS_STYLE_GUIDE
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        # Style for "OK" / "Save" buttons (Green background, white text, 1px solid white border)
        ok_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px; /* Adjust min-width to ensure consistent size */
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}
            QPushButton:disabled {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_TERTIARY};
                border: 1px solid {AppConfig.DARK_TEXT_TERTIARY};
            }}
        """
        ok_button.setStyleSheet(ok_button_style)

        # Style for "Cancel" / Neutral buttons (Neutral gray background, primary text, 1px solid white border)
        cancel_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px; /* Adjust min-width to ensure consistent size */
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
            QPushButton:disabled {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_TERTIARY};
                border: 1px solid {AppConfig.DARK_TEXT_TERTIARY};
            }}
        """
        cancel_button.setStyleSheet(cancel_button_style)

    def _populate_fields(self):
        if self.veterinarian:
            self.first_name_input.setText(self.veterinarian.first_name)
            self.last_name_input.setText(self.veterinarian.last_name)
            self.license_number_input.setText(self.veterinarian.license_number)
            self.specialty_input.setText(self.veterinarian.specialty or "")
            self.phone_input.setText(self.veterinarian.phone or "")
            self.email_input.setText(self.veterinarian.email or "")
            self.is_active_checkbox.setChecked(self.veterinarian.is_active)

    def get_data(self) -> Dict[str, Any]:
        """Collects data from the form fields."""
        # BUG FIX: Ensure email is a string, not None, to prevent .strip() error in controller.
        email_text = self.email_input.text().strip()
        email_value = email_text if email_text else None

        return {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "license_number": self.license_number_input.text().strip(),
            "specialty": self.specialty_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "email": email_value,
            "is_active": self.is_active_checkbox.isChecked(),
        }

    def validate_and_accept(self):
        vet_data = self.get_data()
        vet_id_to_ignore = self.veterinarian.vet_id if self.is_edit_mode else None

        is_valid, errors = self.controller.validate_veterinarian_data(
            vet_data, self.is_edit_mode, vet_id_to_ignore
        )

        if not is_valid:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the following errors:\n- " + "\n- ".join(errors),
            )
            return

        try:
            if self.is_edit_mode:
                success, message = self.controller.update_veterinarian(
                    self.veterinarian.vet_id, vet_data, self.current_user_id
                )
            else:
                success, message, _ = self.controller.create_veterinarian(
                    vet_data, self.current_user_id
                )

            if success:
                QMessageBox.information(self, "Success", message)
                self.accept()
            else:
                QMessageBox.critical(
                    self, "Error", message or "An unknown error occurred."
                )
        except Exception as e:
            self.logger.error(f"Error saving veterinarian: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Operation Failed", f"An unexpected error occurred: {e}"
            )
