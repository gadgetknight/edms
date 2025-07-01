"""
EDSI Veterinary Management System - Charge Code Usage PDF Generator
Version: 2.0.0
Purpose: Generates a PDF report for charge code usage statistics, including revenue and sorting.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v2.0.0 (2025-06-12):
    - Upgraded generator to handle a more complex data structure including summary
      data and revenue totals.
    - Added a summary box to the top of the report.
    - Added "Total Revenue" column to the details table.
    - Updated styling to use AppConfig colors for a professional look.
    - Added a more detailed page footer.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch

from config.app_config import AppConfig


class ChargeCodeUsageGenerator:
    """Generates a PDF for the Charge Code Usage report."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
        self.story = []

    def generate_pdf(
        self, report_data: Dict[str, Any], file_path: str
    ) -> Tuple[bool, str]:
        """
        Generates the full PDF report.

        Args:
            report_data: The data dictionary from ReportsController.
            file_path: The full path to save the PDF file.

        Returns:
            A tuple (success, message).
        """
        try:
            self.doc = SimpleDocTemplate(
                file_path,
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            self._add_header(report_data)
            self._add_summary(report_data["summary"])
            self._add_details_table(report_data["details"])

            self.doc.build(
                self.story,
                onFirstPage=self._add_page_footer,
                onLaterPages=self._add_page_footer,
            )
            self.logger.info(
                f"Successfully generated Charge Code Usage report at {file_path}"
            )
            return True, "Report generated successfully."
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}", exc_info=True)
            return False, f"An error occurred: {e}"

    def _add_header(self, report_data: Dict[str, Any]):
        """Adds the main header to the document."""
        options = report_data["options"]
        start_date_str = options["start_date"].strftime("%Y-%m-%d")
        end_date_str = options["end_date"].strftime("%Y-%m-%d")

        title_style = self.styles["h1"]
        title_style.alignment = TA_CENTER
        title_style.textColor = colors.HexColor("#2D3748")

        self.story.append(Paragraph("Charge Code Usage Report", title_style))
        self.story.append(Spacer(1, 0.1 * inch))

        subtitle_style = self.styles["h3"]
        subtitle_style.alignment = TA_CENTER
        self.story.append(
            Paragraph(f"For Period: {start_date_str} to {end_date_str}", subtitle_style)
        )
        self.story.append(Spacer(1, 0.25 * inch))

    def _add_summary(self, summary_data: Dict[str, Any]):
        """Adds a summary box with key metrics."""
        summary_style = ParagraphStyle(
            "Summary", parent=self.styles["Normal"], spaceAfter=10
        )

        summary_text = f"""
            <b>Total Unique Codes Used:</b> {summary_data['unique_codes_used']}<br/>
            <b>Total Usage Count:</b> {summary_data['total_usage_count']}<br/>
            <b>Total Revenue:</b> ${summary_data['total_revenue']:,.2f}
        """

        p = Paragraph(summary_text, summary_style)
        self.story.append(p)
        self.story.append(Spacer(1, 0.25 * inch))

    def _add_details_table(self, details: List[Dict]):
        """Creates and adds the main data table."""
        if not details:
            self.story.append(
                Paragraph(
                    "No usage data found for the selected criteria.",
                    self.styles["Normal"],
                )
            )
            return

        col_widths = [1.2 * inch, 2.8 * inch, 1.5 * inch, 1 * inch, 1 * inch]
        header = [
            Paragraph("<b>Code</b>", self.styles["Normal"]),
            Paragraph("<b>Description</b>", self.styles["Normal"]),
            Paragraph("<b>Category</b>", self.styles["Normal"]),
            Paragraph("<b>Usage Count</b>", self.styles["Normal"]),
            Paragraph("<b>Total Revenue</b>", self.styles["Normal"]),
        ]

        data = [header]

        num_style = ParagraphStyle(
            name="num_style", parent=self.styles["Normal"], alignment=TA_RIGHT
        )

        for item in details:
            row = [
                Paragraph(item["code"], self.styles["Normal"]),
                Paragraph(item["description"], self.styles["Normal"]),
                Paragraph(item["category_name"], self.styles["Normal"]),
                Paragraph(str(item["usage_count"]), num_style),
                Paragraph(f"${item['total_revenue']:,.2f}", num_style),
            ]
            data.append(row)

        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(AppConfig.DARK_PRIMARY_ACTION),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#EDF2F7")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        self.story.append(table)

    def _add_page_footer(self, canvas, doc):
        """Adds a footer to each page."""
        canvas.saveState()
        canvas.setFont("Helvetica", 9)

        page_num_text = f"Page {doc.page}"
        canvas.drawRightString(doc.width + 0.5 * inch, 0.25 * inch, page_num_text)

        gen_date_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        canvas.drawString(doc.leftMargin, 0.25 * inch, gen_date_text)

        canvas.restoreState()
