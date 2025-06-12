# views/reports/options/charge_code_usage_options.py
"""
EDSI Veterinary Management System - Charge Code Usage Options Widget
Version: 1.0.0
Purpose: A widget defining the user-selectable options for generating a
         Charge Code Usage report.
Last Updated: June 11, 2025
Author: Gemini
"""

import logging
from typing import Optional, Dict
from datetime import date

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDateEdit,
    QLabel,
    QComboBox,
)
from PySide6.QtCore import Qt, QDate

from config.app_config import AppConfig


class ChargeCodeUsageOptionsWidget(QWidget):
    """UI for the Charge Code Usage report options."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_ui()

    def setup_ui(self):
        """Initializes and lays out the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        description = QLabel(
            "This report shows how many times each charge code was used "
            "within the selected date range."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-bottom: 15px;"
        )
        layout.addWidget(description)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        # Date Range
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Start Date:", self.start_date_edit)

        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("End Date:", self.end_date_edit)

        layout.addLayout(form_layout)
        self.apply_styles()

    def apply_styles(self):
        """Applies consistent styling to the widgets."""
        style_sheet = f"""
            QDateEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
                min-height: 22px;
            }}
            QDateEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QLabel {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
        """
        self.setStyleSheet(style_sheet)

    def get_options(self) -> Dict:
        """Returns the currently selected report options."""
        return {
            "start_date": self.start_date_edit.date().toPython(),
            "end_date": self.end_date_edit.date().toPython(),
        }
