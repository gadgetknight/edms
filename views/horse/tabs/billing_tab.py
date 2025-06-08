# views/horse/tabs/billing_tab.py
"""
EDSI Veterinary Management System - Horse Billing Tab
Version: 1.2.2
Purpose: UI for displaying and managing billing charges for a specific horse.
         - Corrected module imports to be relative to fix an ImportError.
Last Updated: June 7, 2025
Author: Gemini

Changelog:
- v1.2.2 (2025-06-07):
    - Bug Fix: Changed dialog imports to be relative (e.g., `..dialogs`) to resolve an `ImportError` during application startup.
    - Refactor: Improved robustness of `_update_total_due_display` to calculate totals from the underlying data model instead of UI text.
- v1.2.1 (2025-06-07):
    - Removed inline source citation markers from the code.
- v1.2.0 (2025-06-07):
    - Restyled action buttons for "Add", "Edit", and "Delete" to match new UI specification.
    - Added prominent title for the transactions table.
    - Implemented blue row highlighting for selected items in the transactions table.
    - Ensured "Total Due" summary is correctly positioned and styled.
- v1.1.5 (2025-06-06):
    - Bug Fix: Ensured the `self.transactions` attribute is always initialized
      as a list in both `__init__` and `clear_display` to prevent a TypeError.
- v1.1.4 (2025-06-06):
    - Bug Fix: Corrected attribute access for horse location and birth date.
- v1.1.3 (2025-06-06):
    - Bug Fix: Added `QColor` to the `PySide6.QtGui` import list.
- v1.1.2 (2025-06-06):
    - Bug Fix: Corrected the column count and headers in the transactions table.
- v1.1.1 (2025-06-06):
    - Bug Fix: Corrected attribute access for administered_by user.
- v1.1.0 (2025-06-06):
    - Major UI Overhaul and implementation of edit/delete functionality.
"""

import logging
from typing import Optional, List
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QAbstractItemView,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QToolButton,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QColor

from models import Horse, Transaction
from controllers import FinancialController
from ..dialogs.add_charge_dialog import AddChargeDialog
from ..dialogs.edit_charge_dialog import EditChargeDialog
from config.app_config import AppConfig


class BillingTab(QWidget):
    status_message = Signal(str)

    def __init__(
        self,
        financial_controller: FinancialController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.financial_controller = financial_controller
        self.current_horse: Optional[Horse] = None
        self.transactions: List[Transaction] = []

        self._setup_ui()
        self._setup_connections()
        self.clear_display()

    def _create_action_button(
        self,
        text: str,
        icon_char: str,
        base_color: str,
        border_color: Optional[str] = None,
    ) -> QPushButton:
        """Helper to create styled QPushButtons for the action bar."""
        button = QPushButton(f" {icon_char}  {text}")
        font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 10)
        font.setBold(True)
        button.setFont(font)
        button.setMinimumHeight(36)

        border_style = (
            f"border: 1px solid {border_color};" if border_color else "border: none;"
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                text-align: center;
                {border_style}
            }}
            QPushButton:disabled {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_TERTIARY};
                border: 1px solid {AppConfig.DARK_TEXT_TERTIARY};
            }}
            QPushButton:hover {{
                background-color: {QColor(base_color).lighter(115).name()};
            }}
        """
        )
        return button

    def _setup_ui(self):
        """Initialize the UI components of the tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.add_charge_btn = self._create_action_button(
            "Add New Charges", "➕", AppConfig.DARK_SUCCESS_ACTION
        )
        self.edit_charge_btn = self._create_action_button(
            "Edit Selected",
            "✏️",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_PRIMARY_ACTION,
        )
        self.delete_charge_btn = self._create_action_button(
            "Delete Selected",
            "➖",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_DANGER_ACTION,
        )

        action_layout.addWidget(self.add_charge_btn)
        action_layout.addWidget(self.edit_charge_btn)
        action_layout.addWidget(self.delete_charge_btn)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.title_label = QLabel("Un-invoiced Charges")
        font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-top: 10px;"
        )
        main_layout.addWidget(self.title_label)

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Service Date",
                "Description",
                "Qty",
                "Unit Price",
                "Total",
                "Notes",
                "Administered By",
            ]
        )
        self.transactions_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.transactions_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.transactions_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.transactions_table.setColumnHidden(0, True)
        self.transactions_table.setStyleSheet(
            f"""
            QTableWidget {{
                gridline-color: {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {AppConfig.DARK_BORDER};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
        """
        )
        main_layout.addWidget(self.transactions_table)

        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_due_title_label = QLabel("Total Due:")
        font.setPointSize(14)
        total_due_title_label.setFont(font)
        self.total_due_label = QLabel("$0.00")
        self.total_due_label.setFont(font)
        self.total_due_label.setStyleSheet("color: white;")

        total_layout.addWidget(total_due_title_label)
        total_layout.addWidget(self.total_due_label)
        main_layout.addLayout(total_layout)

    def _setup_connections(self):
        """Set up signal-slot connections."""
        self.add_charge_btn.clicked.connect(self._launch_add_charge_dialog)
        self.edit_charge_btn.clicked.connect(self._edit_selected_charge)
        self.delete_charge_btn.clicked.connect(self._delete_selected_charge)
        self.transactions_table.itemSelectionChanged.connect(self.update_buttons_state)

    def set_current_horse(self, horse: Optional[Horse]):
        """Set the currently displayed horse and update the view."""
        self.current_horse = horse
        self.load_transactions()
        self.update_buttons_state()

    def load_transactions(self):
        """Load and display transactions for the current horse."""
        if not self.current_horse:
            self.clear_display()
            return

        self.transactions = self.financial_controller.get_transactions_for_horse(
            self.current_horse.horse_id, invoiced=False
        )
        self.populate_transactions_table()

    def populate_transactions_table(self):
        """Fills the transactions table with data."""
        self.transactions_table.setRowCount(0)

        if self.transactions:
            self.transactions_table.setRowCount(len(self.transactions))
            for row, trans in enumerate(self.transactions):
                trans_id = trans.transaction_id
                id_item = QTableWidgetItem(str(trans_id))
                id_item.setData(Qt.ItemDataRole.UserRole, trans_id)
                self.transactions_table.setItem(row, 0, id_item)

                self.transactions_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(trans.transaction_date.strftime("%Y-%m-%d")),
                )
                self.transactions_table.setItem(
                    row, 2, QTableWidgetItem(trans.description)
                )
                self.transactions_table.setItem(
                    row, 3, QTableWidgetItem(str(trans.quantity))
                )
                self.transactions_table.setItem(
                    row, 4, QTableWidgetItem(f"{trans.unit_price:.2f}")
                )
                self.transactions_table.setItem(
                    row, 5, QTableWidgetItem(f"{trans.total_price:.2f}")
                )
                self.transactions_table.setItem(
                    row, 6, QTableWidgetItem(trans.item_notes or "")
                )

                admin_name = (
                    trans.administered_by.user_name if trans.administered_by else "N/A"
                )
                self.transactions_table.setItem(row, 7, QTableWidgetItem(admin_name))

        self._update_total_due_display()

    def clear_display(self):
        """Clears all displayed data from the tab."""
        self.transactions_table.setRowCount(0)
        self.transactions = []
        self.current_horse = None
        self.update_buttons_state()
        self._update_total_due_display()

    def update_buttons_state(self):
        """Enables or disables buttons based on current state."""
        has_horse = self.current_horse is not None
        has_selection = has_horse and len(self.transactions_table.selectedItems()) > 0

        has_items_to_invoice = has_horse and (
            isinstance(self.transactions, list) and len(self.transactions) > 0
        )

        self.add_charge_btn.setEnabled(has_horse)
        self.edit_charge_btn.setEnabled(has_selection)
        self.delete_charge_btn.setEnabled(has_selection)

    def _update_total_due_display(self):
        """Calculates and updates the total due display from the data model."""
        total_due = sum(
            trans.total_price
            for trans in self.transactions
            if trans and hasattr(trans, "total_price")
        )
        self.total_due_label.setText(f"${total_due:.2f}")

    def _launch_add_charge_dialog(self):
        """Opens the dialog to add new charges."""
        if not self.current_horse:
            QMessageBox.warning(
                self,
                "No Horse Selected",
                "Please select a horse before adding charges.",
            )
            return

        self.logger.info(
            f"Launching AddChargeDialog for horse: {self.current_horse.horse_name}"
        )
        dialog = AddChargeDialog(
            horse=self.current_horse,
            financial_controller=self.financial_controller,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_message.emit(
                f"New charges added for {self.current_horse.horse_name}."
            )
            self.load_transactions()

    def _edit_selected_charge(self):
        """Opens the EditChargeDialog for the selected transaction."""
        selected_items = self.transactions_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        transaction_id = self.transactions_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )

        transaction_to_edit = self.financial_controller.get_transaction_by_id(
            transaction_id
        )
        if not transaction_to_edit:
            QMessageBox.critical(
                self, "Error", "Could not find the selected transaction to edit."
            )
            return

        dialog = EditChargeDialog(
            transaction=transaction_to_edit,
            financial_controller=self.financial_controller,
            current_user_id=QApplication.instance().current_user_id,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_message.emit("Charge updated successfully.")
            self.load_transactions()

    def _delete_selected_charge(self):
        """Deletes the selected transaction after confirmation."""
        selected_items = self.transactions_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        transaction_id = self.transactions_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        description = self.transactions_table.item(row, 2).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this charge?\n\n- {description}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.financial_controller.delete_charge_transaction(
                transaction_id
            )
            if success:
                self.status_message.emit(message)
                self.load_transactions()
            else:
                QMessageBox.critical(self, "Error", message)
