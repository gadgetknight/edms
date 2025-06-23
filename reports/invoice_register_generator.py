# reports/invoice_register_generator.py
"""
EDSI Veterinary Management System - Invoice Register PDF Generator
Version: 1.1.0
Purpose: Creates a PDF Invoice Register report.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-12):
    - Final corrected version. Standalone class.
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Tuple

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import landscape, letter

from config.app_config import AppConfig
from models import Invoice


class InvoiceRegisterGenerator:
    """Generates an Invoice Register PDF."""

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
        """Creates and saves the Invoice Register PDF."""
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(letter),
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            story = []

            story.append(Paragraph("Invoice Register", self.styles["h1"]))
            start_date_str = report_data["start_date"].strftime("%Y-%m-%d")
            end_date_str = report_data["end_date"].strftime("%Y-%m-%d")
            story.append(
                Paragraph(
                    f"For Period: {start_date_str} to {end_date_str}", self.styles["h2"]
                )
            )
            story.append(Spacer(1, 0.25 * inch))

            self._add_register_table(story, report_data["invoices"])

            doc.build(
                story,
                onFirstPage=self._add_page_numbers,
                onLaterPages=self._add_page_numbers,
            )
            self.logger.info(
                f"Successfully generated Invoice Register report: {file_path}"
            )
            return True, f"Successfully generated report to {file_path}"
        except Exception as e:
            self.logger.error(
                f"Failed to generate Invoice Register PDF: {e}", exc_info=True
            )
            return False, f"Failed to generate PDF: {e}"

    def _add_register_table(self, story, invoices):
        table_data = [
            [
                "Inv #",
                "Date",
                "Billed To",
                "Total",
                "Amount Paid",
                "Balance Due",
                "Status",
            ]
        ]

        grand_total = Decimal("0.00")
        for inv in invoices:
            owner_name = (
                inv.owner.farm_name
                or f"{inv.owner.first_name or ''} {inv.owner.last_name or ''}".strip()
            )
            table_data.append(
                [
                    f"INV-{inv.invoice_id}",
                    inv.invoice_date.strftime("%Y-%m-%d"),
                    Paragraph(owner_name, self.styles["Normal_Left"]),
                    f"${inv.grand_total:,.2f}",
                    f"${inv.amount_paid:,.2f}",
                    f"${inv.balance_due:,.2f}",
                    inv.status,
                ]
            )
            grand_total += inv.grand_total

        table_data.append(
            [
                Paragraph(
                    f"<b>Total Invoices: {len(invoices)}</b>",
                    self.styles["Normal"],
                ),
                "",
                "",
                Paragraph(f"<b>${grand_total:,.2f}</b>", self.styles["Normal_Right"]),
                "",
                "",
                "",
            ]
        )

        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
                ("SPAN", (0, -1), (2, -1)),
                ("SPAN", (3, -1), (6, -1)),
                ("ALIGN", (3, -1), (3, -1), "RIGHT"),
            ]
        )
        tbl = Table(
            table_data,
            colWidths=[
                0.7 * inch,
                0.9 * inch,
                3.4 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
            ],
            repeatRows=1,
        )
        tbl.setStyle(style)
        story.append(tbl)
