# views/base_view.py
"""
EDSI Veterinary Management System - Base View Class
Version: 1.2.0
Purpose: Provides a base class for all main views/screens in the application,
         handling common UI setup like dark theme and status messages.
Last Updated: June 7, 2025
Author: Gemini

Changelog:
- v1.2.0 (2025-06-07):
    - Added global stylesheet rules for QMessageBox buttons to provide
      a consistent, "boxed-in" style with a green "Yes" button.
- v1.1.8 (2025-05-21):
    - Added `DARK_TEXT_TERTIARY` to the imports from `config.app_config`.
- v1.1.7 (2025-05-21):
    - Added `DARK_PRIMARY_ACTION` to the imports.
- v1.1.6 (2025-05-21):
    - Added debug print statements for troubleshooting.
- v1.1.5 (2025-05-20):
    - Added detailed logging to BaseView.setup_ui.
- v1.1.4 (2025-05-18):
    - Ensured central_widget always has a layout.
- v1.1.3 (2025-05-17):
    - Added placeholder for status_bar if not created by subclass.
- v1.1.2 (2025-05-16):
    - Added show_confirmation_dialog and show_error_dialog methods.
- v1.1.1 (2025-05-15):
    - Standardized status message methods.
- v1.1.0 (2025-05-14):
    - Initial implementation with dark theme palette and global styles.
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QApplication,
    QMessageBox,
    QStatusBar,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt, QTimer

from config.app_config import (
    DARK_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_BORDER,
    DARK_WIDGET_BACKGROUND,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DEFAULT_FONT_FAMILY,
    DARK_HEADER_FOOTER,
    DARK_PRIMARY_ACTION,
    DARK_ITEM_HOVER,
    DARK_TEXT_TERTIARY,
    DARK_SUCCESS_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
)


class BaseView(QMainWindow):
    """
    Base class for all main views/screens in the application.
    Handles common setup like dark theme, status messages, and basic layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"BaseView __init__ for {self.__class__.__name__} started.")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.logger.info(
            f"BaseView __init__ for {self.__class__.__name__}: central_widget created."
        )

        if hasattr(self, "setup_ui") and callable(self.setup_ui):
            self.logger.info(
                f"BaseView __init__ for {self.__class__.__name__}: Calling overridden setup_ui()."
            )
            self.setup_ui()
        else:
            self.logger.info(
                f"BaseView __init__ for {self.__class__.__name__}: Using default BaseView setup_ui()."
            )
            default_layout = QVBoxLayout(self.central_widget)
            default_label = QLabel(f"Welcome to {self.__class__.__name__}")
            default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            default_layout.addWidget(default_label)
            self.logger.info(
                f"BaseView __init__ for {self.__class__.__name__}: Default QVBoxLayout set on central_widget."
            )

        if self.__class__.__name__ == "HorseUnifiedManagement":
            print(
                f"--- BASEVIEW.__INIT__: BEFORE apply_dark_theme. self.tab_widget is {type(getattr(self, 'tab_widget', None))} ---"
            )

        self.apply_dark_theme_palette_and_global_styles()

        if self.__class__.__name__ == "HorseUnifiedManagement":
            print(
                f"--- BASEVIEW.__INIT__: AFTER apply_dark_theme. self.tab_widget is {type(getattr(self, 'tab_widget', None))} ---"
            )

        if not hasattr(self, "status_bar") or self.status_bar is None:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.logger.info(
                f"BaseView __init__ for {self.__class__.__name__}: Default QStatusBar created and set."
            )
        self.update_status("Ready", 0)

        self.logger.info(f"BaseView __init__ for {self.__class__.__name__} finished.")

    def set_title(self, title: str):
        self.setWindowTitle(title)

    def apply_dark_theme_palette_and_global_styles(self):
        if self.__class__.__name__ == "HorseUnifiedManagement":
            print(
                f"--- BASEVIEW.APPLY_DARK_THEME: START. self.tab_widget is {type(getattr(self, 'tab_widget', None))} ---"
            )

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_HIGHLIGHT_BG))
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(DARK_HIGHLIGHT_TEXT)
        )

        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(DARK_TEXT_TERTIARY),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(DARK_TEXT_TERTIARY),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            QColor(DARK_TEXT_TERTIARY),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Base,
            QColor(DARK_HEADER_FOOTER),
        )

        QApplication.setPalette(palette)
        QApplication.instance().setPalette(palette)

        QApplication.instance().setStyleSheet(
            f"""
            QMainWindow, QDialog, QWidget {{
                font-family: "{DEFAULT_FONT_FAMILY}";
                font-size: 13px;
                color: {DARK_TEXT_PRIMARY};
                background-color: {DARK_BACKGROUND};
            }}
            QToolTip {{
                color: {DARK_TEXT_PRIMARY};
                background-color: {DARK_WIDGET_BACKGROUND};
                border: 1px solid {DARK_BORDER};
                padding: 4px;
                border-radius: 3px;
            }}
            QStatusBar {{
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_SECONDARY};
                border-top: 1px solid {DARK_BORDER};
            }}
            QStatusBar QLabel {{
                color: {DARK_TEXT_SECONDARY};
                background-color: transparent;
                padding: 0 2px;
            }}
            QMenuBar {{
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_PRIMARY};
                border-bottom: 1px solid {DARK_BORDER};
            }}
            QMenuBar::item {{
                spacing: 3px;
                padding: 4px 10px;
                background: transparent;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background: {DARK_ITEM_HOVER};
            }}
            QMenuBar::item:pressed {{
                background: {DARK_PRIMARY_ACTION};
            }}
            QMenu {{
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 20px 5px 20px;
            }}
            QMenu::item:selected {{
                background-color: {DARK_HIGHLIGHT_BG};
                color: {DARK_HIGHLIGHT_TEXT};
            }}
            QMenu::separator {{
                height: 1px;
                background: {DARK_BORDER};
                margin-left: 5px;
                margin-right: 5px;
            }}
            QScrollBar:vertical {{
                border: 1px solid {DARK_BORDER};
                background: {DARK_WIDGET_BACKGROUND};
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {DARK_TEXT_SECONDARY};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: 1px solid {DARK_BORDER};
                background: {DARK_WIDGET_BACKGROUND};
                height: 12px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {DARK_TEXT_SECONDARY};
                min-width: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            /* Styling for QMessageBox buttons */
            QMessageBox QPushButton {{
                background-color: {DARK_BUTTON_BG};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {DARK_BUTTON_HOVER};
            }}
            QMessageBox QPushButton[text="&Yes"] {{
                background-color: {DARK_SUCCESS_ACTION};
                color: white;
            }}
            QMessageBox QPushButton[text="&Yes"]:hover {{
                background-color: {QColor(DARK_SUCCESS_ACTION).lighter(115).name()};
            }}
        """
        )
        self.logger.info(
            f"Dark theme palette and global styles applied for {self.__class__.__name__}."
        )
        if self.__class__.__name__ == "HorseUnifiedManagement":
            print(
                f"--- BASEVIEW.APPLY_DARK_THEME: END. self.tab_widget is {type(getattr(self, 'tab_widget', None))} ---"
            )

    def update_status(self, message: str, timeout: int = 5000):
        """Displays a message on the status bar for a specified duration."""
        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage(message, timeout)
            self.logger.info(f"Status update: {message}")
        else:
            self.logger.warning(
                f"Attempted to update status for {self.__class__.__name__}, but no status_bar attribute found or it is None."
            )

    def show_info(self, title: str, message: str):
        self.logger.info(f"Displaying Info: {title} - {message}")
        QMessageBox.information(self, title, message)

    def show_warning(self, title: str, message: str):
        self.logger.warning(f"Displaying Warning: {title} - {message}")
        QMessageBox.warning(self, title, message)

    def show_error(self, title: str, message: str):
        self.logger.error(f"Displaying Error: {title} - {message}")
        QMessageBox.critical(self, title, message)

    def show_question(self, title: str, message: str) -> bool:
        self.logger.info(f"Asking Question: {title} - {message}")
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
