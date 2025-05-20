# views/horse/widgets/horse_list_widget.py

"""
EDSI Veterinary Management System - Horse List Widget
Version: 1.0.1
Purpose: Custom QListWidget for displaying a list of horses with specific styling
         and item representation. Corrected AppConfig constant usage.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.0.1 (2025-05-18):
    - Corrected AppConfig constant usage. Imported constants directly instead of
      accessing them via the AppConfig class.
- v1.0.0 (2025-05-17):
    - Initial extraction from horse_unified_management.py.
"""

import logging
from typing import Optional
from datetime import date

from PySide6.QtWidgets import QListWidget, QVBoxLayout, QLabel, QWidget
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Corrected import: Import constants directly
from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_BORDER,
    DARK_PRIMARY_ACTION,
    DARK_ITEM_HOVER,
    DEFAULT_FONT_FAMILY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
)


class HorseListWidget(QListWidget):
    """Custom list widget styled for the dark theme and responsible for horse item rendering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: none; background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY}; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 15px; border-bottom: 1px solid {DARK_BORDER};
                min-height: 55px; background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION}40; /* RGBA */
                border-left: 3px solid {DARK_PRIMARY_ACTION}; color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
            """
        )

    def create_horse_list_item_widget(self, horse) -> QWidget:
        """
        Creates a custom widget for displaying a single horse item in the list.
        Args:
            horse: The horse data object (expected to have attributes like
                   horse_name, account_number, breed, color, sex, date_of_birth, location).
        Returns:
            QWidget: The custom widget for the list item.
        """
        widget = QWidget()
        # Ensure the widget itself doesn't override the transparent background needed for items
        widget.setStyleSheet(
            f"background-color: transparent; border: none; color: {DARK_TEXT_PRIMARY};"
        )
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(2)

        name_label = QLabel(horse.horse_name or "Unnamed Horse")
        name_label.setFont(QFont(DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold))
        name_label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )

        info_text = f"Acct: {horse.account_number or 'N/A'} | {horse.breed or 'N/A'}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )

        details_text = f"{horse.color or '?'} | {horse.sex or '?'} | {self._calculate_age(horse.date_of_birth)}"
        details_label = QLabel(details_text)
        details_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )

        location_text = horse.location.location_name if horse.location else "N/A"
        location_label = QLabel(f"📍 {location_text}")
        location_label.setStyleSheet(
            f"color: {DARK_TEXT_TERTIARY}; font-size: 10px; background: transparent;"
        )

        layout.addWidget(name_label)
        layout.addWidget(info_label)
        layout.addWidget(details_label)
        layout.addWidget(location_label)
        layout.addStretch()
        return widget

    def _calculate_age(self, birth_date_obj: Optional[date]) -> str:
        """
        Calculates the age of the horse based on the birth date.
        Args:
            birth_date_obj: The date of birth of the horse.
        Returns:
            str: A string representation of the horse's age.
        """
        if not birth_date_obj or not isinstance(birth_date_obj, date):
            # self.logger.warning(f"Invalid birth_date_obj for age calculation: {birth_date_obj}")
            return "Age N/A"
        try:
            today = date.today()
            age_val = (
                today.year
                - birth_date_obj.year
                - (
                    (today.month, today.day)
                    < (birth_date_obj.month, birth_date_obj.day)
                )
            )
            return f"{age_val} yr" if age_val == 1 else f"{age_val} yrs"
        except Exception as e:
            self.logger.error(
                f"Error calculating age for date {birth_date_obj}: {e}", exc_info=True
            )
            return "Age Error"
