# views/horse/dialogs/add_charge_dialog.py
"""
EDSI Veterinary Management System - Add Charge Dialog
Version: 1.0.2
Purpose: Dialog for adding multiple charges (batch entry) for a horse.
         - Fixed NameError for 'Tuple' type hint by importing from 'typing'.
         - Corrected checkmark icon path construction using AppConfig.PROJECT_ROOT.
Last Updated: June 4, 2025
Author: Gemini
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import date
import os  # MODIFIED: Added os import for path joining

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QPushButton,
    QDialogButtonBox,
    QDoubleSpinBox,
    QSizePolicy,
    QHeaderView,
    QWidget,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, QDate, Signal, Slot
from PySide6.QtGui import QPalette, QColor, QFont

from config.app_config import AppConfig
from models import Horse, Owner, User as UserModel, ChargeCode as ChargeCodeModel
from controllers.financial_controller import FinancialController


class AddChargeDialog(QDialog):
    charges_saved = Signal()

    COL_CHARGE_CODE = 0
    COL_DESCRIPTION = 1
    COL_QTY = 2
    COL_UNIT_PRICE = 3
    COL_TOTAL = 4
    COL_ITEM_NOTES = 5
    COL_PRINT_NOTES = 6
    COL_REMOVE_ROW = 7

    TABLE_COLUMN_COUNT = 8

    def __init__(
        self,
        parent_view: QWidget,
        horse: Horse,
        current_user_id: str,
        financial_controller: FinancialController,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.current_horse = horse
        self.current_user_id = current_user_id
        self.financial_controller = financial_controller

        self.setWindowTitle(
            f"Add Charges for: {self.current_horse.horse_name if self.current_horse else 'N/A'}"
        )
        self.setMinimumSize(900, 700)

        self.owner_combo: Optional[QComboBox] = None
        self.service_date_edit: Optional[QDateEdit] = None
        self.billing_date_edit: Optional[QDateEdit] = None
        self.administered_by_combo: Optional[QComboBox] = None
        self.print_all_notes_checkbox: Optional[QCheckBox] = None

        self.charges_table: Optional[QTableWidget] = None
        self.add_row_btn: Optional[QPushButton] = None

        self.batch_subtotal_label: Optional[QLabel] = None
        self.button_box: Optional[QDialogButtonBox] = None

        self._owners_list: List[Owner] = []
        self._users_list: List[UserModel] = []
        self._charge_codes_list: List[ChargeCodeModel] = []

        self._setup_palette()
        self._setup_ui()
        self._setup_connections()

        self._load_initial_data()
        self._add_charge_row()

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
        palette.setColor(
            QPalette.ColorRole.AlternateBase, QColor(AppConfig.DARK_ITEM_HOVER)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Highlight, QColor(AppConfig.DARK_HIGHLIGHT_BG)
        )
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(AppConfig.DARK_HIGHLIGHT_TEXT)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _get_input_style(self, base_bg=AppConfig.DARK_INPUT_FIELD_BACKGROUND) -> str:
        checkmark_svg_path = "assets/icons/checkmark_light.svg"  # Default
        if hasattr(AppConfig, "PROJECT_ROOT") and AppConfig.PROJECT_ROOT:
            # MODIFIED: Construct full path and replace backslashes for URL
            full_icon_path = os.path.join(
                AppConfig.PROJECT_ROOT, "assets", "icons", "checkmark_light.svg"
            )
            checkmark_svg_path = full_icon_path.replace(os.sep, "/")
            # Check if the file exists for debugging, but don't halt if not found here, Qt will handle it
            if not os.path.exists(full_icon_path):
                self.logger.warning(
                    f"Checkbox icon not found at expected path: {full_icon_path}"
                )
        else:
            self.logger.warning(
                "AppConfig.PROJECT_ROOT not available for icon path construction."
            )

        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox, QDateEdit {{ 
                background-color: {base_bg}; color: {AppConfig.DARK_TEXT_PRIMARY}; 
                border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; 
                padding: 6px 8px; font-size: 13px; min-height: 20px; 
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus {{ 
                border-color: {AppConfig.DARK_PRIMARY_ACTION}; 
            }}
            QComboBox::drop-down {{ border: none; background-color: transparent; }}
            QComboBox::down-arrow {{ color: {AppConfig.DARK_TEXT_SECONDARY}; }} 
            QComboBox QAbstractItemView {{ 
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY}; 
                border: 1px solid {AppConfig.DARK_BORDER}; 
                selection-background-color: {AppConfig.DARK_HIGHLIGHT_BG}; 
                selection-color: {AppConfig.DARK_HIGHLIGHT_TEXT}; 
            }}
             QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px; border: 1px solid {AppConfig.DARK_BORDER};}}
             QCheckBox::indicator:checked {{ 
                 background-color: {AppConfig.DARK_PRIMARY_ACTION}; 
                 border-color: {AppConfig.DARK_PRIMARY_ACTION}; 
                 image: url({checkmark_svg_path}); 
             }}
             QCheckBox {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background: transparent; padding-left: 5px;}}
        """

    def _get_generic_button_style(self) -> str:
        return (
            f"QPushButton {{background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; }}"
        )

    def _create_label(self, text: str, is_bold: bool = False) -> QLabel:
        label = QLabel(text)
        font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 10)
        if is_bold:
            font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; background: transparent;"
        )
        return label

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QGridLayout(header_frame)
        header_layout.setSpacing(10)

        horse_name_display_text = f"<b>Horse:</b> {self.current_horse.horse_name if self.current_horse and self.current_horse.horse_name else 'N/A'}"
        horse_name_display = self._create_label(horse_name_display_text)
        header_layout.addWidget(horse_name_display, 0, 0, 1, 4)

        header_layout.addWidget(
            self._create_label("Owner*:"), 1, 0, Qt.AlignmentFlag.AlignRight
        )
        self.owner_combo = QComboBox()
        header_layout.addWidget(self.owner_combo, 1, 1)

        header_layout.addWidget(
            self._create_label("Administered By*:"), 1, 2, Qt.AlignmentFlag.AlignRight
        )
        self.administered_by_combo = QComboBox()
        header_layout.addWidget(self.administered_by_combo, 1, 3)

        header_layout.addWidget(
            self._create_label("Service Date*:"), 2, 0, Qt.AlignmentFlag.AlignRight
        )
        self.service_date_edit = QDateEdit(QDate.currentDate())
        self.service_date_edit.setCalendarPopup(True)
        self.service_date_edit.setDisplayFormat("yyyy-MM-dd")
        header_layout.addWidget(self.service_date_edit, 2, 1)

        header_layout.addWidget(
            self._create_label("Billing Date:"), 2, 2, Qt.AlignmentFlag.AlignRight
        )
        self.billing_date_edit = QDateEdit()
        self.billing_date_edit.setCalendarPopup(True)
        self.billing_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.billing_date_edit.setSpecialValueText(" ")
        self.billing_date_edit.setDate(QDate.currentDate())
        header_layout.addWidget(self.billing_date_edit, 2, 3)

        self.print_all_notes_checkbox = QCheckBox("Print All Item Notes on Statement")
        self.print_all_notes_checkbox.setChecked(True)
        header_layout.addWidget(self.print_all_notes_checkbox, 3, 0, 1, 2)

        input_style = self._get_input_style()
        for i in range(header_layout.count()):
            widget = header_layout.itemAt(i).widget()
            if isinstance(widget, (QComboBox, QDateEdit, QCheckBox)):
                widget.setStyleSheet(input_style)

        main_layout.addWidget(header_frame)

        self.charges_table = QTableWidget()
        self.charges_table.setColumnCount(self.TABLE_COLUMN_COUNT)
        self.charges_table.setHorizontalHeaderLabels(
            [
                "Charge Code",
                "Description",
                "Qty",
                "Unit Price",
                "Total",
                "Item Notes",
                "Print",
                "Action",
            ]
        )
        self.charges_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.charges_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        header = self.charges_table.horizontalHeader()
        header.setSectionResizeMode(
            self.COL_CHARGE_CODE, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            self.COL_DESCRIPTION, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            self.COL_QTY, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_UNIT_PRICE, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_TOTAL, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_ITEM_NOTES, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            self.COL_PRINT_NOTES, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COL_REMOVE_ROW, QHeaderView.ResizeMode.ResizeToContents
        )

        self.charges_table.setMinimumHeight(300)
        main_layout.addWidget(self.charges_table)

        self.add_row_btn = QPushButton("➕ Add Charge Item")
        self.add_row_btn.setStyleSheet(
            self._get_generic_button_style().replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
            )
        )
        add_row_layout = QHBoxLayout()
        add_row_layout.addStretch()
        add_row_layout.addWidget(self.add_row_btn)
        main_layout.addLayout(add_row_layout)

        summary_layout = QHBoxLayout()
        summary_layout.addStretch()
        summary_layout.addWidget(self._create_label("Batch Subtotal:", is_bold=True))
        self.batch_subtotal_label = self._create_label("$0.00", is_bold=True)
        font = self.batch_subtotal_label.font()
        font.setPointSize(12)
        self.batch_subtotal_label.setFont(font)
        summary_layout.addWidget(self.batch_subtotal_label)
        main_layout.addLayout(summary_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            "Save Charges"
        )

        generic_btn_style = self._get_generic_button_style()
        save_btn_style = (
            generic_btn_style.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
            )
            + "color: white;"
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(
            save_btn_style
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            generic_btn_style
        )

        main_layout.addWidget(self.button_box)

    def _setup_connections(self):
        if self.button_box:
            self.button_box.accepted.connect(self._on_save_charges)
            self.button_box.rejected.connect(self.reject)

        if self.add_row_btn:
            self.add_row_btn.clicked.connect(self._add_charge_row)

        if self.charges_table:
            self.charges_table.cellChanged.connect(self._on_table_cell_changed)

    def _load_initial_data(self):
        self.logger.debug("Loading initial data for AddChargeDialog...")
        if self.current_horse and self.current_horse.owners:
            self._owners_list = self.current_horse.owners
            if self.owner_combo:
                self.owner_combo.clear()
                for owner in self._owners_list:
                    display_name = (
                        owner.farm_name
                        or f"{owner.first_name or ''} {owner.last_name or ''}".strip()
                        or f"ID: {owner.owner_id}"
                    )
                    self.owner_combo.addItem(display_name, owner.owner_id)
                if self._owners_list:
                    self.owner_combo.setCurrentIndex(0)
        else:
            self._owners_list = self.financial_controller.get_active_owners_for_lookup()
            if self.owner_combo:
                self.owner_combo.clear()
                for owner in self._owners_list:
                    display_name = (
                        owner.farm_name
                        or f"{owner.first_name or ''} {owner.last_name or ''}".strip()
                        or f"ID: {owner.owner_id}"
                    )
                    self.owner_combo.addItem(display_name, owner.owner_id)

        self._users_list = self.financial_controller.get_active_users_for_lookup()
        if self.administered_by_combo:
            self.administered_by_combo.clear()
            current_user_found_idx = -1
            for idx, user in enumerate(self._users_list):
                self.administered_by_combo.addItem(
                    user.user_name or user.user_id, user.user_id
                )
                if user.user_id == self.current_user_id:
                    current_user_found_idx = idx
            if current_user_found_idx != -1:
                self.administered_by_combo.setCurrentIndex(current_user_found_idx)

        self._charge_codes_list = (
            self.financial_controller.get_charge_codes_for_lookup()
        )
        self.logger.debug(
            f"Loaded {len(self._charge_codes_list)} charge codes for lookup."
        )

    def _add_charge_row(self, charge_data: Optional[Dict] = None):
        if not self.charges_table:
            return

        row_position = self.charges_table.rowCount()
        self.charges_table.insertRow(row_position)

        charge_code_combo = QComboBox()
        charge_code_combo.addItem("Select Charge Code...", None)
        for cc in self._charge_codes_list:
            charge_code_combo.addItem(f"{cc.code} - {cc.description[:30]}...", cc.id)
        charge_code_combo.setStyleSheet(self._get_input_style())
        self.charges_table.setCellWidget(
            row_position, self.COL_CHARGE_CODE, charge_code_combo
        )
        charge_code_combo.currentIndexChanged.connect(
            lambda idx, r=row_position: self._on_charge_code_selected_in_row(r, idx)
        )

        desc_edit = QLineEdit(charge_data.get("description", "") if charge_data else "")
        desc_edit.setStyleSheet(self._get_input_style())
        self.charges_table.setCellWidget(row_position, self.COL_DESCRIPTION, desc_edit)

        qty_spin = QDoubleSpinBox()
        qty_spin.setDecimals(3)
        qty_spin.setRange(0.001, 9999.999)
        qty_spin.setValue(charge_data.get("quantity", 1.000) if charge_data else 1.000)
        qty_spin.setStyleSheet(self._get_input_style())
        self.charges_table.setCellWidget(row_position, self.COL_QTY, qty_spin)

        price_spin = QDoubleSpinBox()
        price_spin.setDecimals(2)
        price_spin.setRange(0.00, 99999.99)
        price_spin.setPrefix("$ ")
        price_spin.setValue(
            charge_data.get("unit_price", 0.00) if charge_data else 0.00
        )
        price_spin.setStyleSheet(self._get_input_style())
        self.charges_table.setCellWidget(row_position, self.COL_UNIT_PRICE, price_spin)

        total_label = QLabel("$0.00")
        total_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; padding: 6px; background-color: transparent;"
        )
        total_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.charges_table.setCellWidget(row_position, self.COL_TOTAL, total_label)

        notes_edit = QLineEdit(charge_data.get("item_notes", "") if charge_data else "")
        notes_edit.setStyleSheet(self._get_input_style())
        self.charges_table.setCellWidget(row_position, self.COL_ITEM_NOTES, notes_edit)

        print_chk = QCheckBox()
        print_chk.setChecked(
            self.print_all_notes_checkbox.isChecked()
            if self.print_all_notes_checkbox
            else True
        )
        chk_widget = QWidget()
        chk_layout = QHBoxLayout(chk_widget)
        chk_layout.addWidget(print_chk)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_layout.setContentsMargins(0, 0, 0, 0)
        chk_widget.setStyleSheet("background:transparent;")
        self.charges_table.setCellWidget(row_position, self.COL_PRINT_NOTES, chk_widget)

        remove_btn = QPushButton("🗑️")
        remove_btn.setStyleSheet(
            self._get_generic_button_style().replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_DANGER_ACTION
            )
            + "padding: 5px; min-width: 30px; max-width:30px;"
        )
        remove_btn.setToolTip("Remove this charge item")
        remove_btn.clicked.connect(
            self._remove_charge_row_by_sender
        )  # Connect without lambda
        self.charges_table.setCellWidget(row_position, self.COL_REMOVE_ROW, remove_btn)

        qty_spin.valueChanged.connect(
            lambda val, r=row_position: self._update_row_total(r)
        )
        price_spin.valueChanged.connect(
            lambda val, r=row_position: self._update_row_total(r)
        )

        self._update_row_total(row_position)

    @Slot()
    def _remove_charge_row_by_sender(self):
        if not self.charges_table:
            return
        button = self.sender()
        if button and isinstance(
            button, QPushButton
        ):  # Check if sender is a QPushButton
            # Find the row of the button
            for r in range(self.charges_table.rowCount()):
                if self.charges_table.cellWidget(r, self.COL_REMOVE_ROW) == button:
                    self.charges_table.removeRow(r)
                    self._update_batch_subtotal()
                    return  # Exit after removing the correct row

    def _on_charge_code_selected_in_row(self, row: int, combo_box_index: int):
        if not self.charges_table:
            return

        charge_code_combo_widget = self.charges_table.cellWidget(
            row, self.COL_CHARGE_CODE
        )
        if not isinstance(charge_code_combo_widget, QComboBox):
            return

        selected_charge_code_id = charge_code_combo_widget.itemData(combo_box_index)

        desc_widget = self.charges_table.cellWidget(row, self.COL_DESCRIPTION)
        price_widget = self.charges_table.cellWidget(row, self.COL_UNIT_PRICE)

        if selected_charge_code_id is not None:
            charge_code_obj = next(
                (
                    cc
                    for cc in self._charge_codes_list
                    if cc.id == selected_charge_code_id
                ),
                None,
            )
            if charge_code_obj:
                if isinstance(desc_widget, QLineEdit):
                    desc_widget.setText(charge_code_obj.description)
                if isinstance(price_widget, QDoubleSpinBox):
                    price_widget.setValue(float(charge_code_obj.standard_charge))
            else:
                if isinstance(desc_widget, QLineEdit):
                    desc_widget.clear()
                if isinstance(price_widget, QDoubleSpinBox):
                    price_widget.setValue(0.00)
        else:
            if isinstance(desc_widget, QLineEdit):
                desc_widget.clear()
            if isinstance(price_widget, QDoubleSpinBox):
                price_widget.setValue(0.00)

        self._update_row_total(row)

    def _update_row_total(self, row: int):
        if not self.charges_table:
            return

        qty_widget = self.charges_table.cellWidget(row, self.COL_QTY)
        price_widget = self.charges_table.cellWidget(row, self.COL_UNIT_PRICE)
        total_widget = self.charges_table.cellWidget(row, self.COL_TOTAL)

        if (
            isinstance(qty_widget, QDoubleSpinBox)
            and isinstance(price_widget, QDoubleSpinBox)
            and isinstance(total_widget, QLabel)
        ):

            qty = qty_widget.value()
            price = price_widget.value()
            row_total = qty * price
            total_widget.setText(f"${row_total:.2f}")

        self._update_batch_subtotal()

    def _update_batch_subtotal(self):
        if not self.charges_table or not self.batch_subtotal_label:
            return

        total_sum = 0.0
        for r in range(self.charges_table.rowCount()):
            total_widget = self.charges_table.cellWidget(r, self.COL_TOTAL)
            if isinstance(total_widget, QLabel):
                try:
                    total_sum += float(total_widget.text().replace("$", ""))
                except ValueError:
                    pass

        self.batch_subtotal_label.setText(f"${total_sum:.2f}")

    @Slot(int, int)
    def _on_table_cell_changed(self, row: int, column: int):
        pass

    def _collect_charge_items_data(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not self.charges_table:
            return [], ["Table widget not initialized."]

        items_data = []
        errors: List[str] = []

        for r in range(self.charges_table.rowCount()):
            line_num = r + 1
            item: Dict[str, Any] = {}

            cc_combo_widget = self.charges_table.cellWidget(r, self.COL_CHARGE_CODE)
            if isinstance(cc_combo_widget, QComboBox):
                item["charge_code_id"] = cc_combo_widget.currentData()
                if item["charge_code_id"] is None:
                    errors.append(f"Line {line_num}: Charge Code must be selected.")
            else:
                errors.append(f"Line {line_num}: Charge Code widget error.")

            desc_widget = self.charges_table.cellWidget(r, self.COL_DESCRIPTION)
            if isinstance(desc_widget, QLineEdit):
                item["description"] = desc_widget.text().strip()
                if not item["description"]:
                    errors.append(f"Line {line_num}: Description is required.")
            else:
                errors.append(f"Line {line_num}: Description widget error.")

            qty_widget = self.charges_table.cellWidget(r, self.COL_QTY)
            if isinstance(qty_widget, QDoubleSpinBox):
                item["quantity"] = qty_widget.value()
                if item["quantity"] <= 0:
                    errors.append(f"Line {line_num}: Quantity must be greater than 0.")
            else:
                errors.append(f"Line {line_num}: Quantity widget error.")

            price_widget = self.charges_table.cellWidget(r, self.COL_UNIT_PRICE)
            if isinstance(price_widget, QDoubleSpinBox):
                item["unit_price"] = price_widget.value()
            else:
                errors.append(f"Line {line_num}: Unit Price widget error.")

            notes_widget = self.charges_table.cellWidget(r, self.COL_ITEM_NOTES)
            if isinstance(notes_widget, QLineEdit):
                item["item_notes"] = notes_widget.text().strip() or None

            print_chk_container = self.charges_table.cellWidget(r, self.COL_PRINT_NOTES)
            if (
                isinstance(print_chk_container, QWidget)
                and print_chk_container.layout()
                and isinstance(
                    print_chk_container.layout().itemAt(0).widget(), QCheckBox
                )
            ):
                item["item_print_on_statement"] = (
                    print_chk_container.layout().itemAt(0).widget().isChecked()
                )
            else:
                item["item_print_on_statement"] = True

            # Check if any error occurred FOR THIS ROW before appending
            current_row_has_error = any(f"Line {line_num}" in e for e in errors)
            if not current_row_has_error:
                items_data.append(item)

        return items_data, errors

    def _on_save_charges(self):
        self.logger.info("Save Charges clicked.")

        header_errors: List[str] = []
        selected_owner_id = self.owner_combo.currentData() if self.owner_combo else None
        if selected_owner_id is None:
            header_errors.append("Owner must be selected.")

        service_date_val = (
            self.service_date_edit.date().toPython() if self.service_date_edit else None
        )
        if not service_date_val:
            header_errors.append("Service Date is required.")
        elif service_date_val > date.today():
            header_errors.append("Service Date cannot be in the future.")

        billing_date_val = None
        if (
            self.billing_date_edit
            and self.billing_date_edit.text().strip() != ""
            and self.billing_date_edit.specialValueText()
            != self.billing_date_edit.text()
        ):
            billing_date_val = self.billing_date_edit.date().toPython()
            if (
                billing_date_val
                and service_date_val
                and billing_date_val < service_date_val
            ):
                header_errors.append("Billing Date cannot be before Service Date.")

        administered_by_user_id_val = (
            self.administered_by_combo.currentData()
            if self.administered_by_combo
            else None
        )
        if administered_by_user_id_val is None:
            header_errors.append("'Administered By' user must be selected.")

        if header_errors:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct header information:\n- " + "\n- ".join(header_errors),
            )
            return

        charge_items, item_errors = self._collect_charge_items_data()

        # Consolidate all errors before showing QMessageBox
        all_validation_errors = header_errors + item_errors
        # Also, call the controller's validation for each item if it exists
        # This part was in the financial_controller, let's assume it's called by add_charge_batch_to_horse
        # For UI, we've done widget-level checks.

        if (
            item_errors
        ):  # If _collect_charge_items_data found structural issues or basic item errors
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct charge items:\n- " + "\n- ".join(item_errors),
            )
            return

        if not charge_items:
            QMessageBox.information(
                self, "No Charges", "Please add at least one charge item to save."
            )
            return

        success, message, _ = self.financial_controller.add_charge_batch_to_horse(
            horse_id=self.current_horse.horse_id,
            owner_id=selected_owner_id,
            charge_items=charge_items,
            batch_service_date=service_date_val,
            batch_billing_date=billing_date_val,
            administered_by_user_id=administered_by_user_id_val,
            batch_print_on_statement=(
                self.print_all_notes_checkbox.isChecked()
                if self.print_all_notes_checkbox
                else True
            ),
        )

        if success:
            QMessageBox.information(self, "Success", message)
            self.charges_saved.emit()
            super().accept()
        else:
            # Message from controller might already include specific validation errors
            QMessageBox.critical(self, "Save Failed", message)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    class MockHorse:
        horse_id = 1
        horse_name = "Test Horse"
        owners = []

    class MockOwner:
        def __init__(self, id, farm_name, first_name="", last_name=""):
            self.owner_id = id
            self.farm_name = farm_name
            self.first_name = first_name
            self.last_name = last_name

    class MockUser:
        def __init__(self, id, name):
            self.user_id = id
            self.user_name = name

    class MockChargeCode:
        def __init__(self, id, code, desc, price):
            self.id = id
            self.code = code
            self.description = desc
            self.standard_charge = price  # Should be Decimal or float compatible

    mock_owner1 = MockOwner(1, "Sunrise Stables", "John", "Doe")
    mock_owner2 = MockOwner(2, "Willow Creek", "Jane", "Smith")
    mock_horse_obj = MockHorse()
    mock_horse_obj.owners = [mock_owner1, mock_owner2]

    mock_user1 = MockUser("vet1", "Dr. Alice")
    mock_user2 = MockUser("tech1", "Bob The Tech")

    mock_cc1 = MockChargeCode(101, "VAC01", "Annual Vaccination", 75.00)
    mock_cc2 = MockChargeCode(102, "EXM05", "Lameness Exam", 150.00)

    class MockController:
        def get_active_owners_for_lookup(self):
            return [mock_owner1, mock_owner2]

        def get_active_users_for_lookup(self):
            return [mock_user1, mock_user2]

        def get_charge_codes_for_lookup(self):
            return [mock_cc1, mock_cc2]

        def add_charge_batch_to_horse(
            self,
            horse_id,
            owner_id,
            charge_items,
            batch_service_date,
            batch_billing_date,
            administered_by_user_id,
            batch_print_on_statement,
        ):
            self.logger.info(
                f"MockController: add_charge_batch_to_horse called with: horse_id={horse_id}, owner_id={owner_id}, items={len(charge_items)}"
            )

            # Simulate controller-side validation (example)
            all_item_errors = []
            for i, item in enumerate(charge_items):
                if not item.get("charge_code_id"):
                    all_item_errors.append(
                        f"Controller Validation Line {i+1}: Charge Code is missing."
                    )
                if not item.get("description"):
                    all_item_errors.append(
                        f"Controller Validation Line {i+1}: Description is missing."
                    )
                # Add more specific validations here as in your actual controller's validate_charge_data

            if all_item_errors:
                return (
                    False,
                    "Controller validation failed:\n- " + "\n- ".join(all_item_errors),
                    None,
                )

            return True, f"{len(charge_items)} charges saved successfully (mock).", []

        def __init__(self):  # Add logger to mock controller
            self.logger = logging.getLogger(self.__class__.__name__)

    app = QApplication(sys.argv)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s",
    )

    mock_fc = MockController()

    # Ensure parent_view=None is acceptable or provide a mock QWidget
    dialog = AddChargeDialog(
        parent_view=None,
        horse=mock_horse_obj,
        current_user_id="vet1",
        financial_controller=mock_fc,
    )
    dialog.show()
    sys.exit(app.exec())
