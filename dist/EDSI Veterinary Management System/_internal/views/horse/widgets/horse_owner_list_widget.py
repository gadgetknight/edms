# views/horse/widgets/horse_owner_list_widget.py

"""
EDSI Veterinary Management System - Horse Owner List Widget
Version: 1.0.1
Purpose: Custom QListWidget for displaying horse-owner associations with specific styling.
         Corrected AppConfig constant usage.
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
from PySide6.QtWidgets import QListWidget

# QColor might not be directly used if config provides strings, but good to keep if needed by palette
from PySide6.QtGui import QColor

# Corrected import: Import constants directly
from config.app_config import (
    DARK_BORDER,
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_PRIMARY_ACTION,
    DARK_ITEM_HOVER,
)


class HorseOwnerListWidget(QListWidget):
    """Custom list widget for displaying horse owners in the Owners tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {DARK_BORDER};
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                outline: none; border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px; border-bottom: 1px solid {DARK_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION}50; /* Using alpha for selection */
                color: #ffffff; /* Ensure text is readable on selection */
            }}
            QListWidget::item:hover:!selected {{
                background-color: {DARK_ITEM_HOVER};
            }}
            """
        )
