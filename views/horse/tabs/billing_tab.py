# views/horse/tabs/billing_tab.py
"""
EDSI Veterinary Management System - Horse Billing Tab
Version: 1.0.0
Purpose: UI for displaying and managing billing charges for a specific horse.
Last Updated: June 4, 2025
Author: Gemini
"""

import logging
from typing import Optional, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor

from config.app_config import AppConfig  # For styling constants
from models import Horse, Transaction  # For type hinting
from controllers.financial_controller import FinancialController
from views.horse.dialogs.add_charge_dialog import (
    AddChargeDialog,
)  # Assuming it's in this path

if TYPE_CHECKING:
    from views.horse.horse_unified_management import HorseUnifiedManagement


class BillingTab(QWidget):
    charges_updated = Signal()  # To notify parent view if charges change

    # Column indices for the charges table
    COL_DATE_SERVICE = 0
    COL_DATE_BILLING = 1
    COL_CHARGE_CODE = 2
    COL_DESCRIPTION = 3
    COL_QTY = 4
    COL_UNIT_PRICE = 5
    COL_TOTAL_AMOUNT = 6
    COL_ADMIN_BY = 7
    COL_NOTES = 8
    COL_INVOICE_ID = 9

    CHARGES_TABLE_COLUMN_COUNT = 10

    def __init__(
        self,
        parent_view: "HorseUnifiedManagement",
        financial_controller: FinancialController,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.financial_controller = financial_controller
        self.current_horse: Optional[Horse] = None
        self.current_user_id: str = (
            parent_view.current_user
            if hasattr(parent_view, "current_user")
            else "SYSTEM"
        )

        self.charges_table: Optional[QTableWidget] = None
        self.add_charge_btn: Optional[QPushButton] = None
        self.no_charges_label: Optional[QLabel] = None

        self._setup_ui()
        self._setup_connections()
        self.update_buttons_state()

    def _get_generic_button_style(self, primary: bool = False) -> str:
        base_style = (
            f"QPushButton {{background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; padding: 8px 15px; "
            f"font-size: 13px; font-weight: 500; min-height: 30px;}} "
            f"QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; }}"
        )
        if primary:
            base_style = base_style.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
            )
            # Add other primary-specific styles if needed, e.g., text color white
        return base_style

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Action Buttons ---
        action_layout = QHBoxLayout()
        self.add_charge_btn = QPushButton("➕ Add New Charges")
        self.add_charge_btn.setStyleSheet(self._get_generic_button_style(primary=True))
        action_layout.addWidget(self.add_charge_btn)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        # --- Charges Table ---
        self.charges_table = QTableWidget()
        self.charges_table.setColumnCount(self.CHARGES_TABLE_COLUMN_COUNT)
        self.charges_table.setHorizontalHeaderLabels(
            [
                "Service Date",
                "Billing Date",
                "Code",
                "Description",
                "Qty",
                "Unit Price",
                "Total",
                "Admin",
                "Notes",
                "Invoice #",
            ]
        )
        self.charges_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.charges_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.charges_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )  # Read-only display
        self.charges_table.verticalHeader().setVisible(False)
        self.charges_table.setShowGrid(True)  # Show grid lines
        self.charges_table.setStyleSheet(
            f"""
            QTableWidget {{
                gridline-color: {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {AppConfig.DARK_BORDER};
                font-weight: 500;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {AppConfig.DARK_HIGHLIGHT_BG};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
        """
        )

        header = self.charges_table.horizontalHeader()
        header.setSectionResizeMode(
            self.COL_DESCRIPTION, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(self.COL_NOTES, QHeaderView.ResizeMode.Stretch)
        for col in [
            self.COL_DATE_SERVICE,
            self.COL_DATE_BILLING,
            self.COL_CHARGE_CODE,
            self.COL_QTY,
            self.COL_UNIT_PRICE,
            self.COL_TOTAL_AMOUNT,
            self.COL_ADMIN_BY,
            self.COL_INVOICE_ID,
        ]:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.charges_table, 1)  # Stretch factor 1

        # --- No Charges Label (shown when table is empty) ---
        self.no_charges_label = QLabel("No charges recorded for this horse.")
        self.no_charges_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_charges_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; font-size: 14px; padding: 20px;"
        )
        self.no_charges_label.setVisible(False)  # Initially hidden
        main_layout.addWidget(self.no_charges_label)

    def _setup_connections(self):
        if self.add_charge_btn:
            self.add_charge_btn.clicked.connect(self._launch_add_charge_dialog)

    def load_charges_for_horse(self, horse: Optional[Horse]):
        self.current_horse = horse
        if not self.charges_table:
            return

        self.charges_table.setRowCount(0)  # Clear existing rows

        if self.current_horse and self.current_horse.horse_id is not None:
            self.logger.debug(
                f"BillingTab: Loading charges for horse ID {self.current_horse.horse_id}"
            )
            transactions = self.financial_controller.get_transactions_for_horse(
                self.current_horse.horse_id
            )

            if transactions:
                self.charges_table.setVisible(True)
                self.no_charges_label.setVisible(False)
                self.charges_table.setRowCount(len(transactions))
                for row_idx, trans in enumerate(transactions):
                    self._populate_table_row(row_idx, trans)
            else:
                self.charges_table.setVisible(False)
                self.no_charges_label.setVisible(True)
        else:
            self.logger.debug("BillingTab: No current horse selected.")
            self.charges_table.setVisible(False)
            self.no_charges_label.setVisible(True)

        self.update_buttons_state()

    def _populate_table_row(self, row_idx: int, transaction: Transaction):
        if not self.charges_table:
            return

        # Helper to create table items
        def create_item(
            text: Optional[Any],
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        ) -> QTableWidgetItem:
            item = QTableWidgetItem(str(text) if text is not None else "")
            item.setTextAlignment(alignment)
            # item.setForeground(QColor(AppConfig.DARK_TEXT_PRIMARY)) # Potentially redundant due to table style
            return item

        self.charges_table.setItem(
            row_idx, self.COL_DATE_SERVICE, create_item(transaction.service_date)
        )
        self.charges_table.setItem(
            row_idx, self.COL_DATE_BILLING, create_item(transaction.billing_date)
        )

        charge_code_str = (
            transaction.charge_code.code if transaction.charge_code else "N/A"
        )
        self.charges_table.setItem(
            row_idx, self.COL_CHARGE_CODE, create_item(charge_code_str)
        )

        self.charges_table.setItem(
            row_idx, self.COL_DESCRIPTION, create_item(transaction.description)
        )

        self.charges_table.setItem(
            row_idx,
            self.COL_QTY,
            create_item(
                f"{transaction.quantity:.3f}",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            ),
        )
        self.charges_table.setItem(
            row_idx,
            self.COL_UNIT_PRICE,
            create_item(
                f"${transaction.unit_price:.2f}",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            ),
        )
        self.charges_table.setItem(
            row_idx,
            self.COL_TOTAL_AMOUNT,
            create_item(
                f"${transaction.total_amount:.2f}",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            ),
        )

        admin_by_str = (
            transaction.administered_by_user.user_id
            if transaction.administered_by_user
            else "N/A"
        )
        self.charges_table.setItem(
            row_idx, self.COL_ADMIN_BY, create_item(admin_by_str)
        )

        self.charges_table.setItem(
            row_idx, self.COL_NOTES, create_item(transaction.notes)
        )
        self.charges_table.setItem(
            row_idx,
            self.COL_INVOICE_ID,
            create_item(transaction.invoice_id or "Unbilled"),
        )

    def update_buttons_state(self):
        can_add_charge = self.current_horse is not None
        if self.add_charge_btn:
            self.add_charge_btn.setEnabled(can_add_charge)

    @Slot()
    def _launch_add_charge_dialog(self):
        if not self.current_horse:
            self.parent_view.show_warning("Add Charges", "Please select a horse first.")
            return

        self.logger.info(
            f"Launching AddChargeDialog for horse: {self.current_horse.horse_name}"
        )

        # Ensure financial_controller is available
        if not self.financial_controller:
            self.logger.error(
                "FinancialController not available to launch AddChargeDialog."
            )
            self.parent_view.show_error(
                "System Error", "Financial controller is missing."
            )
            return

        dialog = AddChargeDialog(
            parent_view=self.parent_view,  # The main window or HorseUnifiedManagement
            horse=self.current_horse,
            current_user_id=self.current_user_id,
            financial_controller=self.financial_controller,
        )
        dialog.charges_saved.connect(self._handle_charges_saved)

        dialog.exec()  # Use exec() for modal dialog

    @Slot()
    def _handle_charges_saved(self):
        self.logger.info(
            "Charges saved signal received from AddChargeDialog. Refreshing charges list."
        )
        self.load_charges_for_horse(self.current_horse)
        self.charges_updated.emit()  # Notify parent if needed

    def set_current_horse(self, horse: Optional[Horse]):
        """Called by the parent view when the selected horse changes."""
        self.load_charges_for_horse(horse)
