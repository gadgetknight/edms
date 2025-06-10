# views/horse/dialogs/edit_all_charges_dialog.py
"""
EDSI Veterinary Management System - Edit All Charges Dialog
Version: 1.1.1
Purpose: A dialog for bulk-editing all un-invoiced charges for a horse.
Last Updated: June 8, 2025
Author: Gemini

Changelog:
- v1.1.1 (2025-06-08):
    - Bug Fix: Added defensive checks to the `_update_totals` method to prevent
      warnings caused by a race condition during dialog initialization.
- v1.1.0 (2025-06-08):
    - Updated the header to display the full, detailed information line for the
      horse, matching the main application screens for consistency.
- v1.0.0 (2025-06-08):
    - Initial creation of the dialog.
"""

import logging
from decimal import Decimal, InvalidOperation
from datetime import date
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QLineEdit,
    QCompleter,
    QDoubleSpinBox,
    QCheckBox,
    QAbstractItemView,
    QFormLayout,
    QTextEdit,
    QApplication,
    QAbstractSpinBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot
from PySide6.QtGui import QFont, QColor, QPainter, QPen

from models import Horse, Transaction, ChargeCode
from controllers import FinancialController
from config.app_config import AppConfig


class BoxedCellDelegate(QStyledItemDelegate):
    """A delegate to draw borders around cells to give them a 'boxed' look."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        super().paint(painter, option, index)
        painter.save()
        pen = QPen(QColor(AppConfig.DARK_BORDER))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(option.rect)
        painter.restore()


class EditAllChargesDialog(QDialog):
    """A dialog for editing a batch of existing charge items for a horse."""

    charges_updated = Signal()

    def __init__(
        self,
        horse: Horse,
        transactions: List[Transaction],
        financial_controller: FinancialController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse = horse
        self.transactions = transactions
        self.financial_controller = financial_controller
        self.current_user_id = QApplication.instance().current_user_id

        self.setWindowTitle(
            f"Edit All Un-invoiced Charges for: {self.horse.horse_name}"
        )
        self.setMinimumSize(1200, 700)

        self._charge_codes_list: List[ChargeCode] = []
        self._charge_code_lookup: Dict[str, ChargeCode] = {}
        self._alt_code_lookup: Dict[str, ChargeCode] = {}
        self._row_notes: Dict[int, str] = {}
        self._current_notes_row: Optional[int] = None
        self._taxable_subtotal = Decimal(0)

        self._setup_ui()
        self._apply_styles()
        self._setup_connections()

        self._populate_header()
        QTimer.singleShot(0, self._load_initial_data)

    def _get_input_field_style(self) -> str:
        """Generates the requested style for all input fields."""
        return f"""
            QLineEdit, QDoubleSpinBox, QTextEdit {{
                background-color: #3E3E3E;
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_TERTIARY};
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

    def _setup_ui(self):
        """Initializes and lays out the UI widgets based on the new design."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.horse_title_label = QLabel()
        self.horse_info_line_label = QLabel()
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.horse_title_label)
        header_layout.addWidget(self.horse_info_line_label)
        main_layout.addWidget(header_widget)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.charges_table = QTableWidget()
        table_layout.addWidget(self.charges_table)
        self.notes_edit = QTextEdit()
        table_layout.addWidget(self.notes_edit)
        table_layout.setStretchFactor(self.charges_table, 3)
        table_layout.setStretchFactor(self.notes_edit, 1)
        main_layout.addWidget(table_container, 1)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton(
            "Save Changes", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.cancel_button = self.button_box.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        footer_layout.addWidget(self.button_box)
        footer_layout.addStretch()

        totals_container = QWidget()
        totals_form_layout = QFormLayout(totals_container)
        totals_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.subtotal_label = QLabel("$0.00")
        self.taxable_subtotal_label = QLabel("$0.00")
        self.tax_amount_input = QDoubleSpinBox()
        self.tax_rate_input = QDoubleSpinBox()
        self.grand_total_label = QLabel("$0.00")
        tax_layout = QHBoxLayout()
        tax_layout.addWidget(self.tax_rate_input)
        tax_layout.addWidget(self.tax_amount_input)
        totals_form_layout.addRow("Subtotal:", self.subtotal_label)
        totals_form_layout.addRow("Taxable Subtotal:", self.taxable_subtotal_label)
        totals_form_layout.addRow("Tax (% / Amt):", tax_layout)
        totals_form_layout.addRow("<b>Grand Total:</b>", self.grand_total_label)
        footer_layout.addWidget(totals_container)
        main_layout.addLayout(footer_layout)

    def _populate_header(self):
        self.horse_title_label.setText(self.horse.horse_name)
        age_str = self._calculate_age(self.horse.date_of_birth)
        owner_name = self._get_display_owner_name(self.horse)
        location_name = self._get_display_location_name(self.horse)
        info_parts = [
            f"Acct: {self.horse.account_number or 'N/A'}",
            f"👥 {owner_name}",
            f"Breed: {self.horse.breed or 'N/A'}",
            f"Color: {self.horse.color or 'N/A'}",
            f"Sex: {self.horse.sex or 'N/A'}",
            f"Age: {age_str}",
            f"📍 {location_name}",
        ]
        self.horse_info_line_label.setText(" | ".join(info_parts))

    def _apply_styles(self):
        """Applies consistent styling to the dialog's widgets."""
        self.horse_title_label.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 16, QFont.Weight.Bold)
        )
        self.horse_title_label.setStyleSheet(f"color:{AppConfig.DARK_TEXT_PRIMARY};")
        self.horse_info_line_label.setStyleSheet(
            f"color:{AppConfig.DARK_TEXT_SECONDARY}; font-size: 11px;"
        )

        self.charges_table.setColumnCount(7)
        self.charges_table.setHorizontalHeaderLabels(
            ["Code", "Alt. Code", "Description", "Qty", "Unit Price", "Tax", "Total"]
        )
        self.charges_table.verticalHeader().setVisible(False)
        self.charges_table.setItemDelegate(BoxedCellDelegate(self))
        header = self.charges_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.charges_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.notes_edit.setPlaceholderText(
            "Notes for the selected line item will appear here..."
        )

        self.tax_rate_input.setDecimals(4)
        self.tax_rate_input.setRange(0.00, 100.00)
        self.tax_rate_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tax_rate_input.setSuffix(" %")

        self.tax_amount_input.setDecimals(2)
        self.tax_amount_input.setRange(0.00, 99999.99)
        self.tax_amount_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tax_amount_input.setPrefix("$ ")

        totals_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 11)
        self.subtotal_label.setFont(totals_font)
        self.taxable_subtotal_label.setFont(totals_font)
        self.grand_total_label.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold)
        )

        self.save_button.setMinimumSize(120, 40)
        self.cancel_button.setMinimumSize(120, 40)

        save_button_style = f"""QPushButton {{ background-color: {AppConfig.DARK_SUCCESS_ACTION}; color: white; border: 1px solid {QColor(AppConfig.DARK_SUCCESS_ACTION).darker(120).name()}; border-radius: 4px; }} QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}"""
        cancel_button_style = f"""QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; }} QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}"""
        self.save_button.setStyleSheet(save_button_style)
        self.cancel_button.setStyleSheet(cancel_button_style)

        field_style = self._get_input_field_style()
        self.notes_edit.setStyleSheet(field_style)
        self.tax_amount_input.setStyleSheet(field_style)
        self.tax_rate_input.setStyleSheet(field_style)

    def _setup_connections(self):
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.tax_rate_input.valueChanged.connect(self._calculate_tax_from_rate)
        self.tax_amount_input.valueChanged.connect(self._clear_tax_rate_on_manual_edit)
        self.charges_table.currentCellChanged.connect(self._handle_row_change)
        self.notes_edit.textChanged.connect(self._save_notes_for_current_row)

    def _load_initial_data(self):
        """Populates the table with the transactions passed during init."""
        self.charges_table.setRowCount(len(self.transactions))
        for row, trans in enumerate(self.transactions):
            self._setup_row_widgets(row)
            self._populate_row_from_transaction(row, trans)

        self._update_totals()
        if self.charges_table.rowCount() > 0:
            self.charges_table.setCurrentCell(0, 0)

    def _setup_row_widgets(self, row: int):
        """Places the appropriate widgets into the cells of a given row."""
        field_style = self._get_input_field_style()
        code_item = QTableWidgetItem()
        alt_code_item = QTableWidgetItem()
        desc_item = QTableWidgetItem()

        for item in [code_item, alt_code_item, desc_item]:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.charges_table.setItem(row, 0, code_item)
        self.charges_table.setItem(row, 1, alt_code_item)
        self.charges_table.setItem(row, 2, desc_item)

        qty_spinbox = QDoubleSpinBox()
        qty_spinbox.setStyleSheet(field_style)
        qty_spinbox.setDecimals(3)
        qty_spinbox.setRange(0.001, 9999.0)
        qty_spinbox.valueChanged.connect(self._update_totals)
        self.charges_table.setCellWidget(row, 3, qty_spinbox)

        price_spinbox = QDoubleSpinBox()
        price_spinbox.setStyleSheet(field_style)
        price_spinbox.setDecimals(2)
        price_spinbox.setRange(0.00, 99999.99)
        price_spinbox.setPrefix("$ ")
        price_spinbox.valueChanged.connect(self._update_totals)
        self.charges_table.setCellWidget(row, 4, price_spinbox)

        tax_checkbox = QCheckBox()
        tax_checkbox.setStyleSheet(field_style)
        tax_checkbox.stateChanged.connect(self._update_totals)
        chk_widget = QWidget()
        chk_layout = QHBoxLayout(chk_widget)
        chk_layout.addWidget(tax_checkbox)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_layout.setContentsMargins(0, 0, 0, 0)
        self.charges_table.setCellWidget(row, 5, chk_widget)

        total_item = QTableWidgetItem("$0.00")
        total_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.charges_table.setItem(row, 6, total_item)

    def _populate_row_from_transaction(self, row: int, trans: Transaction):
        """Fills a pre-made row's widgets with transaction data."""
        self.charges_table.item(row, 0).setData(
            Qt.ItemDataRole.UserRole, trans.transaction_id
        )
        self.charges_table.item(row, 0).setText(
            trans.charge_code.code if trans.charge_code else "N/A"
        )
        self.charges_table.item(row, 1).setText(
            trans.charge_code.alternate_code if trans.charge_code else "N/A"
        )
        self.charges_table.item(row, 2).setText(trans.description)
        self.charges_table.cellWidget(row, 3).setValue(float(trans.quantity))
        self.charges_table.cellWidget(row, 4).setValue(float(trans.unit_price))
        self.charges_table.cellWidget(row, 5).findChild(QCheckBox).setChecked(
            trans.taxable
        )
        self._row_notes[row] = trans.item_notes or ""

    @Slot(int, int, int, int)
    def _handle_row_change(
        self, currentRow, currentColumn, previousRow, previousColumn
    ):
        if previousRow != -1 and previousRow < self.charges_table.rowCount():
            self._save_notes_for_current_row()
        self._current_notes_row = currentRow
        current_notes = self._row_notes.get(currentRow, "")
        self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText(current_notes)
        self.notes_edit.blockSignals(False)
        self.notes_edit.setPlaceholderText(f"Notes for line {currentRow + 1}...")

    @Slot()
    def _save_notes_for_current_row(self):
        if (
            self._current_notes_row is not None
            and self._current_notes_row < self.charges_table.rowCount()
        ):
            self._row_notes[self._current_notes_row] = (
                self.notes_edit.toPlainText().strip()
            )

    def _update_totals(self):
        subtotal = Decimal(0)
        self._taxable_subtotal = Decimal(0)
        for row in range(self.charges_table.rowCount()):
            try:
                qty_widget = self.charges_table.cellWidget(row, 3)
                price_widget = self.charges_table.cellWidget(row, 4)
                tax_container = self.charges_table.cellWidget(row, 5)

                if qty_widget and price_widget:
                    qty = Decimal(qty_widget.value())
                    price = Decimal(price_widget.value())
                    line_total = (qty * price).quantize(Decimal("0.01"))

                    total_item = self.charges_table.item(row, 6)
                    if not total_item:
                        total_item = QTableWidgetItem()
                        self.charges_table.setItem(row, 6, total_item)
                    total_item.setText(f"${line_total:.2f}")

                    subtotal += line_total
                    if tax_container and tax_container.findChild(QCheckBox).isChecked():
                        self._taxable_subtotal += line_total
            except Exception as e:
                self.logger.warning(f"Could not calculate total for row {row}: {e}")
                continue

        manual_tax = Decimal(self.tax_amount_input.value())
        grand_total = subtotal + manual_tax
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.taxable_subtotal_label.setText(f"${self._taxable_subtotal:.2f}")
        self.grand_total_label.setText(f"${grand_total:.2f}")

    @Slot(float)
    def _calculate_tax_from_rate(self, rate: float):
        tax_rate = Decimal(rate) / Decimal(100)
        tax_amount = (self._taxable_subtotal * tax_rate).quantize(Decimal("0.01"))
        self.tax_amount_input.blockSignals(True)
        self.tax_amount_input.setValue(float(tax_amount))
        self.tax_amount_input.blockSignals(False)
        self._update_totals()

    @Slot(float)
    def _clear_tax_rate_on_manual_edit(self, amount: float):
        self.tax_rate_input.blockSignals(True)
        self.tax_rate_input.setValue(0.0)
        self.tax_rate_input.blockSignals(False)
        self._update_totals()

    def accept(self):
        """Gathers data and sends updates to the controller."""
        self._save_notes_for_current_row()
        errors = []
        for row in range(self.charges_table.rowCount()):
            trans_id = self.charges_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not trans_id:
                continue

            data = {
                "transaction_date": self.transactions[row].transaction_date,
                "description": self.charges_table.item(row, 2).text(),
                "quantity": Decimal(self.charges_table.cellWidget(row, 3).value()),
                "unit_price": Decimal(self.charges_table.cellWidget(row, 4).value()),
                "taxable": self.charges_table.cellWidget(row, 5)
                .findChild(QCheckBox)
                .isChecked(),
                "item_notes": self._row_notes.get(row, "").strip() or None,
            }
            success, message = self.financial_controller.update_charge_transaction(
                transaction_id=trans_id, data=data, current_user_id=self.current_user_id
            )
            if not success:
                errors.append(f"Line {row+1} ({data['description']}): {message}")

        if errors:
            QMessageBox.critical(
                self,
                "Error Saving Charges",
                "Could not save all changes:\n\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(
                self, "Success", "All charges updated successfully."
            )
            self.charges_updated.emit()
            super().accept()

    def _calculate_age(self, birth_date_obj: Optional[date]) -> str:
        if not birth_date_obj or not isinstance(birth_date_obj, date):
            return "Age N/A"
        try:
            today = date.today()
            age_val = (
                today.year
                - birth_date_obj.year
                - (
                    (today.month, today.day)
                    < (birth_date_obj.month, birth_date_obj.day)
                )
            )
            return f"{age_val} yrs"
        except Exception as e:
            self.logger.error(
                f"Error calculating age for date {birth_date_obj}: {e}", exc_info=True
            )
            return "Age Error"

    def _get_display_owner_name(self, horse: Horse) -> str:
        if not horse.owners:
            return "No Owner Associated"

        first_owner = horse.owners[0]
        name_parts = []
        if first_owner.farm_name:
            name_parts.append(first_owner.farm_name)

        person_name_parts = []
        if first_owner.first_name:
            person_name_parts.append(first_owner.first_name)
        if first_owner.last_name:
            person_name_parts.append(first_owner.last_name)

        person_name_str = " ".join(person_name_parts).strip()
        if person_name_str:
            if name_parts:
                name_parts.append(f"({person_name_str})")
            else:
                name_parts.append(person_name_str)

        return (
            " ".join(name_parts) if name_parts else f"Owner ID: {first_owner.owner_id}"
        )

    def _get_display_location_name(self, horse: Horse) -> str:
        return horse.location.location_name if horse.location else "N/A"
