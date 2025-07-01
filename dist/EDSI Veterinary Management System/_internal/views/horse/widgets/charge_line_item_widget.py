# views/horse/widgets/charge_line_item_widget.py
"""
EDSI Veterinary Management System - Charge Line Item Widget
Version: 1.1.0
Purpose: A self-contained widget for a single charge line item, including notes.
         - Added styling for input fields.
Last Updated: June 6, 2025
Author: Gemini
"""
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QCheckBox,
    QTextEdit,
    QCompleter,
    QToolButton,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon

from models import ChargeCode
from config.app_config import AppConfig


class ChargeLineItemWidget(QWidget):
    """A widget representing a single, editable charge line."""

    remove_requested = Signal(QWidget)
    amount_changed = Signal()

    def __init__(self, charge_codes: List[ChargeCode], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._charge_codes = charge_codes if charge_codes else []
        self._charge_code_lookup = {cc.code: cc for cc in self._charge_codes}
        self._alt_code_lookup = {
            cc.alternate_code: cc for cc in self._charge_codes if cc.alternate_code
        }

        self.charge_data: Optional[ChargeCode] = None

        self._setup_ui()
        self._apply_styles()
        self._setup_connections()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(5)
        self.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border-radius: 5px; padding: 5px;"
        )

        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)

        self.charge_code_input = QLineEdit()
        self.alt_code_input = QLineEdit()
        self.description_label = QLineEdit()
        self.qty_spinbox = QDoubleSpinBox()
        self.price_spinbox = QDoubleSpinBox()
        self.taxable_checkbox = QCheckBox()
        self.total_label = QLabel("$0.00")
        self.remove_button = QToolButton()

        top_layout.addWidget(self.charge_code_input, 2)
        top_layout.addWidget(self.alt_code_input, 2)
        top_layout.addWidget(self.description_label, 6)
        top_layout.addWidget(self.qty_spinbox, 1)
        top_layout.addWidget(self.price_spinbox, 2)
        top_layout.addWidget(self.taxable_checkbox)
        top_layout.addWidget(self.total_label, 2)
        top_layout.addWidget(self.remove_button)

        self.notes_edit = QTextEdit()

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.notes_edit)

    def _apply_styles(self):
        # Apply the "boxed" style to all input fields
        input_style = f"""
            QLineEdit, QDoubleSpinBox, QTextEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
            }}
        """
        self.setStyleSheet(self.styleSheet() + input_style)

        self.charge_code_input.setPlaceholderText("Code")
        self.alt_code_input.setPlaceholderText("Alt Code")
        self.description_label.setPlaceholderText("Description")
        self.description_label.setReadOnly(True)

        self.qty_spinbox.setRange(0.001, 9999.0)
        self.qty_spinbox.setDecimals(3)
        self.qty_spinbox.setValue(1.0)

        self.price_spinbox.setRange(0.00, 99999.99)
        self.price_spinbox.setDecimals(2)
        self.price_spinbox.setPrefix("$ ")

        self.total_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.total_label.setMinimumWidth(80)

        self.notes_edit.setPlaceholderText("Enter notes for this line item...")
        self.notes_edit.setFixedHeight(40)

        self.remove_button.setIcon(QIcon(":/icons/delete"))  # Placeholder
        self.remove_button.setToolTip("Remove this charge")

    def _setup_connections(self):
        self.charge_code_input.editingFinished.connect(self._on_code_entered)
        self.alt_code_input.editingFinished.connect(self._on_alt_code_entered)
        self.qty_spinbox.valueChanged.connect(self._update_total)
        self.price_spinbox.valueChanged.connect(self._update_total)
        self.taxable_checkbox.stateChanged.connect(self.amount_changed.emit)
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))

    @Slot()
    def _on_code_entered(self):
        code_text = self.charge_code_input.text().upper()
        self.charge_data = self._charge_code_lookup.get(code_text)
        self._populate_from_charge_code()

    @Slot()
    def _on_alt_code_entered(self):
        alt_code_text = self.alt_code_input.text().upper()
        self.charge_data = self._alt_code_lookup.get(alt_code_text)
        self._populate_from_charge_code()

    def _populate_from_charge_code(self):
        if self.charge_data:
            self.charge_code_input.setText(self.charge_data.code)
            self.alt_code_input.setText(self.charge_data.alternate_code or "")
            self.description_label.setText(self.charge_data.description)
            self.price_spinbox.setValue(float(self.charge_data.standard_charge))
            self.taxable_checkbox.setChecked(self.charge_data.taxable)
        self._update_total()

    @Slot()
    def _update_total(self):
        try:
            qty = Decimal(self.qty_spinbox.value())
            price = Decimal(self.price_spinbox.value())
            total = qty * price
            self.total_label.setText(f"${total:.2f}")
        except (InvalidOperation, TypeError):
            self.total_label.setText("$0.00")
        self.amount_changed.emit()

    def get_data(self) -> Optional[Dict[str, Any]]:
        if not self.charge_data:
            return None

        return {
            "charge_code_id": self.charge_data.id,
            "description": self.description_label.text(),
            "quantity": Decimal(str(self.qty_spinbox.value())),
            "unit_price": Decimal(str(self.price_spinbox.value())),
            "total_price": (
                Decimal(str(self.qty_spinbox.value()))
                * Decimal(str(self.price_spinbox.value()))
            ),
            "taxable": self.taxable_checkbox.isChecked(),
            "item_notes": self.notes_edit.toPlainText().strip() or None,
        }
