# reports/invoice_generator.py
"""
EDSI Veterinary Management System - Invoice PDF Generator
Version: 1.2.4
Purpose: Generates a professional, print-friendly PDF for a single invoice.
Last Updated: June 13, 2025
Author: Gemini

Changelog:
- v1.2.4 (2025-06-13):
    - Fixed KeyError by correcting style name from 'Center' to 'Normal_Center'
      in the footer creation.
- v1.2.3 (2025-06-13):
    - Fixed KeyError by correcting style name from 'Right' to 'Normal_Right' in
      the summary table creation.
- v1.2.2 (2025-06-13):
    - Fixed KeyError by correcting style name from 'Right' to 'Normal_Right' in
      the summary table creation.
- v1.2.1 (2025-06-13):
    - Fixed KeyError by modifying existing 'h1' and 'h2' styles instead of
      trying to add new ones with the same name.
- v1.2.0 (2025-06-12):
    - Refactored to be a standalone class, removing the dependency on
      ReportGeneratorBase to fix import errors.
    - Added local _setup_styles and _add_page_numbers methods.
- v1.1.0 (2025-06-12):
    - Refactored to inherit from ReportGeneratorBase.
- v1.0.1 (2025-06-09):
    - Bug Fix: Added `Tuple` to the import from the `typing` module.
- v1.0.0 (2025-06-09):
    - Initial creation of the invoice PDF generator.
"""
import logging
from typing import Dict, Any, Tuple
from decimal import Decimal

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

from config.app_config import AppConfig
from controllers import FinancialController, CompanyProfileController
from models import Invoice, Transaction


class InvoiceGenerator:
    """Generates a PDF for a single invoice."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
        self.company_profile_controller = CompanyProfileController()
        self.financial_controller = FinancialController()
        self._setup_styles()

    def _setup_styles(self):
        """Sets up custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="Normal_Left", parent=self.styles["Normal"], alignment=TA_LEFT
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Normal_Center", parent=self.styles["Normal"], alignment=TA_CENTER
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Normal_Right", parent=self.styles["Normal"], alignment=TA_RIGHT
            )
        )

        self.styles["h1"].fontName = "Helvetica-Bold"
        self.styles["h1"].fontSize = 16
        self.styles["h1"].alignment = TA_CENTER

        self.styles["h2"].fontName = "Helvetica-Bold"
        self.styles["h2"].fontSize = 12
        self.styles["h2"].alignment = TA_CENTER

    def _add_page_numbers(self, canvas, doc):
        """Adds page numbers to each page of the PDF."""
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        page_number_text = f"Page {doc.page}"
        canvas.drawCentredString(
            doc.width / 2.0 + doc.leftMargin, 0.25 * inch, page_number_text
        )
        canvas.restoreState()

    def generate_invoice_pdf(self, invoice_id: int, file_path: str) -> Tuple[bool, str]:
        """
        Fetches all data for an invoice and generates a PDF at the specified path.
        """
        try:
            invoice = self.financial_controller.get_invoice_by_id(invoice_id)
            if not invoice:
                return False, f"Invoice ID {invoice_id} not found."

            company_profile = self.company_profile_controller.get_company_profile()
            if not company_profile:
                return False, "Company Profile is not set up."

            owner = invoice.owner
            if not owner:
                return False, f"Owner with ID {invoice.owner_id} not found."

            transactions = self.financial_controller.get_transactions_for_invoice(
                invoice_id
            )

            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )
            story = []

            story.append(self._create_header(company_profile))
            story.append(Spacer(1, 0.25 * inch))
            story.append(self._create_info_tables(owner, invoice))
            story.append(Spacer(1, 0.25 * inch))
            story.append(self._create_transactions_table(transactions))
            story.append(Spacer(1, 0.2 * inch))
            story.append(self._create_summary_table(invoice))
            story.append(Spacer(1, 0.4 * inch))
            story.append(self._create_footer_notes())

            doc.build(
                story,
                onFirstPage=self._add_page_numbers,
                onLaterPages=self._add_page_numbers,
            )

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
        header_table = Table([[header_paragraph]], colWidths=[6.5 * inch])
        header_table.setStyle(
            TableStyle(
                [("ALIGN", (0, 0), (0, 0), "LEFT"), ("VALIGN", (0, 0), (0, 0), "TOP")]
            )
        )
        return header_table

    def _create_info_tables(self, owner, invoice) -> Table:
        col_widths = [3 * inch, 0.5 * inch, 3 * inch]
        bill_to_text = f"""
            <b>BILL TO</b><br/>
            {owner.farm_name or f'{owner.first_name or ""} {owner.last_name or ""}'.strip()}<br/>
            {owner.address_line1 or ''}<br/>
            {owner.city or ''}, {owner.state_code or ''} {owner.zip_code or ''}
        """
        bill_to_p = Paragraph(bill_to_text, self.styles["Normal_Left"])

        invoice_info_text = f"""
            <b>STATEMENT #:</b> INV-{invoice.invoice_id}<br/>
            <b>DATE:</b> {invoice.invoice_date.strftime('%B %d, %Y')}<br/>
            <b>ACCOUNT #:</b> {owner.account_number or 'N/A'}<br/>
        """
        invoice_info_p = Paragraph(invoice_info_text, self.styles["Normal_Left"])

        info_table = Table([[bill_to_p, "", invoice_info_p]], colWidths=col_widths)
        info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return info_table

    def _create_transactions_table(self, transactions) -> Table:
        header = [
            Paragraph("<b>DATE</b>", self.styles["Normal"]),
            Paragraph("<b>DESCRIPTION</b>", self.styles["Normal"]),
            Paragraph("<b>QTY</b>", self.styles["Normal_Right"]),
            Paragraph("<b>PRICE</b>", self.styles["Normal_Right"]),
            Paragraph("<b>AMOUNT</b>", self.styles["Normal_Right"]),
        ]
        table_data = [header]

        for t in transactions:
            table_data.append(
                [
                    t.transaction_date.strftime("%m/%d/%Y"),
                    Paragraph(t.description, self.styles["Normal_Left"]),
                    f"{t.quantity:.2f}",
                    f"${t.unit_price:.2f}",
                    Paragraph(f"${t.total_price:.2f}", self.styles["Normal_Right"]),
                ]
            )

        trans_table = Table(
            table_data,
            colWidths=[0.75 * inch, 3.2 * inch, 0.6 * inch, 0.9 * inch, 1.0 * inch],
        )
        trans_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(AppConfig.DARK_HEADER_FOOTER),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0f0f0")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        return trans_table

    def _create_summary_table(self, invoice) -> Table:
        container_col_widths = [4.5 * inch, 2.0 * inch]
        summary_data = [
            ["Subtotal:", f"${invoice.subtotal:.2f}"],
            ["Tax:", f"${invoice.tax_total or 0.00:.2f}"],
            ["Amount Paid:", f"(${invoice.amount_paid:.2f})"],
            ["", ""],
            [
                Paragraph("<b>BALANCE DUE:</b>", self.styles["Normal_Right"]),
                Paragraph(
                    f"<b>${invoice.balance_due:.2f}</b>", self.styles["Normal_Right"]
                ),
            ],
        ]
        summary_table = Table(summary_data, colWidths=[1.0 * inch, 1.0 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LINEABOVE", (0, -1), (1, -1), 1, colors.black),
                    ("TOPPADDING", (0, -1), (1, -1), 5),
                ]
            )
        )
        container_table = Table([[None, summary_table]], colWidths=container_col_widths)
        container_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return container_table

    def _create_footer_notes(self) -> Paragraph:
        text = """
            <font size=9><b>Terms:</b> Payment is due upon receipt. A service charge of 1.50% per month will be assessed on past due balances.</font>
        """
        return Paragraph(text, self.styles["Normal_Center"])
