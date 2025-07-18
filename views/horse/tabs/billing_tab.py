# views/horse/tabs/billing_tab.py
"""
EDSI Veterinary Management System - Horse Billing Tab
Version: 1.9.0
Purpose: UI for displaying and managing billing charges for a specific horse.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.9.0 (2025-06-09):
    - Added invoice_created signal to notify parent views when an invoice
      has been successfully generated, allowing other UI components to refresh.
- v1.8.0 (2025-06-09):
    - Updated `load_transactions` to use the refactored `get_transactions_for_horse`
      controller method that now filters by status instead of an 'invoiced' flag.
- v1.7.0 (2025-06-09):
    - Refactored `_create_invoice` to call `generate_invoices_from_transactions`.
"""

import logging
from typing import Optional, List

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
    QApplication,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QColor

from models import Horse, Transaction
from controllers import FinancialController
from ..dialogs.add_charge_dialog import AddChargeDialog
from ..dialogs.edit_charge_dialog import EditChargeDialog
from ..dialogs.edit_all_charges_dialog import EditAllChargesDialog
from config.app_config import AppConfig


class BillingTab(QWidget):
    status_message = Signal(str)
    invoice_created = Signal()

    def __init__(
        self,
        financial_controller: FinancialController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent
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
        self.edit_all_btn = self._create_action_button(
            "Edit All", "✏️", AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
        )
        self.delete_charge_btn = self._create_action_button(
            "Delete Selected",
            "➖",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_DANGER_ACTION,
        )
        self.create_invoice_btn = self._create_action_button(
            "Create Invoice", "📄", AppConfig.DARK_PRIMARY_ACTION
        )

        action_layout.addWidget(self.add_charge_btn)
        action_layout.addWidget(self.edit_charge_btn)
        action_layout.addWidget(self.edit_all_btn)
        action_layout.addWidget(self.delete_charge_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.create_invoice_btn)
        main_layout.addLayout(action_layout)

        self.title_label = QLabel("Un-invoiced Charges")
        font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-top: 10px;"
        )
        main_layout.addWidget(self.title_label)

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels(
            ["ID", "Code", "Alt. Code", "Description", "Qty", "Unit Price", "Total"]
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
            3, QHeaderView.ResizeMode.Stretch
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
            QTableWidget::item {{ padding: 5px; }}
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
        self.add_charge_btn.clicked.connect(self._launch_add_charge_dialog)
        self.edit_charge_btn.clicked.connect(self._edit_selected_charge)
        self.edit_all_btn.clicked.connect(self._launch_edit_all_charges_dialog)
        self.delete_charge_btn.clicked.connect(self._delete_selected_charge)
        self.create_invoice_btn.clicked.connect(self._create_invoice)
        self.transactions_table.itemSelectionChanged.connect(self.update_buttons_state)
        self.transactions_table.cellDoubleClicked.connect(self._edit_selected_charge)

    def set_current_horse(self, horse: Optional[Horse]):
        self.current_horse = horse
        self.load_transactions()
        self.update_buttons_state()

    def load_transactions(self):
        if not self.current_horse:
            self.clear_display()
            return
        self.transactions = self.financial_controller.get_transactions_for_horse(
            self.current_horse.horse_id
        )
        self.populate_transactions_table()

    def populate_transactions_table(self):
        self.transactions_table.setRowCount(0)
        if self.transactions:
            self.transactions_table.setRowCount(len(self.transactions))
            for row, trans in enumerate(self.transactions):
                trans_id = trans.transaction_id
                id_item = QTableWidgetItem(str(trans_id))
                id_item.setData(Qt.ItemDataRole.UserRole, trans_id)
                self.transactions_table.setItem(row, 0, id_item)

                code = trans.charge_code.code if trans.charge_code else "N/A"
                alt_code = (
                    trans.charge_code.alternate_code if trans.charge_code else "N/A"
                )

                self.transactions_table.setItem(row, 1, QTableWidgetItem(code))
                self.transactions_table.setItem(row, 2, QTableWidgetItem(alt_code))
                self.transactions_table.setItem(
                    row, 3, QTableWidgetItem(trans.description)
                )
                self.transactions_table.setItem(
                    row, 4, QTableWidgetItem(str(trans.quantity))
                )
                self.transactions_table.setItem(
                    row, 5, QTableWidgetItem(f"{trans.unit_price:.2f}")
                )
                self.transactions_table.setItem(
                    row, 6, QTableWidgetItem(f"{trans.total_price:.2f}")
                )
        self._update_total_due_display()
        self.update_buttons_state()

    def clear_display(self):
        self.transactions_table.setRowCount(0)
        self.transactions = []
        self.current_horse = None
        self.update_buttons_state()
        self._update_total_due_display()

    def update_buttons_state(self):
        has_horse = self.current_horse is not None
        has_transactions = len(self.transactions) > 0
        has_selection = (
            has_transactions and len(self.transactions_table.selectedItems()) > 0
        )

        self.add_charge_btn.setEnabled(has_horse)
        self.edit_charge_btn.setEnabled(has_selection)
        self.edit_all_btn.setEnabled(has_transactions)
        self.delete_charge_btn.setEnabled(has_selection)
        self.create_invoice_btn.setEnabled(has_transactions)

    def _update_total_due_display(self):
        total_due = sum(
            trans.total_price
            for trans in self.transactions
            if trans and hasattr(trans, "total_price")
        )
        self.total_due_label.setText(f"${total_due:.2f}")

    def _create_invoice(self):
        """Handler for the 'Create Invoice' button."""
        if not self.current_horse or not self.transactions:
            self.status_message.emit("No charges available to create an invoice.")
            return

        transaction_ids = [t.transaction_id for t in self.transactions]
        total_due = sum(t.total_price for t in self.transactions)

        current_user_id = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "Unknown"
        )
        owner_count = len(self.current_horse.owner_associations)

        confirmation_message = (
            f"This will generate {owner_count} separate invoice(s) for all owners of {self.current_horse.horse_name}, "
            f"splitting a total of ${total_due:.2f} based on their ownership percentage.\n\nProceed?"
        )

        if self.parent_view.show_question(
            "Confirm Invoice Generation", confirmation_message
        ):
            success, message, new_invoices = (
                self.financial_controller.generate_invoices_from_transactions(
                    source_transaction_ids=transaction_ids,
                    current_user_id=current_user_id,
                )
            )
            if success:
                self.status_message.emit(message)
                self.load_transactions()
                self.invoice_created.emit()
            else:
                self.parent_view.show_error("Invoice Creation Failed", message)

    def _launch_add_charge_dialog(self):
        if not self.current_horse:
            return
        dialog = AddChargeDialog(self.current_horse, self.financial_controller, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_message.emit(
                f"New charges added for {self.current_horse.horse_name}."
            )
            self.load_transactions()

    def _launch_edit_all_charges_dialog(self):
        if not self.current_horse or not self.transactions:
            return
        dialog = EditAllChargesDialog(
            self.current_horse, self.transactions, self.financial_controller, self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_message.emit(
                f"Charges updated for {self.current_horse.horse_name}."
            )
            self.load_transactions()

    @Slot(int, int)
    def _edit_selected_charge(self, row=None, column=None):
        selected_items = self.transactions_table.selectedItems()
        if not selected_items:
            return

        selected_row = selected_items[0].row()
        transaction_id = self.transactions_table.item(selected_row, 0).data(
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
        selected_items = self.transactions_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        transaction_id = self.transactions_table.item(row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        description = self.transactions_table.item(row, 3).text()

        if self.parent_view and hasattr(self.parent_view, "show_question"):
            reply_is_yes = self.parent_view.show_question(
                "Confirm Delete",
                f"Are you sure you want to delete this charge?\n\n- {description}",
            )
        else:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete this charge?\n\n- {description}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            reply_is_yes = reply == QMessageBox.StandardButton.Yes

        if reply_is_yes:
            success, message = self.financial_controller.delete_charge_transaction(
                transaction_id
            )
            if success:
                self.status_message.emit(message)
                self.load_transactions()
            else:
                QMessageBox.critical(self, "Error", message)
