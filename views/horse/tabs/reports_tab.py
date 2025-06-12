# views/horse/tabs/reports_tab.py
"""
EDSI Veterinary Management System - Reports Tab
Version: 1.6.0
Purpose: A UI tab to serve as a hub for selecting and running reports.
Last Updated: June 11, 2025
Author: Gemini

Changelog:
- v1.6.0 (2025-06-11):
    - Implemented the `_run_payment_history_report` method to connect the UI
      to the controller and PDF generator.
- v1.5.1 (2025-06-11):
    - Added and integrated the PaymentHistoryOptionsWidget.
"""

import logging
import os
import webbrowser
import urllib.parse
from typing import Optional, Dict
from datetime import date

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QStackedWidget,
    QLabel,
    QPushButton,
    QFrame,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from config.app_config import AppConfig
from controllers import ReportsController
from reports import (
    OwnerStatementGenerator,
    ARAgingGenerator,
    InvoiceRegisterGenerator,
    PaymentHistoryGenerator,
)
from views.reports.options import (
    OwnerStatementOptionsWidget,
    ARAgingOptionsWidget,
    InvoiceRegisterOptionsWidget,
    PaymentHistoryOptionsWidget,
)
from models import Owner


class ReportsTab(QWidget):
    """A tab for selecting and running all system reports."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reports_controller = ReportsController()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        left_panel = QFrame()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        report_list_label = QLabel("Available Reports")
        report_list_label.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        report_list_label.setStyleSheet(f"color: {AppConfig.DARK_TEXT_SECONDARY};")
        self.report_list_widget = QListWidget()
        self.report_list_widget.setStyleSheet(
            f"""
            QListWidget {{ border: 1px solid {AppConfig.DARK_BORDER}; background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; }}
            QListWidget::item {{ padding: 12px; }}
            QListWidget::item:selected {{ background-color: {AppConfig.DARK_PRIMARY_ACTION}; color: {AppConfig.DARK_HIGHLIGHT_TEXT}; border: none; }}
            """
        )
        self.populate_report_list()
        left_layout.addWidget(report_list_label)
        left_layout.addWidget(self.report_list_widget, 1)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        self.options_stack = QStackedWidget()
        right_layout.addWidget(self.options_stack, 1)
        self.placeholder_widget = QLabel(
            "Select a report from the list to configure its options."
        )
        self.placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_widget.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY};"
        )
        self.owner_statement_options = OwnerStatementOptionsWidget()
        self.ar_aging_options = ARAgingOptionsWidget()
        self.invoice_register_options = InvoiceRegisterOptionsWidget()
        self.payment_history_options = PaymentHistoryOptionsWidget()
        self.options_stack.addWidget(self.placeholder_widget)
        self.options_stack.addWidget(self.owner_statement_options)
        self.options_stack.addWidget(self.ar_aging_options)
        self.options_stack.addWidget(self.invoice_register_options)
        self.options_stack.addWidget(self.payment_history_options)
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.email_report_button = QPushButton("Generate & Email")
        self.email_report_button.setEnabled(False)
        self.email_report_button.setMinimumHeight(36)
        self.run_report_button = QPushButton("Generate Report")
        self.run_report_button.setEnabled(False)
        self.run_report_button.setMinimumHeight(36)
        action_layout.addWidget(self.email_report_button)
        action_layout.addWidget(self.run_report_button)
        right_layout.addLayout(action_layout)
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        self._apply_button_styles()

    def _apply_button_styles(self):
        self.run_report_button.setStyleSheet(
            f"""
            QPushButton {{ background-color: {AppConfig.DARK_SUCCESS_ACTION}; color: white; border: none; border-radius: 4px; padding: 8px 24px; font-weight: bold; }}
            QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; }}
        """
        )
        self.email_report_button.setStyleSheet(
            f"""
            QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_PRIMARY_ACTION}; border-radius: 4px; padding: 8px 24px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
            QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; border: 1px solid {AppConfig.DARK_HEADER_FOOTER};}}
        """
        )

    def setup_connections(self):
        self.report_list_widget.currentItemChanged.connect(
            self._on_report_selection_changed
        )
        self.run_report_button.clicked.connect(self._on_run_report_clicked)
        self.email_report_button.clicked.connect(self._on_email_report_clicked)

    def populate_report_list(self):
        reports = [
            "Owner Statement",
            "A/R Aging",
            "Invoice Register",
            "Payment History",
            "Charge Code Usage",
            "Horse Transaction History",
        ]
        for report_name in reports:
            self.report_list_widget.addItem(QListWidgetItem(report_name))

    def _on_report_selection_changed(
        self, current: QListWidgetItem, previous: QListWidgetItem
    ):
        self.run_report_button.setEnabled(bool(current))
        self.email_report_button.setEnabled(bool(current))
        if not current:
            self.options_stack.setCurrentWidget(self.placeholder_widget)
            return
        report_name = current.text()
        if report_name == "Owner Statement":
            self.options_stack.setCurrentWidget(self.owner_statement_options)
        elif report_name == "A/R Aging":
            self.options_stack.setCurrentWidget(self.ar_aging_options)
            self.email_report_button.setEnabled(False)
        elif report_name == "Invoice Register":
            self.options_stack.setCurrentWidget(self.invoice_register_options)
            self.email_report_button.setEnabled(False)
        elif report_name == "Payment History":
            self.options_stack.setCurrentWidget(self.payment_history_options)
            self.email_report_button.setEnabled(False)
        else:
            self.options_stack.setCurrentWidget(self.placeholder_widget)
            self.run_report_button.setEnabled(False)
            self.email_report_button.setEnabled(False)

    def _on_run_report_clicked(self):
        current_item = self.report_list_widget.currentItem()
        if not current_item:
            return
        report_name = current_item.text()
        if report_name == "Owner Statement":
            self._run_owner_statement_report(False)
        elif report_name == "A/R Aging":
            self._run_ar_aging_report()
        elif report_name == "Invoice Register":
            self._run_invoice_register_report()
        elif report_name == "Payment History":
            self._run_payment_history_report()
        else:
            QMessageBox.information(
                self,
                "Not Implemented",
                f"The '{report_name}' report has not been implemented yet.",
            )

    def _on_email_report_clicked(self):
        current_item = self.report_list_widget.currentItem()
        if not current_item:
            return
        if current_item.text() == "Owner Statement":
            self._run_owner_statement_report(True)
        else:
            QMessageBox.information(
                self,
                "Not Implemented",
                "Emailing is not available for this report type.",
            )

    def _run_payment_history_report(self):
        """Orchestrates the generation of the Payment History report."""
        options = self.payment_history_options.get_options()
        self.logger.info(
            f"Generating Payment History from {options['start_date']} to {options['end_date']} for owner: {options['owner_id']}"
        )
        report_data = self.reports_controller.get_payment_history_data(**options)
        if not report_data or not report_data.get("payments"):
            QMessageBox.information(
                self, "No Data", "No payments found for the selected criteria."
            )
            return
        default_filename = f"Payment_History_{date.today()}.pdf"
        default_path = os.path.join(AppConfig.PROJECT_ROOT, default_filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Payment History Report", default_path, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        try:
            generator = PaymentHistoryGenerator()
            success, message = generator.generate_pdf(report_data, file_path)
            if success:
                QMessageBox.information(
                    self, "Success", f"Report saved successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "PDF Generation Failed", message)
        except Exception as e:
            self.logger.error(
                f"Failed to run Payment History generator: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def _run_invoice_register_report(self):
        options = self.invoice_register_options.get_options()
        self.logger.info(
            f"Generating Invoice Register from {options['start_date']} to {options['end_date']}"
        )
        report_data = self.reports_controller.get_invoice_register_data(
            options["start_date"], options["end_date"]
        )
        if not report_data or not report_data.get("invoices"):
            QMessageBox.information(
                self, "No Data", "No invoices found in the selected date range."
            )
            return
        default_filename = f"Invoice_Register_{date.today()}.pdf"
        default_path = os.path.join(AppConfig.PROJECT_ROOT, default_filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Invoice Register", default_path, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        try:
            generator = InvoiceRegisterGenerator()
            success, message = generator.generate_pdf(report_data, file_path)
            if success:
                QMessageBox.information(
                    self, "Success", f"Report saved successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "PDF Generation Failed", message)
        except Exception as e:
            self.logger.error(
                f"Failed to run Invoice Register generator: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def _run_ar_aging_report(self):
        options = self.ar_aging_options.get_options()
        as_of_date = options["as_of_date"]
        self.logger.info(f"Generating A/R Aging report for date: {as_of_date}")
        report_data = self.reports_controller.get_ar_aging_data(as_of_date)
        if not report_data or not report_data.get("lines"):
            QMessageBox.information(
                self, "No Data", "No outstanding balances found for the selected date."
            )
            return
        default_filename = f"AR_Aging_Report_{date.today()}.pdf"
        default_path = os.path.join(AppConfig.PROJECT_ROOT, default_filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save A/R Aging Report", default_path, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        try:
            generator = ARAgingGenerator()
            success, message = generator.generate_pdf(report_data, file_path)
            if success:
                QMessageBox.information(
                    self, "Success", f"Report saved successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "PDF Generation Failed", message)
        except Exception as e:
            self.logger.error(f"Failed to run A/R Aging generator: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def _run_owner_statement_report(self, email_after: bool):
        options = self.owner_statement_options.get_options()
        owner_id = options.get("owner_id")
        if email_after and owner_id == "all":
            QMessageBox.warning(
                self,
                "Batch Email Not Supported",
                "Emailing is only available when a single owner is selected.",
            )
            return
        if owner_id == "all":
            self._generate_batch_statements(options["start_date"], options["end_date"])
        elif owner_id is not None:
            self._generate_single_statement(owner_id, options, email_after)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select an owner.")

    def _generate_batch_statements(self, start_date: date, end_date: date):
        self.logger.info(
            f"Generating batch owner statements from {start_date} to {end_date}"
        )
        all_data = self.reports_controller.get_data_for_all_owner_statements(
            start_date, end_date
        )
        if not all_data:
            QMessageBox.information(
                self,
                "No Statements",
                "No owners found with a balance or activity in the selected period.",
            )
            return
        save_dir = QFileDialog.getExistingDirectory(
            self, "Select Directory to Save Statements", AppConfig.PROJECT_ROOT
        )
        if not save_dir:
            return
        generator = OwnerStatementGenerator()
        success_count, fail_count = 0, 0
        for data in all_data:
            owner_name = data["owner"].last_name or f"Owner{data['owner'].owner_id}"
            file_path = os.path.join(
                save_dir, f"Statement for {owner_name} {date.today()}.pdf"
            )
            success, _ = generator.generate_statement_pdf(data, file_path)
            if success:
                success_count += 1
            else:
                fail_count += 1
        summary_message = f"Successfully generated {success_count} statements."
        if fail_count > 0:
            summary_message += (
                f"\nFailed to generate {fail_count} statements. Please check the logs."
            )
        QMessageBox.information(self, "Batch Generation Complete", summary_message)

    def _generate_single_statement(
        self, owner_id: int, options: Dict, email_after: bool
    ):
        self.logger.info(f"Generating owner statement for owner_id: {owner_id}")
        report_data = self.reports_controller.get_owner_statement_data(
            owner_id=owner_id,
            start_date=options["start_date"],
            end_date=options["end_date"],
        )
        if not report_data:
            QMessageBox.critical(self, "Error", "Could not fetch data for the report.")
            return
        owner_name = report_data["owner"].last_name or f"Owner{owner_id}"
        default_filename = f"Statement for {owner_name} {date.today()}.pdf"
        save_dir = AppConfig.INVOICES_DIR if email_after else AppConfig.PROJECT_ROOT
        default_path = os.path.join(save_dir, default_filename)
        file_path = (
            default_path
            if email_after
            else QFileDialog.getSaveFileName(
                self, "Save Owner Statement", default_path, "PDF Files (*.pdf)"
            )[0]
        )
        if not file_path:
            return
        try:
            generator = OwnerStatementGenerator()
            success, message = generator.generate_statement_pdf(report_data, file_path)
            if success:
                if email_after:
                    self._dispatch_email(report_data["owner"], file_path)
                else:
                    QMessageBox.information(
                        self, "Success", f"Report saved successfully to:\n{file_path}"
                    )
            else:
                QMessageBox.critical(self, "PDF Generation Failed", message)
        except Exception as e:
            self.logger.error(
                f"Failed to instantiate or run PDF generator: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def _dispatch_email(self, owner: Owner, attachment_path: str):
        if not owner.email:
            QMessageBox.warning(
                self,
                "Cannot Email",
                f"Owner '{owner.last_name}' does not have an email address on file.",
            )
            return
        company_name = (
            self.reports_controller.company_profile.company_name
            if self.reports_controller.company_profile
            else "Your Clinic"
        )
        subject = f"Your Statement from {company_name}"
        body = (
            f"Dear {owner.first_name or owner.last_name},\n\n"
            f"Please find your statement attached.\n\n"
            f"Thank you,\n{company_name}"
        )
        mailto_url = f"mailto:{owner.email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        try:
            webbrowser.open(mailto_url)
            QMessageBox.information(
                self,
                "Email Draft Created",
                f"Your email client should now be open.\n\nPlease manually attach the following file before sending:\n{attachment_path}",
            )
        except Exception as e:
            self.logger.error(f"Could not open mail client: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Email Error",
                "Could not open your default email client. The PDF has been saved for you to attach manually.",
            )
