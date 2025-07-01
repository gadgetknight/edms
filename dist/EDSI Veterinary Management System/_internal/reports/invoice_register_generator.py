# reports/invoice_register_generator.py
"""
EDSI Veterinary Management System - Invoice Register PDF Generator
Version: 1.1.1
Purpose: Creates a PDF Invoice Register report.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v1.1.1 (2025-06-28):
    - Modified `_add_register_table` to use `inv.display_invoice_id` for the
      "Inv #" column, reflecting the new owner-specific, date-sequential format.
    - Modified `_add_register_table` to format the "Billed To" column as
      `Farm Name (First Name Last Name) [Account Number]` (or `First Name Last Name [Account Number]`
      if no farm name) for improved clarity.
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

            table_data.append(
                [
                    inv.display_invoice_id,  # MODIFIED: Use the hybrid property
                    inv.invoice_date.strftime("%Y-%m-%d"),
                    Paragraph(
                        owner_display_text, self.styles["Normal_Left"]
                    ),  # Use the formatted text
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
                0.9 * inch,  # Increased width for new ID format
                0.9 * inch,
                3.2 * inch,  # Adjusted width for detailed Billed To
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
            ],
            repeatRows=1,
        )
        tbl.setStyle(style)
        story.append(tbl)
