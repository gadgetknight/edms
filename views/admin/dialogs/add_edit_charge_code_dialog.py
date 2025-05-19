# views/admin/dialogs/add_edit_charge_code_dialog.py

"""
EDSI Veterinary Management System - Add/Edit Charge Code Dialog
Version: 1.0.0
Purpose: Dialog for creating and editing charge codes.
Last Updated: May 18, 2025
Author: Claude Assistant
"""

import logging
from typing import Optional, Dict
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from config.app_config import AppConfig
from controllers.charge_code_controller import (
    ChargeCodeController,
)  # Assuming this exists
from models import ChargeCode  # For type hinting


class AddEditChargeCodeDialog(QDialog):
    """
    A dialog for adding a new charge code or editing an existing one.
    """

    def __init__(
        self,
        parent,
        charge_code_controller: ChargeCodeController,
        charge_code: Optional[ChargeCode] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.controller = charge_code_controller
        self.charge_code_to_edit = charge_code  # None if adding new

        if self.charge_code_to_edit:
            self.setWindowTitle("Edit Charge Code")
        else:
            self.setWindowTitle("Add New Charge Code")

        self.setMinimumWidth(500)
        self._setup_palette()
        self._setup_ui()

        if self.charge_code_to_edit:
            self._load_data()

    def _setup_palette(self):
        """Sets the dark theme palette for the dialog."""
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
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)

    def _get_input_style(self):
        """Gets the input style from the parent view or a default."""
        if hasattr(self.parent(), "get_form_input_style"):
            return self.parent().get_form_input_style()
        # Fallback basic style
        return f"""
            QLineEdit, QTextEdit, QDoubleSpinBox {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QTextEdit {{ min-height: 60px; }}
        """

    def _setup_ui(self):
        """Creates and lays out the UI elements."""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setSpacing(10)

        input_style = self._get_input_style()
        label_style = f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color:transparent; padding-top:3px;}}"
        self.setStyleSheet(label_style)

        self.code_input = QLineEdit()
        self.code_input.setStyleSheet(input_style)
        self.code_input.setPlaceholderText("e.g., 9991, FC")
        form_layout.addRow(QLabel("Charge Code*:"), self.code_input)

        self.alt_code_input = QLineEdit()
        self.alt_code_input.setStyleSheet(input_style)
        self.alt_code_input.setPlaceholderText("e.g., IVO (Optional)")
        form_layout.addRow(QLabel("Alternate Code:"), self.alt_code_input)

        self.description_input = (
            QTextEdit()
        )  # Using QTextEdit for potentially longer descriptions
        self.description_input.setStyleSheet(input_style)
        self.description_input.setPlaceholderText("Full description of the charge code")
        form_layout.addRow(QLabel("Description*:"), self.description_input)

        self.category_input = QLineEdit()
        self.category_input.setStyleSheet(input_style)
        self.category_input.setPlaceholderText(
            "e.g., VETERINARY - CALL FEES (Optional)"
        )
        form_layout.addRow(QLabel("Category:"), self.category_input)

        self.standard_charge_spinbox = QDoubleSpinBox()
        self.standard_charge_spinbox.setStyleSheet(input_style)
        self.standard_charge_spinbox.setDecimals(2)
        self.standard_charge_spinbox.setMinimum(0.00)
        self.standard_charge_spinbox.setMaximum(999999.99)  # Adjust as needed
        self.standard_charge_spinbox.setPrefix("$ ")
        form_layout.addRow(QLabel("Standard Charge*:"), self.standard_charge_spinbox)

        self.is_active_checkbox = QCheckBox("Is Active")
        self.is_active_checkbox.setChecked(True)  # Default to active
        self.is_active_checkbox.setStyleSheet(
            f"QCheckBox {{ color: {AppConfig.DARK_TEXT_SECONDARY}; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        form_layout.addRow("", self.is_active_checkbox)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        generic_button_style = (
            self.parent().get_generic_button_style()
            if hasattr(self.parent(), "get_generic_button_style")
            else ""
        )
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            if generic_button_style:
                button.setStyleSheet(generic_button_style)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = AppConfig.DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    .replace(AppConfig.DARK_BUTTON_BG, ok_bg_color)
                    .replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white;")
                )
        layout.addWidget(self.button_box)

    def _load_data(self):
        """Populates dialog fields if editing an existing charge code."""
        if self.charge_code_to_edit:
            self.code_input.setText(self.charge_code_to_edit.code)
            self.alt_code_input.setText(self.charge_code_to_edit.alternate_code or "")
            self.description_input.setPlainText(self.charge_code_to_edit.description)
            self.category_input.setText(self.charge_code_to_edit.category or "")
            self.standard_charge_spinbox.setValue(
                float(self.charge_code_to_edit.standard_charge)
            )
            self.is_active_checkbox.setChecked(self.charge_code_to_edit.is_active)
            # Disable code input if editing, as it's usually a primary identifier
            # self.code_input.setEnabled(False) # Or make it read-only

    def get_data(self) -> Optional[Dict[str, any]]:
        """Collects data from the form fields."""
        data = {
            "code": self.code_input.text().strip(),
            "alternate_code": self.alt_code_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "category": self.category_input.text().strip(),
            "standard_charge": Decimal(self.standard_charge_spinbox.value()),
            "is_active": self.is_active_checkbox.isChecked(),
        }
        return data

    def _on_accept(self):
        """Handles the OK button click, validates and processes data."""
        charge_data = self.get_data()
        if not charge_data:  # Should not happen if get_data is robust
            QMessageBox.critical(self, "Error", "Could not retrieve data from form.")
            return

        is_new = self.charge_code_to_edit is None

        # Perform validation using the controller
        is_valid, errors = self.controller.validate_charge_code_data(
            charge_data, is_new=is_new
        )

        # Specific check for code uniqueness if editing and code has changed
        if not is_new and charge_data["code"] != self.charge_code_to_edit.code:
            existing = self.controller.get_charge_code_by_code(charge_data["code"])
            if (
                existing
                and existing.charge_code_id != self.charge_code_to_edit.charge_code_id
            ):
                is_valid = False
                errors.append(
                    f"Charge Code '{charge_data['code']}' already exists for another record."
                )

        if not is_valid:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the following errors:\n\n- " + "\n- ".join(errors),
            )
            return

        if is_new:
            success, message, _ = self.controller.create_charge_code(charge_data)
        else:
            success, message = self.controller.update_charge_code(
                self.charge_code_to_edit.charge_code_id, charge_data
            )

        if success:
            QMessageBox.information(self, "Success", message)
            super().accept()  # Close the dialog
        else:
            QMessageBox.critical(self, "Error", message)
            # Dialog remains open for correction
