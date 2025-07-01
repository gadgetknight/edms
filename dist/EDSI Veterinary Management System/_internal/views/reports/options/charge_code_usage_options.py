"""
EDSI Veterinary Management System - Charge Code Usage Options Widget
Version: 2.0.0
Purpose: An advanced UI panel for selecting options for the Charge Code Usage report.
Last Updated: June 12, 2025
Author: Gemini

Changelog:
- v2.0.0 (2025-06-12):
    - Upgraded widget to include options for grouping and sorting the report data.
    - Added QGroupBoxes for better UI organization.
    - get_options() now returns group_by and sort_by keys.
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QDateEdit,
    QGroupBox,
    QRadioButton,
    QComboBox,
)
from PySide6.QtCore import Qt, QDate

from config.app_config import AppConfig


class ChargeCodeUsageOptionsWidget(QWidget):
    """Widget for setting options for the Charge Code Usage report."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()

    def _setup_ui(self):
        """Initializes the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Date Range Group ===
        date_group = QGroupBox("Date Range")
        date_layout = QGridLayout(date_group)

        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(date.today() - timedelta(days=30))

        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(date.today())

        date_layout.addWidget(QLabel("Start Date:"), 0, 0)
        date_layout.addWidget(self.start_date_edit, 0, 1)
        date_layout.addWidget(QLabel("End Date:"), 1, 0)
        date_layout.addWidget(self.end_date_edit, 1, 1)

        # === Grouping Group ===
        grouping_group = QGroupBox("Group By")
        grouping_layout = QVBoxLayout(grouping_group)
        self.group_by_code_radio = QRadioButton("Charge Code")
        self.group_by_category_radio = QRadioButton("Charge Code Category")
        self.group_by_code_radio.setChecked(True)
        grouping_layout.addWidget(self.group_by_code_radio)
        grouping_layout.addWidget(self.group_by_category_radio)

        # === Sorting Group ===
        sorting_group = QGroupBox("Sort By")
        sorting_layout = QVBoxLayout(sorting_group)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            [
                "Usage Count (High to Low)",
                "Total Revenue (High to Low)",
                "Charge Code (A-Z)",
                "Category (A-Z)",
            ]
        )
        sorting_layout.addWidget(self.sort_combo)

        main_layout.addWidget(date_group)
        main_layout.addWidget(grouping_group)
        main_layout.addWidget(sorting_group)

        self.setStyleSheet(self._get_style())

    def _get_style(self) -> str:
        """Returns the stylesheet for the widget."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                color: {AppConfig.DARK_TEXT_SECONDARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 5px;
                margin-top: 1ex;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
            }}
            QLabel {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
                font-size: 10pt;
            }}
            QDateEdit, QComboBox {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: white;
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QDateEdit:focus, QComboBox:focus {{
                border: 1px solid {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QRadioButton {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
        """

    def get_options(self) -> Dict[str, Any]:
        """
        Retrieves the selected report options from the UI controls.

        Returns:
            A dictionary containing the selected options.
        """
        grouping_option = (
            "category" if self.group_by_category_radio.isChecked() else "code"
        )

        options = {
            "start_date": self.start_date_edit.date().toPython(),
            "end_date": self.end_date_edit.date().toPython(),
            "group_by": grouping_option,
            "sort_by": self.sort_combo.currentText(),
        }
        self.logger.info(f"Report options selected: {options}")
        return options
