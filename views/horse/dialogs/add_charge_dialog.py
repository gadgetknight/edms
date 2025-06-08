# views/horse/dialogs/add_charge_dialog.py
"""
EDSI Veterinary Management System - Add Charge Dialog
Version: 3.3.1
Purpose: Dialog for entering multiple charge transactions for a horse using a table.
Last Updated: June 7, 2025
Author: Gemini

Changelog:
- v3.3.1 (2025-06-07):
    - Bug Fix: Corrected the behavior of the Enter key. It no longer closes the
      dialog but now correctly adds a new charge row for rapid data entry.
    - Removed the `EnterKeyEventFilter` in favor of connecting the `returnPressed`
      signal directly from the QLineEdit widgets in the table.
    - Disabled the default button behavior on the dialog's button box.
- v3.3.0 (2025-06-07):
    - Added a tax rate input field to allow for percentage-based tax calculation.
- v3.2.0 (2025-06-07):
    - Re-styled all input fields to match the BasicInfoTab style.
- v3.1.0 (2025-06-07):
    - Updated header format to match the main HorseUnifiedManagement screen.
    - Repositioned the Save/Cancel buttons to the bottom-left of the dialog.
- v3.0.3 (2025-06-07):
    - Bug Fix: Corrected signal name from `currentRowChanged` to `currentCellChanged`.
- v3.0.2 (2025-06-07):
    - Bug Fix: Corrected an AttributeError by using QAbstractSpinBox.ButtonSymbols.NoButtons.
- v3.0.1 (2025-06-07):
    - Bug Fix: Imported the `Slot` decorator from PySide6.QtCore.
- v3.0.0 (2025-06-07):
    - Complete refactor to a `QTableWidget`-based interface for charge entry.
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
    QSpacerItem,
    QSizePolicy,
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
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QObject, Slot
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


class AddChargeDialog(QDialog):
    """A dialog for adding multiple charge items for a horse in a table."""

    charges_saved = Signal(list)

    def __init__(
        self,
        horse: Horse,
        financial_controller: FinancialController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse = horse
        self.financial_controller = financial_controller
        self.current_user_id = QApplication.instance().current_user_id

        self.setWindowTitle(f"Add Charges for: {self.horse.horse_name}")
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
            QCompleter::popup {{
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
            }}
            QCompleter::popup::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
        """

    def _setup_ui(self):
        """Initializes and lays out the UI widgets based on the new design."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Header ---
        self.horse_title_label = QLabel()
        self.horse_info_line_label = QLabel()
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.horse_title_label)
        header_layout.addWidget(self.horse_info_line_label)
        main_layout.addWidget(header_widget)

        # --- Main Content: Table and Notes ---
        content_layout = QHBoxLayout()
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.charges_table = QTableWidget()
        table_layout.addWidget(self.charges_table)

        self.notes_edit = QTextEdit()
        table_layout.addWidget(self.notes_edit)
        table_layout.setStretchFactor(self.charges_table, 3)
        table_layout.setStretchFactor(self.notes_edit, 1)

        content_layout.addWidget(table_container)
        main_layout.addLayout(content_layout, 1)

        # --- Footer ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)

        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton(
            "Save Charges", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.cancel_button = self.button_box.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.save_button.setAutoDefault(False)  # Prevent Enter from triggering save
        self.cancel_button.setAutoDefault(False)

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

        footer_layout.addWidget(self.button_box)
        footer_layout.addStretch()
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
        self.charges_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
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

        save_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                color: white;
                border: 1px solid {QColor(AppConfig.DARK_SUCCESS_ACTION).darker(120).name()};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        cancel_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
        """
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
        self._charge_codes_list = (
            self.financial_controller.get_charge_codes_for_lookup()
        )
        self._charge_code_lookup = {
            cc.code.upper(): cc for cc in self._charge_codes_list
        }
        self._alt_code_lookup = {
            cc.alternate_code.upper(): cc
            for cc in self._charge_codes_list
            if cc.alternate_code
        }
        self.logger.debug(f"Loaded {len(self._charge_codes_list)} charge codes.")
        self._add_charge_row()

    @Slot(int)
    def _handle_enter_in_row(self, row: int):
        self._add_charge_row(from_row=row)

    def _add_charge_row(self, from_row: Optional[int] = None):
        """Adds a new, empty row to the charges table."""
        if from_row is None:
            row_to_insert = self.charges_table.rowCount()
        else:
            row_to_insert = from_row + 1

        self.charges_table.insertRow(row_to_insert)
        self._setup_row_widgets(row_to_insert)
        self.charges_table.setCurrentCell(row_to_insert, 0)

    def _setup_row_widgets(self, row: int):
        """Places the appropriate widgets into the cells of a given row."""
        field_style = self._get_input_field_style()

        # Code
        code_edit = QLineEdit()
        code_edit.setStyleSheet(field_style)
        code_completer = QCompleter([cc.code for cc in self._charge_codes_list])
        code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        code_completer.popup().setStyleSheet(field_style)
        code_edit.setCompleter(code_completer)
        code_edit.editingFinished.connect(lambda: self._on_code_entered(row))
        code_edit.returnPressed.connect(lambda: self._handle_enter_in_row(row))
        self.charges_table.setCellWidget(row, 0, code_edit)

        # Alt Code
        alt_code_edit = QLineEdit()
        alt_code_edit.setStyleSheet(field_style)
        alt_code_completer = QCompleter(
            [cc.alternate_code for cc in self._charge_codes_list if cc.alternate_code]
        )
        alt_code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        alt_code_completer.popup().setStyleSheet(field_style)
        alt_code_edit.setCompleter(alt_code_completer)
        alt_code_edit.editingFinished.connect(lambda: self._on_alt_code_entered(row))
        alt_code_edit.returnPressed.connect(lambda: self._handle_enter_in_row(row))
        self.charges_table.setCellWidget(row, 1, alt_code_edit)

        # Description (read-only)
        desc_item = QTableWidgetItem()
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.charges_table.setItem(row, 2, desc_item)

        # Qty
        qty_spinbox = QDoubleSpinBox()
        qty_spinbox.setStyleSheet(field_style)
        qty_spinbox.setDecimals(3)
        qty_spinbox.setRange(0.001, 9999.0)
        qty_spinbox.setValue(1.0)
        qty_spinbox.valueChanged.connect(self._update_totals)
        self.charges_table.setCellWidget(row, 3, qty_spinbox)

        # Unit Price
        price_spinbox = QDoubleSpinBox()
        price_spinbox.setStyleSheet(field_style)
        price_spinbox.setDecimals(2)
        price_spinbox.setRange(0.00, 99999.99)
        price_spinbox.setPrefix("$ ")
        price_spinbox.valueChanged.connect(self._update_totals)
        self.charges_table.setCellWidget(row, 4, price_spinbox)

        # Taxable
        tax_checkbox = QCheckBox()
        tax_checkbox.setStyleSheet(field_style)
        tax_checkbox.stateChanged.connect(self._update_totals)
        chk_widget = QWidget()
        chk_layout = QHBoxLayout(chk_widget)
        chk_layout.addWidget(tax_checkbox)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_layout.setContentsMargins(0, 0, 0, 0)
        self.charges_table.setCellWidget(row, 5, chk_widget)

        # Total
        total_item = QTableWidgetItem("$0.00")
        total_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.charges_table.setItem(row, 6, total_item)

    def _on_code_entered(self, row: int):
        code_widget = self.charges_table.cellWidget(row, 0)
        if isinstance(code_widget, QLineEdit):
            code = code_widget.text().upper()
            charge_code = self._charge_code_lookup.get(code)
            self._populate_row_from_charge_code(row, charge_code)

    def _on_alt_code_entered(self, row: int):
        alt_code_widget = self.charges_table.cellWidget(row, 1)
        if isinstance(alt_code_widget, QLineEdit):
            alt_code = alt_code_widget.text().upper()
            charge_code = self._alt_code_lookup.get(alt_code)
            self._populate_row_from_charge_code(row, charge_code)

    def _populate_row_from_charge_code(
        self, row: int, charge_code: Optional[ChargeCode]
    ):
        if charge_code:
            code_widget = self.charges_table.cellWidget(row, 0)
            if isinstance(code_widget, QLineEdit):
                code_widget.setText(charge_code.code)
            alt_code_widget = self.charges_table.cellWidget(row, 1)
            if isinstance(alt_code_widget, QLineEdit):
                alt_code_widget.setText(charge_code.alternate_code or "")
            self.charges_table.item(row, 2).setText(charge_code.description)
            price_widget = self.charges_table.cellWidget(row, 4)
            if isinstance(price_widget, QDoubleSpinBox):
                price_widget.setValue(float(charge_code.standard_charge))
            tax_widget_container = self.charges_table.cellWidget(row, 5)
            if tax_widget_container:
                tax_checkbox = tax_widget_container.findChild(QCheckBox)
                if tax_checkbox:
                    tax_checkbox.setChecked(charge_code.taxable)
        self._update_totals()

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

        if currentRow != -1:
            self.notes_edit.setPlaceholderText(f"Notes for line {currentRow + 1}...")
        else:
            self.notes_edit.setPlaceholderText(
                "Notes for the selected line item will appear here..."
            )

    @Slot()
    def _save_notes_for_current_row(self):
        if (
            self._current_notes_row is not None
            and self._current_notes_row < self.charges_table.rowCount()
        ):
            notes = self.notes_edit.toPlainText().strip()
            if notes:
                self._row_notes[self._current_notes_row] = notes
            elif self._current_notes_row in self._row_notes:
                del self._row_notes[self._current_notes_row]

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
                    self.charges_table.item(row, 6).setText(f"${line_total:.2f}")

                    subtotal += line_total
                    if tax_container and tax_container.findChild(QCheckBox).isChecked():
                        self._taxable_subtotal += line_total
            except (InvalidOperation, TypeError, AttributeError) as e:
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

    def get_data_from_table(self) -> List[Dict[str, Any]]:
        """Collects and validates data from all rows in the table."""
        charges_to_save = []
        for row in range(self.charges_table.rowCount()):
            try:
                code_widget = self.charges_table.cellWidget(row, 0)
                desc_item = self.charges_table.item(row, 2)
                qty_widget = self.charges_table.cellWidget(row, 3)
                price_widget = self.charges_table.cellWidget(row, 4)
                tax_container = self.charges_table.cellWidget(row, 5)

                code = code_widget.text().upper()
                charge_code_obj = self._charge_code_lookup.get(code)

                if not charge_code_obj or not desc_item or not desc_item.text():
                    continue

                charges_to_save.append(
                    {
                        "charge_code_id": charge_code_obj.id,
                        "description": desc_item.text(),
                        "quantity": Decimal(qty_widget.value()),
                        "unit_price": Decimal(price_widget.value()),
                        "taxable": tax_container.findChild(QCheckBox).isChecked(),
                        "item_notes": self._row_notes.get(row),
                    }
                )
            except Exception as e:
                self.logger.error(f"Error processing row {row} for saving: {e}")
        return charges_to_save

    def accept(self):
        """Gathers data from the table and sends it to the controller to be saved."""
        self._save_notes_for_current_row()
        charges_to_save = self.get_data_from_table()

        if not charges_to_save:
            QMessageBox.warning(
                self, "No Charges", "Please add at least one valid charge item."
            )
            return

        if not self.horse.owners:
            QMessageBox.critical(
                self,
                "Billing Error",
                "This horse has no owner assigned and cannot be billed.",
            )
            return

        success, message, new_transactions = (
            self.financial_controller.add_charge_batch_to_horse(
                horse_id=self.horse.horse_id,
                owner_id=self.horse.owners[0].owner_id,
                charge_items=charges_to_save,
                batch_transaction_date=date.today(),
                administered_by_user_id=self.current_user_id,
            )
        )

        if success:
            self.charges_saved.emit(new_transactions)
            super().accept()
        else:
            QMessageBox.critical(self, "Error Saving Charges", message)

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
