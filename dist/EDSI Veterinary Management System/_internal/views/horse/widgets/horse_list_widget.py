# views/horse/widgets/horse_list_widget.py
"""
EDSI Veterinary Management System - Horse List Widget
Version: 1.1.2
Purpose: Custom QListWidget for displaying a list of horses with specific styling
         and item representation. Corrected vertical text cutoff.
Last Updated: June 13, 2025
Author: Gemini

Changelog:
- v1.1.2 (2025-06-13):
    - Increased the minimum height of list items to 70px to provide more vertical padding and improve visual balance.
- v1.1.1 (2025-06-13):
    - Correctly fixed vertical text cutoff by setting the minimum height on the
      custom item widget directly, as the stylesheet height is ignored when
      using setItemWidget.
    - Removed ineffective min-height style from QListWidget::item stylesheet.
- v1.1.0 (2025-06-13):
    - Increased list item min-height to 80px to fix vertical text cutoff after content simplification.
- v1.0.9 (2025-06-13):
    - Fixed vertical text cutoff by increasing the min-height of list items in the stylesheet to 70px.
- v1.0.8 (2025-06-13):
    - Simplified the list item to display only the horse's name and account number.
    - Removed breed, color, sex, age, and location from the list item display.
    - Set word wrap on the horse name to prevent it from being cut off.
    - Reduced the minimum height of list items to 55px to better fit the reduced content.
- v1.0.7 (2025-06-10):
    - Increased `min-height` of list items in the stylesheet to 70px to
      definitively prevent text from being cut off.
- v1.0.6 (2025-06-10):
    - Increased the minimum height of list items to 75px to
      provide more vertical space and prevent text clipping.
- v1.0.5 (2025-06-10):
    - Adjusted vertical margins and spacing in the custom item widget to
      prevent text from being cut off at the bottom.
- v1.0.4 (2025-06-10):
    - Adjusted vertical margins and spacing in the custom item widget to
      prevent text from being cut off at the bottom.
- v1.0.3 (2025-06-08):
    - Re-implemented `mouseDoubleClickEvent` to more reliably emit the
      `itemDoubleClicked` signal, fixing the double-click-to-edit feature.
- v1.0.2 (2025-06-08):
    - Bug Fix: Overrode `mouseDoubleClickEvent` to ensure the `itemDoubleClicked`
      signal is emitted correctly, even when using custom item widgets.
- v1.0.1 (2025-05-18):
    - Corrected AppConfig constant usage.
- v1.0.0 (2025-05-17):
    - Initial extraction from horse_unified_management.py.
"""

import logging
from typing import Optional
from datetime import date

from PySide6.QtWidgets import QListWidget, QVBoxLayout, QLabel, QWidget
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtCore import Qt

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
                background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION}40; /* RGBA */
                border-left: 3px solid {DARK_PRIMARY_ACTION};
                color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
            """
        )

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Overrides the default double-click handler to ensure the itemDoubleClicked
        signal is emitted reliably, even when using custom widgets.
        """
        item = self.itemAt(event.pos())
        if item:
            self.logger.debug(
                f"Double click detected on item for horse ID: {item.data(Qt.ItemDataRole.UserRole)}"
            )
            self.itemDoubleClicked.emit(item)
        # We do not call the super() implementation, as we are handling the event completely.
        # This prevents any potential conflicts.

    def create_horse_list_item_widget(self, horse) -> QWidget:
        """
        Creates a custom widget for displaying a single horse item in the list.
        Args:
            horse: The horse data object.
        Returns:
            QWidget: The custom widget for the list item.
        """
        widget = QWidget()
        widget.setMinimumHeight(70)  # Set height on the widget itself
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
        name_label.setWordWrap(True)

        info_text = f"Acct: {horse.account_number or 'N/A'}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )

        layout.addWidget(name_label)
        layout.addWidget(info_label)
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
