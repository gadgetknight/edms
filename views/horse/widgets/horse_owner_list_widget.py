# views/horse/widgets/horse_owner_list_widget.py

"""
EDSI Veterinary Management System - Horse Owner List Widget
Version: 1.0.0
Purpose: Custom QListWidget for displaying horse-owner associations with specific styling.
         Extracted from horse_unified_management.py.
Last Updated: May 17, 2025
Author: Claude Assistant
"""

import logging
from PySide6.QtWidgets import QListWidget
from PySide6.QtGui import (
    QColor,
)  # QColor might not be directly used if AppConfig provides strings

from config.app_config import AppConfig


class HorseOwnerListWidget(QListWidget):
    """Custom list widget for displaying horse owners in the Owners tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                outline: none; border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px; border-bottom: 1px solid {AppConfig.DARK_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION}50; /* Using alpha for selection */
                color: #ffffff; /* Ensure text is readable on selection */
            }}
            QListWidget::item:hover:!selected {{ 
                background-color: {AppConfig.DARK_ITEM_HOVER}; 
            }}
            """
        )
