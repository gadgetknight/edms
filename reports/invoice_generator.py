# reports/invoice_generator.py
"""
EDSI Veterinary Management System - Invoice PDF Generator
Version: 1.0.1
Purpose: Generates a professional PDF invoice for a given invoice record.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-06-09):
    - Bug Fix: Added `Tuple` to the import from the `typing` module to resolve a NameError.
- v1.0.0 (2025-06-09):
    - Initial creation of the invoice PDF generator.
"""
import logging
from typing import Optional, Tuple
from decimal import Decimal

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

from models import Invoice
from controllers import FinancialController, CompanyProfileController, OwnerController


class InvoiceGenerator:
    """Generates a PDF invoice for a given invoice ID."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.financial_controller = FinancialController()
        self.company_profile_controller = CompanyProfileController()
        self.owner_controller = OwnerController()

        # Setup styles
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name="Right", alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER))

    def generate_invoice_pdf(self, invoice_id: int, file_path: str) -> Tuple[bool, str]:
        """
        Fetches all data for an invoice and generates a PDF at the specified path.
        """
        try:
            # --- 1. Fetch Data ---
            invoice = self.financial_controller.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, f"Invoice ID {invoice_id} not found."

            company_profile = self.company_profile_controller.get_company_profile()
            if not company_profile:
                return False, "Company Profile is not set up."

            owner = self.owner_controller.get_owner_by_id(invoice.owner_id)
            if not owner:
                return False, f"Owner with ID {invoice.owner_id} not found."

            transactions = self.financial_controller.get_transactions_for_invoice(
                invoice_id
            )

            # --- 2. Build PDF ---
            doc = SimpleDocTemplate(
                file_path, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18
            )
            story = []

            # --- Header ---
            story.append(self._create_header(company_profile))
            story.append(Spacer(1, 0.25 * inch))

            # --- Bill To & Statement Info ---
            story.append(self._create_info_tables(owner, invoice))
            story.append(Spacer(1, 0.25 * inch))

            # --- Line Items Table ---
            story.append(self._create_transactions_table(transactions))
            story.append(Spacer(1, 0.2 * inch))

            # --- Financial Summary ---
            story.append(self._create_summary_table(invoice))

            # --- Footer Notes ---
            story.append(Spacer(1, 0.4 * inch))
            story.append(self._create_footer_notes())

            doc.build(story)
            self.logger.info(
                f"Successfully generated PDF for Invoice #{invoice_id} at {file_path}"
            )
            return True, "PDF generated successfully."

        except Exception as e:
            self.logger.error(
                f"Failed to generate PDF for Invoice #{invoice_id}: {e}", exc_info=True
            )
            return False, f"An unexpected error occurred: {e}"

    def _create_header(self, profile) -> Table:
        header_text = f"""
            <font size=18>{profile.company_name or 'Your Company Name'}</font><br/>
            <font size=10>{profile.address_line1 or ''}<br/>
            {profile.address_line2 or ''}<br/>
            {profile.city or ''}, {profile.state or ''} {profile.zip_code or ''}<br/>
            Phone: {profile.phone or ''} | Email: {profile.email or ''}</font>
        """
        header_paragraph = Paragraph(header_text, self.styles["Normal"])

        header_table = Table([[header_paragraph]], colWidths=[4.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("VALIGN", (0, 0), (0, 0), "TOP"),
                ]
            )
        )
        return header_table

    def _create_info_tables(self, owner, invoice) -> Table:
        col_widths = [2.5 * inch, 0.5 * inch, 2.5 * inch]

        bill_to_text = f"""
            <b>BILL TO</b><br/>
            {owner.farm_name or f'{owner.first_name} {owner.last_name}'}<br/>
            {owner.address_line1 or ''}<br/>
            {owner.city or ''}, {owner.state_code or ''} {owner.zip_code or ''}
        """
        bill_to_p = Paragraph(bill_to_text, self.styles["Normal"])

        invoice_info_text = f"""
            <b>STATEMENT #</b>: INV-{invoice.invoice_id}<br/>
            <b>DATE</b>: {invoice.invoice_date.strftime('%B %d, %Y')}<br/>
            <b>ACCOUNT #</b>: {owner.account_number or 'N/A'}<br/>
        """
        invoice_info_p = Paragraph(invoice_info_text, self.styles["Normal"])

        info_table = Table([[bill_to_p, "", invoice_info_p]], colWidths=col_widths)
        info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return info_table

    def _create_transactions_table(self, transactions) -> Table:
        table_data = [["DATE", "DESCRIPTION", "QTY", "PRICE", "AMOUNT"]]

        for t in transactions:
            table_data.append(
                [
                    t.transaction_date.strftime("%m/%d/%Y"),
                    Paragraph(t.description, self.styles["Normal"]),
                    f"{t.quantity:.2f}",
                    f"${t.unit_price:.2f}",
                    Paragraph(f"${t.total_price:.2f}", self.styles["Right"]),
                ]
            )

        trans_table = Table(
            table_data,
            colWidths=[0.75 * inch, 3 * inch, 0.5 * inch, 0.8 * inch, 0.8 * inch],
        )
        trans_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.darkgrey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),  # Description
                    ("ALIGN", (4, 1), (4, -1), "RIGHT"),  # Amount
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                ]
            )
        )
        return trans_table

    def _create_summary_table(self, invoice) -> Table:
        summary_data = [
            ["Subtotal:", f"${invoice.subtotal:.2f}"],
            ["Tax:", f"${invoice.tax_total or 0.00:.2f}"],
            ["Amount Paid:", f"(${invoice.amount_paid:.2f})"],
            ["", ""],
            ["BALANCE DUE:", f"${invoice.balance_due:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[1.5 * inch, 1 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LINEABOVE", (0, -1), (1, -1), 1, colors.black),
                    ("FONTNAME", (0, -1), (1, -1), "Helvetica-Bold"),
                ]
            )
        )
        return summary_table

    def _create_footer_notes(self) -> Paragraph:
        text = """
            <font size=9><b>Terms:</b> Payment is due upon receipt. A service charge of 1.50% per month will be assessed on past due balances.</font>
        """
        return Paragraph(text, self.styles["Center"])
