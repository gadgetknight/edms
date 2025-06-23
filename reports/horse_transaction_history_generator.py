# reports/horse_transaction_history_generator.py
"""
EDSI Veterinary Management System - Horse Transaction History PDF Generator
Version: 1.1.0
Purpose: Generates a PDF report detailing all financial transactions for a horse.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-12):
    - Refactored to be a standalone class, removing the dependency on
      ReportGeneratorBase to fix import errors.
    - Added local _setup_styles and _add_page_numbers methods.
- v1.0.0 (2025-06-12):
    - Initial creation of the Horse Transaction History report generator.
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
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

from config.app_config import AppConfig


class HorseTransactionHistoryGenerator:
    """Generates a PDF for a single horse's transaction history."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
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
        self.styles.add(
            ParagraphStyle(
                name="h1",
                parent=self.styles["h1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="h2",
                parent=self.styles["h2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                alignment=TA_CENTER,
            )
        )

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
        Generates the PDF document.
        """
        try:
            horse = report_data.get("horse")
            transactions = report_data.get("transactions", [])
            start_date = report_data.get("start_date")
            end_date = report_data.get("end_date")

            if not horse:
                return False, "Horse data is missing from the report."

            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(letter),
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            story = []
            self._add_header(story, horse, start_date, end_date)
            self._add_transaction_table(story, transactions)

            doc.build(
                story,
                onFirstPage=self._add_page_numbers,
                onLaterPages=self._add_page_numbers,
            )
            self.logger.info(f"Successfully generated PDF: {file_path}")
            return True, "PDF generated successfully."

        except Exception as e:
            self.logger.error(
                f"Error generating Horse Transaction History PDF: {e}", exc_info=True
            )
            return False, f"An unexpected error occurred: {e}"

    def _add_header(self, story: list, horse, start_date, end_date):
        """Adds the report header to the story."""
        styles = self.styles
        story.append(
            Paragraph(f"Transaction History for: {horse.horse_name}", styles["h1"])
        )
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"Report Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                styles["h2"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        owner_names = ", ".join(
            [
                owner.farm_name or f"{owner.first_name} {owner.last_name}"
                for owner in horse.owners
            ]
        )
        horse_info = f"<b>Account:</b> {horse.account_number or 'N/A'} | <b>Owner(s):</b> {owner_names}"
        story.append(Paragraph(horse_info, styles["Normal"]))

        story.append(Spacer(1, 0.2 * inch))

    def _add_transaction_table(self, story: list, transactions: list):
        """Creates and styles the main data table."""
        if not transactions:
            story.append(
                Paragraph(
                    "No transactions found for this period.", self.styles["Normal"]
                )
            )
            return

        header = [
            "Date",
            "Code",
            "Description",
            "Qty",
            "Unit Price",
            "Total",
            "Billed?",
            "Admin by",
        ]

        data = [header]

        total_charges = Decimal("0.00")

        for trans in transactions:
            total_charges += trans.total_price
            row = [
                trans.transaction_date.strftime("%Y-%m-%d"),
                trans.charge_code.code if trans.charge_code else "N/A",
                Paragraph(trans.description, self.styles["Normal_Left"]),
                f"{trans.quantity:.2f}",
                f"${trans.unit_price:.2f}",
                f"${trans.total_price:.2f}",
                "Yes" if trans.invoice_id else "No",
                trans.administered_by.user_name if trans.administered_by else "N/A",
            ]
            data.append(row)

        # Add totals row
        data.append(
            [
                "",
                "",
                Paragraph("<b>TOTAL</b>", self.styles["Normal_Right"]),
                "",
                "",
                Paragraph(f"<b>${total_charges:.2f}</b>", self.styles["Normal_Right"]),
                "",
                "",
            ]
        )

        table = Table(
            data,
            colWidths=[
                0.8 * inch,
                0.7 * inch,
                3.5 * inch,
                0.6 * inch,
                0.8 * inch,
                0.8 * inch,
                0.6 * inch,
                1.0 * inch,
            ],
            repeatRows=1,
        )

        style = TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(AppConfig.DARK_HEADER_FOOTER),
                ),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#e0e0e0")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                # Alignment for data rows
                ("ALIGN", (0, 1), (1, -1), "CENTER"),  # Date, Code
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),  # Qty
                ("ALIGN", (4, 1), (6, -1), "RIGHT"),  # Prices, Total, Billed
                ("ALIGN", (7, 1), (7, -1), "LEFT"),  # Admin
                # Totals Row Style
                ("SPAN", (2, -1), (4, -1)),
                ("ALIGN", (2, -1), (2, -1), "RIGHT"),
                ("FONTNAME", (2, -1), (5, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
        table.setStyle(style)
        story.append(table)
