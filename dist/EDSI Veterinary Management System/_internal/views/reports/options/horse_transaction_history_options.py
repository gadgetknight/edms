# views/reports/options/horse_transaction_history_options.py
"""
EDSI Veterinary Management System - Horse Transaction History Options Widget
Version: 1.0.0
Purpose: A widget defining the user-selectable options for generating a
         Horse Transaction History report.
Last Updated: June 12, 2025
Author: Gemini
"""

import logging
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDateEdit,
    QLabel,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, QDate, QTimer

from config.app_config import AppConfig
from controllers import HorseController
from models import Horse


class HorseTransactionHistoryOptionsWidget(QWidget):
    """UI for the Horse Transaction History report options."""

    def __init__(
        self, horse_controller: HorseController, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse_controller = horse_controller
        self.all_horses: List[Horse] = []
        self.selected_horse_id: Optional[int] = None

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_horse_list)

        self.setup_ui()
        self.load_horses()

    def setup_ui(self):
        """Initializes and lays out the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        description = QLabel(
            "This report provides a detailed list of all financial transactions "
            "for a single horse within a selected date range."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-bottom: 15px;"
        )
        layout.addWidget(description)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        # Horse Selection
        self.horse_search_input = QLineEdit()
        self.horse_search_input.setPlaceholderText("Search for horse by name...")
        self.horse_search_input.textChanged.connect(self.search_timer.start)
        form_layout.addRow("Search Horse:", self.horse_search_input)

        self.horse_list_widget = QListWidget()
        self.horse_list_widget.setFixedHeight(150)
        self.horse_list_widget.itemClicked.connect(self._on_horse_selected)
        form_layout.addRow(self.horse_list_widget)

        # Date Range
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-30))
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
            QDateEdit, QLineEdit, QListWidget {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
                min-height: 22px;
            }}
            QDateEdit:focus, QLineEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QLabel {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
        """
        self.setStyleSheet(style_sheet)

    def load_horses(self):
        """Loads all active horses for the selection list."""
        try:
            self.all_horses = self.horse_controller.search_horses(status="all")
            self._filter_horse_list()
        except Exception as e:
            self.logger.error(f"Failed to load horses: {e}", exc_info=True)

    def _filter_horse_list(self):
        """Filters the horse list based on the search input."""
        search_text = self.horse_search_input.text().lower()
        self.horse_list_widget.clear()
        for horse in self.all_horses:
            if search_text in horse.horse_name.lower():
                item = QListWidgetItem(
                    f"{horse.horse_name} (Acct: {horse.account_number or 'N/A'})"
                )
                item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)
                self.horse_list_widget.addItem(item)

    def _on_horse_selected(self, item: QListWidgetItem):
        """Handles the selection of a horse from the list."""
        self.selected_horse_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Horse selected for report: ID {self.selected_horse_id}")

    def get_options(self) -> Dict:
        """Returns the currently selected report options."""
        return {
            "horse_id": self.selected_horse_id,
            "start_date": self.start_date_edit.date().toPython(),
            "end_date": self.end_date_edit.date().toPython(),
        }
