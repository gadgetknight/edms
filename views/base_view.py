# views/base_view.py

"""
EDSI Veterinary Management System - Base View
Version: 1.0.1
Purpose: Base class for all application windows with improved widget initialization.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.1 (2025-05-12): Fixed central widget initialization
  - Ensured central_widget is created properly in __init__
  - Added explicit central widget creation for PyQt6 compatibility
  - Fixed attribute name consistency across all views
- v1.0.0 (2025-05-12): Initial implementation
  - Created base class for all application windows
  - Implemented common UI elements and styling
  - Added message box helpers and utility methods
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from config.app_config import AppConfig
import logging


class BaseView(QMainWindow):
    """Base class for all application windows"""

    # Signal emitted when window is closing
    closing = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create central widget first
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.setup_ui()
        self.apply_styling()

    def setup_ui(self):
        """Setup basic UI structure - to be overridden by subclasses"""
        # Subclasses should override this method to set their own layouts
        pass

    def apply_styling(self):
        """Apply consistent styling to the window"""
        # Set window properties
        self.setMinimumSize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)

        # Set background color
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {AppConfig.BACKGROUND_COLOR};
            }}
            QFrame {{
                background-color: {AppConfig.SURFACE_COLOR};
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }}
            QLabel {{
                color: {AppConfig.TEXT_COLOR};
                font-family: {AppConfig.DEFAULT_FONT_FAMILY};
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
            }}
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: {AppConfig.DEFAULT_FONT_FAMILY};
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
            }}
            QPushButton:hover {{
                background-color: #106ebe;
            }}
            QPushButton:pressed {{
                background-color: #005a9e;
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
            }}
        """
        )

    def set_title(self, title):
        """Set window title with application name"""
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {title}")

    def show_error(self, title, message):
        """Show error message box"""
        QMessageBox.critical(self, title, message)

    def show_warning(self, title, message):
        """Show warning message box"""
        QMessageBox.warning(self, title, message)

    def show_info(self, title, message):
        """Show information message box"""
        QMessageBox.information(self, title, message)

    def show_question(self, title, message):
        """Show question dialog"""
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def center_on_screen(self):
        """Center the window on the display"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
        )

    def closeEvent(self, event):
        """Handle window close event"""
        self.closing.emit()
        super().closeEvent(event)
