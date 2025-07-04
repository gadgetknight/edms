# views/horse/tabs/invoice_history_tab.py
"""
EDSI Veterinary Management System - Invoice History Tab
Version: 2.9.0
Purpose: UI for displaying and managing historical invoices for a horse's owners.
         Now correctly implements 'Sync Payments' with all necessary imports.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v2.9.0 (2025-06-28):
    - Modified `_get_payment_link_for_invoice` to check `CompanyProfile.use_stripe_payments`.
      If `False`, it will skip Stripe API calls and immediately return `None`, providing a user-configurable
      way to disable Stripe integration.
- v2.8.0 (2025-06-28):
    - Modified `populate_transactions_table` (which populates the `invoices_table`) to use
      `inv.display_invoice_id` for the "Invoice #" column.
    - Modified `populate_transactions_table` to format the "Billed To" column as
      `Farm Name (First Name Last Name) [Account Number]` (or `First Name Last Name [Account Number]`
      if no farm name) for improved clarity and consistency.
- v2.7.1 (2025-06-25):
    - **BUG FIX**: Added missing `from datetime import datetime` import statement to resolve `NameError` for `datetime` in `_sync_payment_statuses`.
- v2.7.0 (2025-06-25):
    - Added 'Sync Payments' button to action layout.
    - Implemented `_sync_payment_statuses` method to:
        - Iterate through displayed unpaid invoices.
        - Call `financial_controller.get_stripe_payment_status` for each.
        - Log the status retrieved from the backend API (local DB update to follow).
    - Updated `update_buttons_state` to enable the 'Sync Payments' button.
- v2.6.2 (2025-06-25):
    - Removed hardcoded `doctor_stripe_secret_key` from `_get_payment_link_for_invoice`.
    - Modified `_get_payment_link_for_invoice` to retrieve `DOCTOR_STRIPE_SECRET_KEY` from `AppConfig`.
- v2.6.1 (2025-06-25):
    - **BUG FIX**: Added missing `from typing import Tuple` import statement to resolve `NameError` for `Tuple` type hint.
- v2.6.0 (2025-06-25):
    - **MAJOR REFACTOR (Payment Link Workflow)**:
        - Removed the standalone 'Generate Payment Link' button from the UI.
        - Integrated Stripe Payment Link generation directly into `_email_selected_invoice` and `_print_selected_invoice` methods.
        - If a single, unpaid invoice is selected, the system now automatically generates a payment link.
        - This generated payment link URL is then passed to `InvoiceGenerator.generate_invoice_pdf` for embedding.
        - This streamlines the process, ensuring the link is on the invoice without user intervention.
    - Updated `update_buttons_state` to reflect the new workflow and button removals.
- v2.5.4 (2025-06-25):
    - **BUG FIX**: Updated `_generate_payment_link` to pass `doctor_stripe_secret_key` and `doctor_identifier`
      arguments to `financial_controller.create_stripe_payment_link`, resolving `TypeError`.
    - Added a placeholder for `doctor_stripe_secret_key` and used `self.parent_view.current_user` as `doctor_identifier`.
- v2.5.3 (2025-06-23):
    - Added 'Generate Payment Link' button to action layout.
    - Implemented `_generate_payment_link` method to call `financial_controller.create_stripe_payment_link`.
    - Added logic to enable/disable the 'Generate Payment Link' button based on invoice selection and status.
    - Included a mechanism to display the generated payment link to the user.
- v2.5.2 (2025-06-13):
    - Refactored the email invoice confirmation to use `self.parent_view.show_info`
      to ensure a consistently styled dialog is displayed, matching the
      application's theme.
- v2.5.1 (2025-06-13):
    - Fixed application closing unexpectedly after saving a PDF by re-parenting
      the QFileDialog to the main window, ensuring stability.
- v2.5.0 (2025-06-10):
    - Added "Record Payment" button and workflow.
    - Button is enabled for single, unpaid invoices.
    - Launches the new RecordPaymentDialog.
    - Added `payment_recorded` signal to notify parent view to refresh data.
- v2.4.0 (2025-06-10):
    - Fixed bug in _on_invoice_selected where details would not show.
    - Enabled batch emailing and deleting for multiple selected invoices.
- v2.3.0 (2025-06-10):
    - Enabled multi-selection (ExtendedSelection) on the main invoices table.
    - Refactored _print_selected_invoice to handle batch saving to a directory.
- v2.2.0 (2025-06-09):
    - Updated PDF save locations to use the new `AppConfig.INVOICES_DIR`.
- v2.1.0 (2025-06-09):
    - Added "Email Invoice" button and functionality.
"""
import logging
import os
import webbrowser
import urllib.parse
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QAbstractItemView,
    QTableWidgetItem,
    QLabel,
    QFileDialog,
    QMessageBox,
    QDialog,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from models import Horse, Invoice, Transaction
from controllers import FinancialController, CompanyProfileController
from reports import InvoiceGenerator
from config.app_config import AppConfig
from ..dialogs.record_payment_dialog import RecordPaymentDialog


class InvoiceHistoryTab(QWidget):
    """Tab widget for displaying and managing invoice history."""

    status_message = Signal(str)
    invoice_deleted = Signal()
    payment_recorded = Signal()

    def __init__(
        self,
        financial_controller: FinancialController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent
        self.financial_controller = financial_controller
        self.company_profile_controller = CompanyProfileController()
        self.current_horse: Optional[Horse] = None
        self.invoices: List[Invoice] = []

        self._setup_ui()
        self._setup_connections()

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
        self.record_payment_btn = self._create_action_button(
            "Record Payment", "💵", AppConfig.DARK_SUCCESS_ACTION
        )
        self.email_invoice_btn = self._create_action_button(
            "Email Selected Invoice(s)",
            "✉️",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_PRIMARY_ACTION,
        )
        self.print_invoice_btn = self._create_action_button(
            "Print Selected Invoice(s)",
            "🖨️",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_PRIMARY_ACTION,
        )
        self.delete_invoice_btn = self._create_action_button(
            "Delete Selected Invoice(s)", "🗑️", AppConfig.DARK_DANGER_ACTION
        )
        self.sync_payments_btn = self._create_action_button(
            "Sync Payments",
            "🔄",
            AppConfig.DARK_BUTTON_BG,
            AppConfig.DARK_TEXT_SECONDARY,
        )

        action_layout.addWidget(self.record_payment_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.sync_payments_btn)
        action_layout.addWidget(self.email_invoice_btn)
        action_layout.addWidget(self.print_invoice_btn)
        action_layout.addWidget(self.delete_invoice_btn)
        main_layout.addLayout(action_layout)

        main_layout.addWidget(QLabel("All Invoices for This Horse's Owners"))
        self.invoices_table = self._create_table(
            ["Invoice #", "Date", "Billed To", "Total", "Balance Due", "Status"],
            multi_select=True,
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.invoices_table)

        main_layout.addWidget(QLabel("Details for Selected Invoice"))
        self.invoice_details_table = self._create_table(
            ["Date", "Code", "Description", "Qty", "Unit Price", "Line Total"]
        )
        self.invoice_details_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        main_layout.addWidget(self.invoice_details_table)

        main_layout.setStretchFactor(self.invoices_table, 2)
        main_layout.setStretchFactor(self.invoice_details_table, 1)

        self.update_buttons_state()

    def _create_table(
        self, headers: List[str], multi_select: bool = False
    ) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        if multi_select:
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        else:
            table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        table.verticalHeader().setVisible(False)
        table.setStyleSheet(
            f"""
            QTableWidget {{
                gridline-color: {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
                padding: 5px; border: none;
                border-bottom: 1px solid {AppConfig.DARK_BORDER};
            }}
            QTableWidget::item {{ padding: 5px; }}
            QTableWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
        """
        )
        return table

    def _setup_connections(self):
        self.invoices_table.itemSelectionChanged.connect(self._on_invoice_selected)
        self.print_invoice_btn.clicked.connect(self._print_selected_invoice)
        self.email_invoice_btn.clicked.connect(self._email_selected_invoice)
        self.delete_invoice_btn.clicked.connect(self._delete_selected_invoice)
        self.record_payment_btn.clicked.connect(self._launch_record_payment_dialog)
        self.sync_payments_btn.clicked.connect(self._sync_payment_statuses)

    def set_current_horse(self, horse: Optional[Horse]):
        self.current_horse = horse
        self.load_invoices()

    def load_invoices(self):
        self.invoices_table.setRowCount(0)
        self.invoice_details_table.setRowCount(0)

        if not self.current_horse or not self.current_horse.owners:
            self.invoices = []
            self.update_buttons_state()
            return

        owner_ids = {owner.owner_id for owner in self.current_horse.owners}
        all_invoices = []
        for owner_id in owner_ids:
            owner_invoices = self.financial_controller.get_invoices_for_owner(owner_id)
            all_invoices.extend(owner_invoices)

        self.invoices = sorted(
            all_invoices, key=lambda inv: inv.invoice_date, reverse=True
        )

        for inv in self.invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)

            # MODIFIED: Format "Billed To" with Farm Name, (First Last), and [Account #]
            owner_name_parts = []
            if inv.owner:
                if inv.owner.farm_name:
                    owner_name_parts.append(inv.owner.farm_name)

                person_name_parts = []
                if inv.owner.first_name:
                    person_name_parts.append(inv.owner.first_name)
                if inv.owner.last_name:
                    person_name_parts.append(inv.owner.last_name)

                person_name_str = " ".join(person_name_parts).strip()

                if person_name_str:
                    if (
                        owner_name_parts
                    ):  # If farm name exists, append personal name in parentheses
                        owner_name_parts.append(f"({person_name_str})")
                    else:  # If no farm name, just use personal name
                        owner_name_parts.append(person_name_str)

                account_number_display = (
                    f" [{inv.owner.account_number}]"
                    if inv.owner.account_number
                    else (f" [ID:{inv.owner.owner_id}]" if inv.owner.owner_id else "")
                )

                owner_display_text = (
                    " ".join(owner_name_parts).strip() + account_number_display
                )
            else:
                owner_display_text = "N/A (Owner Missing)"

            self.invoices_table.setItem(
                row, 0, QTableWidgetItem(inv.display_invoice_id)
            )
            self.invoices_table.setItem(
                row, 1, QTableWidgetItem(inv.invoice_date.strftime("%Y-%m-%d"))
            )
            self.invoices_table.setItem(row, 2, QTableWidgetItem(owner_display_text))
            self.invoices_table.setItem(
                row, 3, QTableWidgetItem(f"${inv.grand_total:.2f}")
            )
            self.invoices_table.setItem(
                row, 4, QTableWidgetItem(f"${inv.balance_due:.2f}")
            )
            self.invoices_table.setItem(row, 5, QTableWidgetItem(inv.status))
            self.invoices_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, inv.invoice_id
            )

        self.update_buttons_state()

    def _on_invoice_selected(self):
        self.invoice_details_table.setRowCount(0)
        selected_rows = self.invoices_table.selectionModel().selectedRows()

        if len(selected_rows) == 1:
            selected_row_index = selected_rows[0].row()
            invoice_id = self.invoices_table.item(selected_row_index, 0).data(
                Qt.ItemDataRole.UserRole
            )
            transactions = self.financial_controller.get_transactions_for_invoice(
                invoice_id
            )
            for trans in transactions:
                row = self.invoice_details_table.rowCount()
                self.invoice_details_table.insertRow(row)

                self.invoice_details_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(trans.transaction_date.strftime("%Y-%m-%d")),
                )
                self.invoice_details_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        trans.charge_code.code if trans.charge_code else ""
                    ),
                )
                self.invoice_details_table.setItem(
                    row, 2, QTableWidgetItem(trans.description)
                )
                self.invoice_details_table.setItem(
                    row, 3, QTableWidgetItem(str(trans.quantity))
                )
                self.invoice_details_table.setItem(
                    row, 4, QTableWidgetItem(f"${trans.unit_price:.2f}")
                )
                self.invoice_details_table.setItem(
                    row, 5, QTableWidgetItem(f"${trans.total_price:.2f}")
                )

        self.update_buttons_state()

    def _get_selected_invoices(self) -> List[Invoice]:
        """Helper to get the full Invoice objects for all selected rows."""
        selected_invoices = []
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows:
            return []

        selected_ids = {
            self.invoices_table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            for row in selected_rows
        }

        for inv in self.invoices:
            if inv.invoice_id in selected_ids:
                selected_invoices.append(inv)
        return selected_invoices

    def _launch_record_payment_dialog(self):
        selected_invoices = self._get_selected_invoices()
        if len(selected_invoices) != 1:
            self.status_message.emit(
                "Please select a single invoice to record a payment."
            )
            return

        invoice_to_pay = selected_invoices[0]
        if invoice_to_pay.balance_due <= 0:
            self.status_message.emit("This invoice has been fully paid.")
            return

        current_user_id = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "Unknown"
        )
        dialog = RecordPaymentDialog(
            invoice=invoice_to_pay,
            financial_controller=self.financial_controller,
            current_user_id=current_user_id,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_message.emit(
                f"Payment recorded for Invoice #{invoice_to_pay.display_invoice_id}."
            )
            self.payment_recorded.emit()

    def _get_payment_link_for_invoice(self, invoice: Invoice) -> Optional[str]:
        """
        Helper to generate a Stripe Payment Link for a single, unpaid invoice.
        Retrieves the doctor's secret key from AppConfig.
        Returns the URL or None if generation fails or not applicable.
        """
        # NEW: Check if Stripe payments are enabled in Company Profile
        company_profile = self.company_profile_controller.get_company_profile()
        if not company_profile or not company_profile.use_stripe_payments:
            self.logger.info(
                "Stripe payments are disabled in Company Profile. Skipping payment link generation."
            )
            return None

        if invoice.balance_due <= 0:
            return None

        self.status_message.emit(
            f"Generating payment link for Invoice #{invoice.display_invoice_id}..."
        )

        doctor_stripe_secret_key = AppConfig.DOCTOR_STRIPE_SECRET_KEY
        if (
            not doctor_stripe_secret_key
            or doctor_stripe_secret_key == "sk_test_YOUR_DOCTOR_SECRET_KEY"
        ):
            self.parent_view.show_warning(
                "Stripe Configuration Missing",
                "Doctor's Stripe Secret Key is not configured in settings. Cannot generate payment link.",
            )
            self.logger.warning(
                "Attempted to generate payment link, but doctor's Stripe Secret Key is missing or placeholder."
            )
            return None

        doctor_identifier = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "UNKNOWN_DOCTOR"
        )

        owner_email = (
            invoice.owner.email if invoice.owner and invoice.owner.email else None
        )
        owner_name = (
            invoice.owner.farm_name
            or f"{invoice.owner.first_name} {invoice.owner.last_name}"
            if invoice.owner
            else "N/A"
        )

        success, message, payment_link_url = (
            self.financial_controller.create_stripe_payment_link(
                invoice_id=invoice.invoice_id,
                amount=invoice.balance_due,
                description=f"Payment for Invoice #{invoice.display_invoice_id} for {owner_name}",
                doctor_stripe_secret_key=doctor_stripe_secret_key,
                doctor_identifier=doctor_identifier,
                customer_email=owner_email,
            )
        )
        if success and payment_link_url:
            self.status_message.emit(
                f"Payment link generated for Invoice #{invoice.display_invoice_id}."
            )
            return payment_link_url
        else:
            self.parent_view.show_warning(
                "Payment Link Generation Failed",
                f"Could not generate payment link for Invoice #{invoice.display_invoice_id}: {message}. PDF will be generated without link.",
            )
            return None

    def _sync_payment_statuses(self):
        """
        Polls the backend API for payment statuses of all unpaid invoices and
        updates local records if payments are confirmed.
        """
        # NEW: Check if Stripe payments are enabled in Company Profile
        company_profile = self.company_profile_controller.get_company_profile()
        if not company_profile or not company_profile.use_stripe_payments:
            self.logger.info(
                "Stripe payments are disabled in Company Profile. Skipping payment sync."
            )
            self.status_message.emit(
                "Stripe payments are disabled. Cannot sync payments."
            )
            return

        unpaid_invoices = [
            inv
            for inv in self.invoices
            if inv.status == "Unpaid" and inv.balance_due > 0
        ]

        if not unpaid_invoices:
            self.status_message.emit("No unpaid invoices to sync.")
            return

        self.status_message.emit(
            f"Checking payment status for {len(unpaid_invoices)} unpaid invoices..."
        )

        doctor_identifier = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "UNKNOWN_DOCTOR"
        )

        if (
            not AppConfig.DOCTOR_STRIPE_SECRET_KEY
            or AppConfig.DOCTOR_STRIPE_SECRET_KEY == "sk_test_YOUR_DOCTOR_SECRET_KEY"
        ):
            self.parent_view.show_warning(
                "Stripe Configuration Missing",
                "Doctor's Stripe Secret Key is not configured in settings. Cannot sync payments.",
            )
            self.logger.warning(
                "Attempted to sync payments, but doctor's Stripe Secret Key is missing or placeholder."
            )
            return

        sync_count = 0
        for invoice in unpaid_invoices:
            success, is_paid, message = (
                self.financial_controller.get_stripe_payment_status(
                    doctor_identifier=doctor_identifier,
                    internal_invoice_id=invoice.invoice_id,
                )
            )

            if success:
                if is_paid:
                    # Update local database: mark as paid, record OwnerPayment, OwnerBillingHistory
                    self.logger.info(
                        f"Invoice #{invoice.display_invoice_id} confirmed paid by backend. Updating local DB."
                    )

                    # Get the actual invoice object again from DB to ensure it's "fresh" and session-attached for updates
                    # This is important before attempting to modify its status and recording payment details.
                    # We need the full invoice object, not just the one from self.invoices list
                    # as it might be detached from session
                    invoice_to_update = self.financial_controller.get_invoice_by_id(
                        invoice.invoice_id
                    )

                    if invoice_to_update:
                        payment_data = {
                            "invoice_id": invoice_to_update.invoice_id,
                            "amount": invoice_to_update.balance_due,  # Use the balance due as the amount paid for full payment
                            "payment_date": datetime.now().date(),  # Use current date as confirmation date
                            "payment_method": "Stripe (Webhook Confirmed)",
                            "reference_number": f"WEBHOOK_INV{invoice_to_update.invoice_id}",  # Reference from webhook
                            "notes": "Automatically confirmed via Stripe webhook.",
                            "user_id": "SYSTEM_SYNC",  # User ID for system-confirmed payments
                        }

                        record_success, record_msg = (
                            self.financial_controller.record_payment(payment_data)
                        )
                        if record_success:
                            sync_count += 1
                            self.status_message.emit(
                                f"Invoice #{invoice.display_invoice_id} marked as Paid in local DB."
                            )
                            self.payment_recorded.emit()  # Signal parent to refresh invoices/UI
                        else:
                            self.logger.error(
                                f"Failed to update local DB for Invoice #{invoice.display_invoice_id} after backend confirmation: {record_msg}"
                            )
                            self.parent_view.show_error(
                                "Local DB Update Failed",
                                f"Invoice #{invoice.display_invoice_id} confirmed paid, but failed to update local records: {record_msg}",
                            )
                    else:
                        self.logger.error(
                            f"Could not retrieve Invoice #{invoice.display_invoice_id} from DB for update after backend confirmation."
                        )
                        self.parent_view.show_error(
                            "Local DB Error",
                            f"Failed to retrieve Invoice #{invoice.display_invoice_id} for update.",
                        )
                else:
                    self.logger.info(
                        f"Invoice #{invoice.display_invoice_id} still unpaid according to backend."
                    )
            else:
                self.logger.error(
                    f"Failed to get status for Invoice #{invoice.display_invoice_id} from backend: {message}"
                )
                self.status_message.emit(
                    f"Error syncing Invoice #{invoice.display_invoice_id}: {message}"
                )

        if sync_count > 0:
            self.status_message.emit(
                f"Sync complete. {sync_count} invoice(s) marked as paid."
            )
            self.load_invoices()  # Reload table to show updated statuses
        else:
            self.status_message.emit("Sync complete. No new payments found.")

    def _email_selected_invoice(self):
        selected_invoices = self._get_selected_invoices()
        if not selected_invoices:
            self.status_message.emit("Please select one or more invoices to email.")
            return

        if len(selected_invoices) > 1:
            reply = self.parent_view.show_question(
                "Confirm Batch Email",
                f"This will attempt to open {len(selected_invoices)} separate draft emails. Do you want to continue?",
            )
            if not reply:
                return

        company_profile = self.company_profile_controller.get_company_profile()
        company_name = (
            company_profile.company_name if company_profile else "Your Company"
        )
        invoices_dir = AppConfig.INVOICES_DIR
        generator = InvoiceGenerator()

        for inv in selected_invoices:
            owner = inv.owner
            if not owner or not owner.email:
                self.parent_view.show_warning(
                    "Missing Information",
                    f"Invoice {inv.display_invoice_id} cannot be emailed because the owner has no email address.",
                )
                continue

            # Generate payment link for single unpaid invoice IF applicable
            payment_link_url = None
            if len(selected_invoices) == 1 and inv.balance_due > 0:
                payment_link_url = self._get_payment_link_for_invoice(inv)

            pdf_filename = f"Invoice-{inv.display_invoice_id}.pdf"
            file_path = os.path.join(invoices_dir, pdf_filename)

            try:
                success, message = generator.generate_invoice_pdf(
                    inv.invoice_id, file_path, payment_link_url
                )
                if not success:
                    self.parent_view.show_error(
                        "PDF Error",
                        f"Failed to generate PDF for {inv.display_invoice_id}:\n{message}",
                    )
                    continue
            except Exception as e:
                self.logger.error(
                    f"An unexpected error occurred during PDF generation for {inv.display_invoice_id}: {e}",
                    exc_info=True,
                )
                self.parent_view.show_error(
                    "Critical Error",
                    f"An unexpected error occurred during PDF generation for {inv.display_invoice_id}:\n{e}",
                )
                continue

            subject = f"Invoice from {company_name}"
            body = f"Dear {owner.first_name or owner.last_name},\n\nPlease find your invoice attached.\n\nThank you,\n{company_name}"
            if payment_link_url:
                body += f"\n\nTo pay online, please visit: {payment_link_url}"

            mailto_url = f"mailto:{owner.email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            webbrowser.open(mailto_url)

        self.parent_view.show_info(
            "Email Process Complete",
            f"Your email client should have opened with drafts for the selected invoices.\n\n"
            f"The invoice PDFs have been saved to the 'invoices' folder.\n\n"
            "Please attach the correct file to each email before sending.",
        )

    def _print_selected_invoice(self):
        selected_invoices = self._get_selected_invoices()
        if not selected_invoices:
            self.status_message.emit("Please select one or more invoices to print.")
            return

        if len(selected_invoices) > 1:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Select Folder to Save Invoices", AppConfig.INVOICES_DIR
            )
            if not folder_path:
                self.logger.info("Batch PDF save was cancelled by the user.")
                return

            generator = InvoiceGenerator()
            for inv in selected_invoices:
                payment_link_url = None

                pdf_filename = f"Invoice-{inv.display_invoice_id}.pdf"
                file_path = os.path.join(folder_path, pdf_filename)

                success, message = generator.generate_invoice_pdf(
                    inv.invoice_id, file_path, payment_link_url
                )
                if success:
                    self.status_message.emit(
                        f"Invoice {inv.display_invoice_id} successfully saved to:\n{file_path}"
                    )
                else:
                    self.parent_view.show_error(
                        "Error",
                        f"Failed to generate PDF for Invoice {inv.display_invoice_id}:\n{message}",
                    )

            self.parent_view.show_info(
                "Batch Print Complete",
                f"{len(selected_invoices)} invoices successfully saved to:\n{folder_path}",
            )

        else:  # Single invoice selected for print
            selected_invoice = selected_invoices[0]

            payment_link_url = None
            if selected_invoice.balance_due > 0:
                payment_link_url = self._get_payment_link_for_invoice(selected_invoice)

            default_filename = f"Invoice-{selected_invoice.display_invoice_id}.pdf"
            default_path = os.path.join(AppConfig.INVOICES_DIR, default_filename)
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent_view, "Save Invoice PDF", default_path, "PDF Files (*.pdf)"
            )
            if not file_path:
                return

            try:
                generator = InvoiceGenerator()
                success, message = generator.generate_invoice_pdf(
                    selected_invoice.invoice_id, file_path, payment_link_url
                )
                if success:
                    self.parent_view.show_info(
                        "Success", f"Report saved successfully to:\n{file_path}"
                    )
                else:
                    self.parent_view.show_error(
                        "Error", f"Failed to generate PDF:\n{message}"
                    )
            except Exception as e:
                self.logger.error(
                    f"An unexpected error occurred during PDF generation: {e}",
                    exc_info=True,
                )
                self.parent_view.show_error(
                    "Critical Error", f"An unexpected error occurred:\n{e}"
                )

    def _delete_selected_invoice(self):
        selected_invoices = self._get_selected_invoices()
        if not selected_invoices:
            self.status_message.emit("Please select one or more invoices to delete.")
            return

        invoice_list_str = "\n - ".join(
            [f"{inv.display_invoice_id}" for inv in selected_invoices]
        )
        warning_message = (
            f"Are you sure you want to permanently delete the following {len(selected_invoices)} invoice(s)?\n\n- {invoice_list_str}\n\n"
            "This will adjust each owner's balance accordingly.\n\n"
            "<b>IMPORTANT:</b> This action will NOT make the original charges billable again. "
            "This action cannot be undone."
        )

        if self.parent_view.show_question("Confirm Delete Invoice(s)", warning_message):
            current_user_id = (
                self.parent_view.current_user
                if hasattr(self.parent_view, "current_user")
                else "Unknown"
            )
            success_count = 0
            for inv in selected_invoices:
                success, message = self.financial_controller.delete_invoice(
                    inv.invoice_id, current_user_id
                )
                if success:
                    success_count += 1
                else:
                    self.parent_view.show_error(
                        f"Deletion Failed for {inv.display_invoice_id}", message
                    )

            if success_count > 0:
                self.status_message.emit(
                    f"Successfully deleted {success_count} invoice(s)."
                )
                self.invoice_deleted.emit()

    def update_buttons_state(self):
        selection_count = len(self.invoices_table.selectionModel().selectedRows())

        self.print_invoice_btn.setEnabled(selection_count > 0)
        self.email_invoice_btn.setEnabled(selection_count > 0)
        self.delete_invoice_btn.setEnabled(selection_count > 0)

        has_unpaid_invoices_in_list = any(
            inv.status == "Unpaid" and inv.balance_due > 0 for inv in self.invoices
        )
        self.sync_payments_btn.setEnabled(has_unpaid_invoices_in_list)

        has_single_unpaid_selection = False
        if selection_count == 1:
            selected_invoice = self._get_selected_invoices()[0]
            if selected_invoice.balance_due > 0:
                has_single_unpaid_selection = True

        self.record_payment_btn.setEnabled(has_single_unpaid_selection)
