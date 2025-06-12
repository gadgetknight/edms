# reports/payment_history_generator.py
"""
EDSI Veterinary Management System - Payment History PDF Generator
Version: 1.0.0
Purpose: Creates a PDF Payment History report.
Last Updated: June 11, 2025
Author: Gemini
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Tuple

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from config.app_config import AppConfig


class PaymentHistoryGenerator:
    """Generates a Payment History PDF."""

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
        self.styles["h1"].alignment = TA_LEFT
        self.styles["h2"].alignment = TA_LEFT

    def generate_pdf(
        self, report_data: Dict[str, Any], file_path: str
    ) -> Tuple[bool, str]:
        """Creates and saves the Payment History PDF."""
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=(11 * inch, 8.5 * inch),  # Landscape
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            story = []

            # --- Header ---
            story.append(Paragraph("Payment History Report", self.styles["h1"]))
            start_date_str = report_data["start_date"].strftime("%Y-%m-%d")
            end_date_str = report_data["end_date"].strftime("%Y-%m-%d")
            story.append(
                Paragraph(
                    f"For Period: {start_date_str} to {end_date_str}", self.styles["h2"]
                )
            )
            story.append(Spacer(1, 0.25 * inch))

            # --- Table ---
            table_data = [
                ["Date", "Paid By", "Amount", "Method", "Reference #", "Notes"]
            ]

            total_payments = Decimal("0.00")
            for pmt in report_data["payments"]:
                owner_name = "N/A"
                if pmt.owner:
                    owner_name = (
                        pmt.owner.farm_name
                        or f"{pmt.owner.first_name or ''} {pmt.owner.last_name or ''}".strip()
                    )

                table_data.append(
                    [
                        pmt.payment_date.strftime("%Y-%m-%d"),
                        owner_name,
                        f"${pmt.amount:,.2f}",
                        pmt.payment_method,
                        pmt.reference_number or "",
                        pmt.notes or "",
                    ]
                )
                total_payments += pmt.amount

            # --- Totals Row ---
            table_data.append(
                [
                    Paragraph(
                        f"<b>Total Payments: {len(report_data['payments'])}</b>",
                        self.styles["Normal"],
                    ),
                    "",
                    Paragraph(
                        f"<b>${total_payments:,.2f}</b>", self.styles["Normal_Right"]
                    ),
                    "",
                    "",
                    "",
                ]
            )

            # --- Table Style ---
            style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 1), (2, -1), "RIGHT"),  # Align Amount column
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
                    ("SPAN", (0, -1), (1, -1)),
                ]
            )
            tbl = Table(
                table_data,
                colWidths=[
                    1 * inch,
                    2.5 * inch,
                    1.25 * inch,
                    1.25 * inch,
                    1.5 * inch,
                    2.5 * inch,
                ],
                repeatRows=1,
            )
            tbl.setStyle(style)
            story.append(tbl)

            doc.build(story)
            self.logger.info(
                f"Successfully generated Payment History report: {file_path}"
            )
            return True, f"Successfully generated report to {file_path}"
        except Exception as e:
            self.logger.error(
                f"Failed to generate Payment History PDF: {e}", exc_info=True
            )
            return False, f"Failed to generate PDF: {e}"
