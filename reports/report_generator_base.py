# reports/report_generator_base.py
"""
EDSI Veterinary Management System - Report Generator Base Class
Version: 1.0.0
Purpose: Provides a base class for all PDF report generators, handling
         common elements like page numbering and standard styles.
Last Updated: June 12, 2025
Author: Gemini
"""

import logging
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black
from config.app_config import AppConfig


class ReportGeneratorBase:
    """Base class for PDF report generators."""

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
            doc.width / 2.0 + doc.leftMargin, 0.25 * AppConfig.inch, page_number_text
        )
        canvas.restoreState()
