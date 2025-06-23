# reports/owner_statement_generator.py
"""
EDSI Veterinary Management System - Owner Statement PDF Generator
Version: 1.2.2
Purpose: Creates a PDF statement for a given owner.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v1.2.2 (2025-06-12):
    - Final corrected version based on user-provided code.
    - Ensured all styled text is correctly wrapped in Paragraph objects.
    - Maintained professional layout and correct balance calculations.
- v1.2.1 (2025-06-11):
    - Redesigned the PDF layout for better readability and alignment.
- v1.2.0 (2025-06-11):
    - Redesigned PDF with a clean, high-contrast, black-on-white style.
"""
import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from models import Owner
from controllers import CompanyProfileController
from config.app_config import AppConfig


class OwnerStatementGenerator:
    """Generates a professionally styled Owner Statement PDF."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.styles = getSampleStyleSheet()
        self.company_profile = CompanyProfileController().get_company_profile()
        self._setup_styles()

    def _setup_styles(self):
        """Creates custom paragraph and table styles for a clean, readable report."""
        self.styles.add(
            ParagraphStyle(
                name="Normal_Right", parent=self.styles["Normal"], alignment=TA_RIGHT
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Body_Left",
                parent=self.styles["BodyText"],
                alignment=TA_LEFT,
                leading=14,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Company_Title",
                parent=self.styles["h1"],
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                fontSize=14,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Bold_Right",
                parent=self.styles["Normal"],
                alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
            )
        )

        self.styles["h1"].alignment = TA_LEFT
        self.styles["h1"].fontName = "Helvetica-Bold"
        self.styles["h1"].fontSize = 16

        self.styles["h2"].alignment = TA_LEFT
        self.styles["h2"].fontName = "Helvetica-Bold"
        self.styles["h2"].fontSize = 12

    def generate_statement_pdf(
        self, statement_data: Dict[str, Any], file_path: str
    ) -> Tuple[bool, str]:
        """Creates and saves the owner statement PDF."""
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=(8.5 * inch, 11 * inch),
                leftMargin=0.75 * inch,
                rightMargin=0.75 * inch,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
            )

            story = []

            self._add_header(story, statement_data)
            story.append(Spacer(1, 0.25 * inch))

            self._add_statement_table(story, statement_data)

            doc.build(story)
            self.logger.info(f"Successfully generated owner statement: {file_path}")
            return True, f"Successfully generated owner statement to {file_path}"
        except Exception as e:
            self.logger.error(
                f"Failed to generate owner statement PDF: {e}", exc_info=True
            )
            return False, f"Failed to generate PDF: {e}"

    def _add_header(self, story, data):
        """Adds the header section with company logo, address, and statement details."""
        owner: Owner = data["owner"]

        company_name = (
            self.company_profile.company_name
            if self.company_profile
            else "EDSI Veterinary Management"
        )
        company_details_parts = [
            self.company_profile.address_line1,
            self.company_profile.address_line2,
            f"{self.company_profile.city}, {self.company_profile.state} {self.company_profile.zip_code}",
            self.company_profile.phone,
            self.company_profile.email,
            self.company_profile.website,
        ]
        company_details = "<br/>".join(filter(None, company_details_parts))

        story.append(Paragraph(company_name, self.styles["Company_Title"]))
        story.append(Spacer(1, 2))
        story.append(Paragraph(company_details, self.styles["Body_Left"]))
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("STATEMENT", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))

        contact_name = f"{owner.first_name or ''} {owner.last_name or ''}".strip()
        bill_to_parts = []
        if owner.farm_name:
            bill_to_parts.append(owner.farm_name)
        if contact_name:
            bill_to_parts.append(contact_name)
        bill_to_parts.extend(
            filter(
                None,
                [
                    owner.address_line1,
                    owner.address_line2,
                    f"{owner.city}, {owner.state_code} {owner.zip_code}",
                    owner.phone,
                    owner.email,
                ],
            )
        )

        bill_to_details = "<br/>".join(bill_to_parts)
        bill_to_para = Paragraph(
            f"<b>BILL TO:</b><br/>{bill_to_details}", self.styles["Body_Left"]
        )

        statement_info_data = [
            [
                Paragraph("<b>Statement Date:</b>", self.styles["Normal"]),
                Paragraph(data["end_date"].strftime("%Y-%m-%d"), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Account #:</b>", self.styles["Normal"]),
                Paragraph(owner.account_number or "N/A", self.styles["Normal"]),
            ],
            [
                Paragraph("<b>For Period:</b>", self.styles["Normal"]),
                Paragraph(
                    f"{data['start_date'].strftime('%Y-%m-%d')} to {data['end_date'].strftime('%Y-%m-%d')}",
                    self.styles["Normal"],
                ),
            ],
        ]
        statement_info_table = Table(
            statement_info_data, colWidths=[1.2 * inch, 2.3 * inch], hAlign="LEFT"
        )
        statement_info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        header_details_table = Table(
            [[bill_to_para, statement_info_table]], colWidths=[3.5 * inch, 3.5 * inch]
        )
        header_details_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

        story.append(header_details_table)

    def _add_statement_table(self, story, data):
        table_data = [
            [
                Paragraph(f"<b>{cell}</b>", self.styles["Normal"])
                for cell in ["Date", "Description", "Charges", "Payments", "Balance"]
            ]
        ]

        balance = Decimal(data.get("starting_balance", "0.00"))

        table_data.append(
            [
                data["start_date"].strftime("%Y-%m-%d"),
                "Previous Balance",
                "",
                "",
                f"${balance:,.2f}",
            ]
        )

        for item in data["items"]:
            charge = Decimal(item.get("charge", "0.00"))
            payment = Decimal(item.get("payment", "0.00"))
            balance += charge - payment

            charge_str = f"${charge:,.2f}" if charge else ""
            payment_str = f"${payment:,.2f}" if payment else ""

            table_data.append(
                [
                    item["date"].strftime("%Y-%m-%d"),
                    item["description"],
                    charge_str,
                    payment_str,
                    f"${balance:,.2f}",
                ]
            )

        tbl = Table(
            table_data,
            colWidths=[0.8 * inch, 3.7 * inch, 1 * inch, 1 * inch, 1 * inch],
            repeatRows=1,
        )
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        for i in range(1, len(table_data)):
            bg_color = colors.whitesmoke if i % 2 == 0 else colors.white
            tbl.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), bg_color)]))

        story.append(tbl)
        story.append(Spacer(1, 0.1 * inch))

        ending_balance_label = Paragraph(
            "<b>Ending Balance:</b>", self.styles["Normal_Right"]
        )
        ending_balance_value = Paragraph(
            f"<b>${balance:,.2f}</b>", self.styles["Normal_Right"]
        )
        summary_data = [["", ending_balance_label, ending_balance_value]]

        summary_table = Table(summary_data, colWidths=[5.5 * inch, 1 * inch, 1 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEABOVE", (1, 0), (2, 0), 1, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
