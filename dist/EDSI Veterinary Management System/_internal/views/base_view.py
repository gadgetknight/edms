# views/base_view.py
"""
EDSI Veterinary Management System - Base View Class
Version: 1.3.7
Purpose: Provides a base class for all main views/screens in the application,
         handling common UI setup like dark theme and status messages.
Last Updated: July 1, 2025
Author: Gemini

Changelog:
- v1.3.7 (2025-07-01):
    - **BUG FIX**: Added missing `from config.app_config import AppConfig` import
      to resolve `NameError: name 'AppConfig' is not defined` when styling the
      copyright label in the status bar.
- v1.3.6 (2025-07-01):
    - Added a copyright QLabel to the permanent widgets of the QStatusBar,
      displaying "© 2025 EDSI. All rights reserved." at the bottom-right of all main screens.
    - Styled the copyright label for visibility and theme consistency.
- v1.3.5 (2025-06-14):
    - Enabled Rich Text formatting in the `show_question` method's QMessageBox
      to ensure HTML tags like `<b>` are rendered correctly.
- v1.3.4 (2025-06-13):
    - Reverted `show_info` and `show_question` to use the standard QMessageBox
      to fix application instability after closing dialogs.
    - Implemented direct button styling on QMessageBox to achieve the custom
      look without needing unstable custom dialog classes.
    - Removed dependencies on the deleted CustomInfoDialog and
      CustomQuestionDialog files.
- v1.3.3 (2025-06-13):
    - Modified `show_info` to use the new `CustomInfoDialog` for consistently
      styled dialog boxes, replacing the standard QMessageBox.
- v1.3.2 (2025-06-08):
    - Corrected the import path for CustomQuestionDialog to point to the
      `views.horse.widgets` sub-package, resolving the ModuleNotFoundError.
- v1.3.1 (2025-06-08):
    - Bug Fix: Changed the import for CustomQuestionDialog to a relative path.
- v1.3.0 (2025-06-08):
    - Refactored `show_question` to use a new `CustomQuestionDialog`.
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
    QDialog,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt, QTimer

from config.app_config import (  # Added AppConfig import
    AppConfig,  # Added AppConfig import
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

        # Add copyright label to status bar
        self.copyright_status_label = QLabel("© 2025 EDSI. All rights reserved.")
        self.copyright_status_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_TERTIARY}; margin-right: 5px;"
        )
        self.copyright_status_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 8))
        self.status_bar.addPermanentWidget(self.copyright_status_label)

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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        ok_button = msg_box.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        ok_button.setStyleSheet(
            f"""
            QPushButton {{
                border: 1px solid white; border-radius: 4px; padding: 8px 16px;
                min-width: 80px; font-weight: bold;
                background-color: {DARK_SUCCESS_ACTION}; color: white;
            }}
            QPushButton:hover {{ background-color: {QColor(DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        )
        msg_box.exec()

    def show_warning(self, title: str, message: str):
        self.logger.warning(f"Displaying Warning: {title} - {message}")
        QMessageBox.warning(self, title, message)

    def show_error(self, title: str, message: str):
        self.logger.error(f"Displaying Error: {title} - {message}")
        QMessageBox.critical(self, title, message)

    def show_question(self, title: str, message: str) -> bool:
        self.logger.info(f"Asking Question: {title} - {message}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setIcon(QMessageBox.Icon.Question)

        yes_button = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_button)

        yes_button.setStyleSheet(
            f"""
            QPushButton {{
                border: 1px solid white; border-radius: 4px; padding: 8px 16px;
                min-width: 80px; font-weight: bold;
                background-color: {DARK_SUCCESS_ACTION}; color: white;
            }}
            QPushButton:hover {{ background-color: {QColor(DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        )
        no_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid white; border-radius: 4px; padding: 8px 16px;
                min-width: 80px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
        """
        )

        msg_box.exec()
        return msg_box.clickedButton() == yes_button
