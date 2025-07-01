# reports/payment_history_generator.py
"""
EDSI Veterinary Management System - Payment History PDF Generator
Version: 1.1.0
Purpose: Generates a PDF report listing all payments in a date range.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-12):
    - Refactored to be a standalone class, removing ReportGeneratorBase dependency.
    - Added local style and page number setup.
- v1.0.0 (2025-06-11):
    - Initial creation of the Payment History report generator.
"""
import logging
from typing import Dict, Any, Tuple
from decimal import Decimal

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from config.app_config import AppConfig


class PaymentHistoryGenerator:
    """Generates a PDF for the Payment History report."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Creates custom styles for the report."""
        self.styles.add(
            ParagraphStyle(
                name="Normal_Right", parent=self.styles["Normal"], alignment=TA_RIGHT
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Normal_Left", parent=self.styles["Normal"], alignment=TA_LEFT
            )
        )
        self.styles["h1"].alignment = TA_LEFT
        self.styles["h2"].alignment = TA_LEFT

    def _add_page_numbers(self, canvas, doc):
        """Adds page numbers to each page of the PDF."""
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        page_number_text = f"Page {doc.page}"
        canvas.drawCentredString(
            doc.width / 2.0 + doc.leftMargin, 0.25 * inch, page_number_text
        )
        canvas.restoreState()

    def generate_pdf(
        self, report_data: Dict[str, Any], file_path: str
    ) -> Tuple[bool, str]:
        """
        Generates the Payment History PDF.
        """
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                leftMargin=0.75 * inch,
                rightMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )
            story = []

            self._add_header(story, report_data["start_date"], report_data["end_date"])
            self._add_payments_table(story, report_data["payments"])

            doc.build(
                story,
                onFirstPage=self._add_page_numbers,
                onLaterPages=self._add_page_numbers,
            )
            return True, "Payment History report generated successfully."
        except Exception as e:
            self.logger.error(
                f"Failed to generate Payment History PDF: {e}", exc_info=True
            )
            return False, f"An unexpected error occurred: {e}"

    def _add_header(self, story, start_date, end_date):
        story.append(Paragraph("Payment History", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(
            Paragraph(
                f"For Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
                self.styles["h2"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

    def _add_payments_table(self, story, payments):
        header = ["Date", "Paid By", "Amount", "Method", "Reference #"]

        data = [header]

        total_payments = Decimal("0.00")

        for pmt in payments:
            total_payments += pmt.amount
            owner_name = (
                pmt.owner.farm_name
                or f"{pmt.owner.first_name or ''} {pmt.owner.last_name or ''}".strip()
            )
            row = [
                pmt.payment_date.strftime("%Y-%m-%d"),
                Paragraph(owner_name, self.styles["Normal_Left"]),
                f"${pmt.amount:.2f}",
                pmt.payment_method,
                pmt.reference_number or "",
            ]
            data.append(row)

        # Add totals row
        data.append(
            ["", "<b>TOTAL PAYMENTS</b>", f"<b>${total_payments:.2f}</b>", "", ""]
        )

        payment_table = Table(
            data,
            colWidths=[1 * inch, 2.5 * inch, 1.2 * inch, 1.2 * inch, 1.5 * inch],
            repeatRows=1,
        )

        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#f0f0f0")),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),  # Amount
                ("ALIGN", (0, 1), (1, -1), "LEFT"),  # Date, Paid By
                ("ALIGN", (3, 1), (4, -1), "CENTER"),  # Method, Ref
                # Style for the totals row
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, -1), (1, -1), "RIGHT"),
                ("SPAN", (0, -1), (1, -1)),  # Span the total label
                ("ALIGN", (2, -1), (2, -1), "RIGHT"),
            ]
        )
        payment_table.setStyle(style)

        story.append(payment_table)
