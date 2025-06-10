# views/horse/dialogs/edit_charge_dialog.py
"""
EDSI Veterinary Management System - Edit Charge Dialog
Version: 1.3.1
Purpose: Dialog for editing the details of a single charge transaction.
         - Corrected styling for read-only fields.
Last Updated: June 8, 2025
Author: Gemini

Changelog:
- v1.3.1 (2025-06-08):
    - Removed a specific style rule for read-only QLineEdits to ensure they
      have the same background color as other input fields for a consistent look.
- v1.3.0 (2025-06-08):
    - Added read-only display fields for "Code" and "Alt. Code" to the top of
      the dialog for better user context.
- v1.2.0 (2025-06-07):
    - Styled the Save (green) and Cancel (gray) buttons with a visible
      border and appropriate colors for better UI consistency and clarity.
- v1.1.0 (2025-06-07):
    - Applied a new, standardized style to all input widgets.
- v1.0.3 (2025-06-07):
    - Bug Fix: Corrected all references to use `item_notes` instead of `notes`.
"""

import logging
from decimal import Decimal, InvalidOperation
from datetime import date
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QLineEdit,
    QDateEdit,
    QDoubleSpinBox,
    QCheckBox,
    QTextEdit,
    QLabel,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPalette, QColor

from models import Transaction
from controllers import FinancialController
from config.app_config import AppConfig


class EditChargeDialog(QDialog):
    """A dialog for editing a single charge item."""

    def __init__(
        self,
        transaction: Transaction,
        financial_controller: FinancialController,
        current_user_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.transaction = transaction
        self.financial_controller = financial_controller
        self.current_user_id = current_user_id

        self.setWindowTitle(f"Edit Charge: {self.transaction.description[:30]}...")
        self.setMinimumWidth(500)

        self._setup_palette()
        self._setup_ui()
        self._apply_styles()
        self._populate_form()

        self.button_box.accepted.connect(self.save_changes)
        self.button_box.rejected.connect(self.reject)

    def _get_input_field_style(self) -> str:
        """Generates the standard style for all input fields in the dialog."""
        return f"""
            QLineEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{
                background-color: #3E3E3E;
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid white;
                border-radius: 3px;
                background-color: #3E3E3E;
            }}
            QCheckBox::indicator:checked {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                border-color: {AppConfig.DARK_SUCCESS_ACTION};
            }}
        """

    def _setup_palette(self):
        """Sets up the dark theme palette for the dialog."""
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        self.setPalette(palette)

    def _setup_ui(self):
        """Initializes and lays out the UI widgets."""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.code_display = QLineEdit()
        self.alt_code_display = QLineEdit()
        self.service_date_edit = QDateEdit()
        self.service_date_edit.setCalendarPopup(True)
        self.service_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.description_edit = QLineEdit()
        self.qty_spinbox = QDoubleSpinBox()
        self.price_spinbox = QDoubleSpinBox()
        self.taxable_checkbox = QCheckBox("This item is taxable")
        self.notes_edit = QTextEdit()

        code_layout = QHBoxLayout()
        code_layout.addWidget(self.code_display)
        code_layout.addWidget(QLabel("Alt. Code:"))
        code_layout.addWidget(self.alt_code_display)

        form_layout.addRow("Charge Code:", code_layout)
        form_layout.addRow("Service Date:", self.service_date_edit)
        form_layout.addRow("Description:", self.description_edit)
        form_layout.addRow("Quantity:", self.qty_spinbox)
        form_layout.addRow("Unit Price:", self.price_spinbox)
        form_layout.addRow("", self.taxable_checkbox)
        form_layout.addRow("Item Notes:", self.notes_edit)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

    def _apply_styles(self):
        """Applies consistent styling to the dialog's widgets."""
        field_style = self._get_input_field_style()

        self.code_display.setReadOnly(True)
        self.alt_code_display.setReadOnly(True)

        # Apply the same style to all fields
        for widget in [
            self.code_display,
            self.alt_code_display,
            self.service_date_edit,
            self.description_edit,
            self.qty_spinbox,
            self.price_spinbox,
            self.taxable_checkbox,
            self.notes_edit,
        ]:
            widget.setStyleSheet(field_style)

        self.qty_spinbox.setDecimals(3)
        self.qty_spinbox.setRange(0.001, 9999.999)
        self.price_spinbox.setDecimals(2)
        self.price_spinbox.setRange(0.00, 99999.99)
        self.price_spinbox.setPrefix("$ ")
        self.notes_edit.setMinimumHeight(80)

        # Style Save and Cancel buttons
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        save_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                color: white;
                border: 1px solid {QColor(AppConfig.DARK_SUCCESS_ACTION).darker(120).name()};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        cancel_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
        """
        save_button.setStyleSheet(save_button_style)
        cancel_button.setStyleSheet(cancel_button_style)

    def _populate_form(self):
        """Fills the form widgets with data from the transaction object."""
        if self.transaction.charge_code:
            self.code_display.setText(self.transaction.charge_code.code)
            self.alt_code_display.setText(
                self.transaction.charge_code.alternate_code or ""
            )
        else:
            self.code_display.setText("N/A")
            self.alt_code_display.setText("N/A")

        self.service_date_edit.setDate(QDate(self.transaction.transaction_date))
        self.description_edit.setText(self.transaction.description)
        self.qty_spinbox.setValue(float(self.transaction.quantity))
        self.price_spinbox.setValue(float(self.transaction.unit_price))
        self.taxable_checkbox.setChecked(self.transaction.taxable)
        self.notes_edit.setPlainText(self.transaction.item_notes or "")

    def get_data_from_form(self) -> Dict[str, Any]:
        """Collects and returns the current data from the form widgets."""
        return {
            "transaction_date": self.service_date_edit.date().toPython(),
            "description": self.description_edit.text().strip(),
            "quantity": Decimal(str(self.qty_spinbox.value())),
            "unit_price": Decimal(str(self.price_spinbox.value())),
            "taxable": self.taxable_checkbox.isChecked(),
            "item_notes": self.notes_edit.toPlainText().strip() or None,
        }

    def save_changes(self):
        """Validates and saves the changes via the financial controller."""
        updated_data = self.get_data_from_form()

        if not updated_data["description"]:
            QMessageBox.warning(
                self, "Validation Error", "Description cannot be empty."
            )
            return

        success, message = self.financial_controller.update_charge_transaction(
            transaction_id=self.transaction.transaction_id,
            data=updated_data,
            current_user_id=self.current_user_id,
        )

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
