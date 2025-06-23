# reports/ar_aging_generator.py
"""
EDSI Veterinary Management System - A/R Aging PDF Generator
Version: 1.1.0
Purpose: Creates a PDF A/R Aging report.
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


class ARAgingGenerator:
    """Generates an A/R Aging PDF."""

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
        """Creates and saves the A/R Aging PDF."""
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

            story.append(
                Paragraph("Accounts Receivable Aging Report", self.styles["h1"])
            )
            as_of_date_str = report_data["as_of_date"].strftime("%B %d, %Y")
            story.append(Paragraph(f"Aged as of: {as_of_date_str}", self.styles["h2"]))
            story.append(Spacer(1, 0.25 * inch))

            self._add_aging_table(story, report_data["lines"], report_data["totals"])

            doc.build(
                story,
                onFirstPage=self._add_page_numbers,
                onLaterPages=self._add_page_numbers,
            )
            self.logger.info(f"Successfully generated A/R Aging report: {file_path}")
            return True, f"Successfully generated report to {file_path}"
        except Exception as e:
            self.logger.error(f"Failed to generate A/R Aging PDF: {e}", exc_info=True)
            return False, f"Failed to generate PDF: {e}"

    def _add_aging_table(self, story, lines, totals):
        table_data = [
            [
                "Owner",
                "Current",
                "31-60 Days",
                "61-90 Days",
                "Over 90 Days",
                "Total Balance",
            ]
        ]

        for line in lines:
            table_data.append(
                [
                    Paragraph(line["name"], self.styles["Normal_Left"]),
                    f"${line['buckets']['current']:,.2f}",
                    f"${line['buckets']['31-60']:,.2f}",
                    f"${line['buckets']['61-90']:,.2f}",
                    f"${line['buckets']['over_90']:,.2f}",
                    f"${line['total']:,.2f}",
                ]
            )

        table_data.append(
            [
                Paragraph("<b>TOTALS</b>", self.styles["Normal"]),
                Paragraph(
                    f"<b>${totals['current']:,.2f}</b>", self.styles["Normal_Right"]
                ),
                Paragraph(
                    f"<b>${totals['31-60']:,.2f}</b>", self.styles["Normal_Right"]
                ),
                Paragraph(
                    f"<b>${totals['61-90']:,.2f}</b>", self.styles["Normal_Right"]
                ),
                Paragraph(
                    f"<b>${totals['over_90']:,.2f}</b>", self.styles["Normal_Right"]
                ),
                Paragraph(
                    f"<b>${totals['total']:,.2f}</b>", self.styles["Normal_Right"]
                ),
            ]
        )

        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
            ]
        )
        tbl = Table(
            table_data,
            colWidths=[
                3 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
                1.5 * inch,
            ],
            repeatRows=1,
        )
        tbl.setStyle(style)
        story.append(tbl)
