# reports/charge_code_usage_generator.py
"""
EDSI Veterinary Management System - Charge Code Usage PDF Generator
Version: 1.0.0
Purpose: Creates a PDF report summarizing charge code usage.
Last Updated: June 11, 2025
Author: Gemini
"""
import logging
from typing import Dict, Any, Tuple

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


class ChargeCodeUsageGenerator:
    """Generates a Charge Code Usage PDF."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Creates custom styles for the report."""
        self.styles["h1"].alignment = TA_LEFT
        self.styles["h2"].alignment = TA_LEFT
        self.styles.add(
            ParagraphStyle(
                name="Normal_Right", parent=self.styles["Normal"], alignment=TA_RIGHT
            )
        )

    def generate_pdf(
        self, report_data: Dict[str, Any], file_path: str
    ) -> Tuple[bool, str]:
        """Creates and saves the Charge Code Usage PDF."""
        try:
            doc = SimpleDocTemplate(file_path, pagesize=(8.5 * inch, 11 * inch))
            story = []

            story.append(Paragraph("Charge Code Usage Report", self.styles["h1"]))
            start_date_str = report_data["start_date"].strftime("%Y-%m-%d")
            end_date_str = report_data["end_date"].strftime("%Y-%m-%d")
            story.append(
                Paragraph(
                    f"For Period: {start_date_str} to {end_date_str}", self.styles["h2"]
                )
            )
            story.append(Spacer(1, 0.25 * inch))

            table_data = [["Code", "Description", "Category", "Usage Count"]]
            for item in report_data["usage_data"]:
                table_data.append(
                    [
                        item["code"],
                        Paragraph(item["description"], self.styles["Normal"]),
                        item["category"],
                        str(item["count"]),
                    ]
                )

            total_usage = sum(item["count"] for item in report_data["usage_data"])
            table_data.append(
                [
                    Paragraph(
                        f"<b>Total Codes Used: {len(report_data['usage_data'])}</b>",
                        self.styles["Normal"],
                    ),
                    "",
                    "",
                    Paragraph(f"<b>{total_usage}</b>", self.styles["Normal_Right"]),
                ]
            )

            tbl = Table(
                table_data,
                colWidths=[1 * inch, 3.5 * inch, 2 * inch, 1 * inch],
                repeatRows=1,
            )
            style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
                    ("SPAN", (0, -1), (2, -1)),
                ]
            )
            tbl.setStyle(style)
            story.append(tbl)

            doc.build(story)
            self.logger.info(
                f"Successfully generated Charge Code Usage report: {file_path}"
            )
            return True, "Report generated successfully."
        except Exception as e:
            self.logger.error(
                f"Failed to generate Charge Code Usage PDF: {e}", exc_info=True
            )
            return False, f"Failed to generate PDF: {e}"
