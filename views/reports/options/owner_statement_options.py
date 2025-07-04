# views/reports/options/owner_statement_options.py
"""
EDSI Veterinary Management System - Owner Statement Options Widget
Version: 1.0.0
Purpose: A widget defining the user-selectable options for generating an
         Owner Statement report.
Last Updated: June 11, 2025
Author: Gemini
"""

import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QLabel,
)
from PySide6.QtCore import Qt, QDate

from controllers import OwnerController
from config.app_config import AppConfig


class OwnerStatementOptionsWidget(QWidget):
    """UI for the Owner Statement report options."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.owner_controller = OwnerController()

        self.setup_ui()
        self.load_owners()

    def setup_ui(self):
        """Initializes and lays out the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        # Owner Selection
        self.owner_combo = QComboBox()
        form_layout.addRow("Select Owner*:", self.owner_combo)

        # Date Range
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Start Date:", self.start_date_edit)

        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("End Date:", self.end_date_edit)

        # Additional Options
        self.include_balance_checkbox = QCheckBox("Include previous balance")
        self.include_balance_checkbox.setChecked(True)
        form_layout.addRow("", self.include_balance_checkbox)

        layout.addLayout(form_layout)
        self.apply_styles()

    def apply_styles(self):
        """Applies consistent styling to the widgets."""
        style_sheet = f"""
            QComboBox, QDateEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
                min-height: 22px;
            }}
            QComboBox:focus, QDateEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QCheckBox, QLabel {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
        """
        self.setStyleSheet(style_sheet)

    def load_owners(self):
        """Fetches active owners and populates the combo box."""
        self.owner_combo.clear()
        self.owner_combo.addItem("All Owners", "all")
        try:
            owners_data = self.owner_controller.get_all_owners_for_lookup()
            for owner in owners_data:
                self.owner_combo.addItem(owner["name_account"], owner["id"])
        except Exception as e:
            self.logger.error(
                f"Failed to load owners for report options: {e}", exc_info=True
            )

    def get_options(self) -> Dict:
        """Returns the currently selected report options."""
        return {
            "owner_id": self.owner_combo.currentData(),
            "start_date": self.start_date_edit.date().toPython(),
            "end_date": self.end_date_edit.date().toPython(),
            "include_previous_balance": self.include_balance_checkbox.isChecked(),
        }
