# views/horse/dialogs/record_payment_dialog.py
"""
EDSI Veterinary Management System - Record Payment Dialog
Version: 1.0.1
Purpose: Dialog for recording a payment against a specific invoice.
Last Updated: June 14, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-06-14):
    - Styled the 'Record Payment' and 'Cancel' buttons to conform to the
      application's style guide.
- v1.0.0 (2025-06-10):
    - Initial creation of the dialog.
"""
import logging
from decimal import Decimal
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
    QComboBox,
    QTextEdit,
    QLabel,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPalette, QColor, QFont

from models import Invoice
from controllers import FinancialController
from config.app_config import AppConfig


class RecordPaymentDialog(QDialog):
    """A dialog for recording a payment for an invoice."""

    PAYMENT_METHODS = ["Check", "Credit Card", "Cash", "Wire Transfer", "Other"]

    def __init__(
        self,
        invoice: Invoice,
        financial_controller: FinancialController,
        current_user_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.invoice = invoice
        self.financial_controller = financial_controller
        self.current_user_id = current_user_id

        self.setWindowTitle("Record Payment")
        self.setMinimumWidth(500)

        self._setup_ui()
        self._apply_styles()
        self._populate_form()

        self.button_box.accepted.connect(self.save_payment)
        self.button_box.rejected.connect(self.reject)

    def _get_input_field_style(self) -> str:
        return f"""
            QLineEdit, QDateEdit, QDoubleSpinBox, QTextEdit, QComboBox {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
            }}
        """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.owner_label = QLabel()
        self.invoice_label = QLabel()
        self.balance_due_label = QLabel()

        self.amount_input = QDoubleSpinBox()
        self.date_input = QDateEdit()
        self.method_combo = QComboBox()
        self.reference_input = QLineEdit()
        self.notes_edit = QTextEdit()

        self.form_layout.addRow("Owner:", self.owner_label)
        self.form_layout.addRow("Invoice #:", self.invoice_label)
        self.form_layout.addRow("Balance Due:", self.balance_due_label)
        self.form_layout.addRow("Payment Amount*:", self.amount_input)
        self.form_layout.addRow("Payment Date*:", self.date_input)
        self.form_layout.addRow("Payment Method*:", self.method_combo)
        self.form_layout.addRow("Reference #:", self.reference_input)
        self.form_layout.addRow("Notes:", self.notes_edit)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Record Payment"
        )

        layout.addLayout(self.form_layout)
        layout.addWidget(self.button_box)

    def _apply_styles(self):
        self.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY};"
        )
        input_style = self._get_input_field_style()

        for widget in [
            self.amount_input,
            self.date_input,
            self.method_combo,
            self.reference_input,
            self.notes_edit,
        ]:
            widget.setStyleSheet(input_style)

        for label in [self.owner_label, self.invoice_label, self.balance_due_label]:
            label.setStyleSheet("font-weight: bold;")

        self.amount_input.setRange(0.01, 999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$ ")

        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")

        self.method_combo.addItems(self.PAYMENT_METHODS)
        self.notes_edit.setFixedHeight(60)

        # MODIFIED: Add button styling
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        base_button_style = """
            QPushButton {
                border: 1px solid white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 120px;
                font-weight: bold;
            }
        """
        ok_button.setStyleSheet(
            base_button_style
            + f"""
            QPushButton {{ background-color: {AppConfig.DARK_SUCCESS_ACTION}; color: white; }}
            QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}
            """
        )
        cancel_button.setStyleSheet(
            base_button_style
            + f"""
            QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
            """
        )

    def _populate_form(self):
        owner_name = "N/A"
        if self.invoice.owner:
            owner_name = (
                self.invoice.owner.farm_name
                or f"{self.invoice.owner.first_name} {self.invoice.owner.last_name}"
            )

        self.owner_label.setText(owner_name)
        self.invoice_label.setText(f"INV-{self.invoice.invoice_id}")
        self.balance_due_label.setText(f"${self.invoice.balance_due:.2f}")
        self.amount_input.setValue(float(self.invoice.balance_due))
        self.date_input.setDate(QDate.currentDate())

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Collects data from the form fields."""
        amount = Decimal(self.amount_input.value())
        if amount <= 0:
            QMessageBox.warning(
                self, "Validation Error", "Payment amount must be greater than zero."
            )
            return None
        if amount > self.invoice.balance_due:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Payment amount cannot be greater than the balance due.",
            )
            return None

        return {
            "invoice_id": self.invoice.invoice_id,
            "owner_id": self.invoice.owner_id,
            "amount": amount,
            "payment_date": self.date_input.date().toPython(),
            "payment_method": self.method_combo.currentText(),
            "reference_number": self.reference_input.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "user_id": self.current_user_id,
        }

    def save_payment(self):
        payment_data = self.get_data()
        if not payment_data:
            return

        success, message = self.financial_controller.record_payment(payment_data)

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
