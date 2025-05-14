# views/base_view.py

"""
EDSI Veterinary Management System - Base View
Version: 1.1.1
Purpose: Base class for all application windows using PySide6.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.1.1 (2025-05-12): Removed unsupported box-shadow property.
  - Removed 'box-shadow' from input field focus style in apply_styling.
- v1.1.0 (2025-05-12): Migrated to PySide6
  - Changed all imports from PyQt6 to PySide6.
  - Ensured compatibility with PySide6 signal/slot syntax and widgets.
- v1.0.1 (2025-05-12): Fixed central widget initialization (PyQt6)
- v1.0.0 (2025-05-12): Initial implementation (PyQt6)
"""

import logging
from PySide6.QtWidgets import (  # Changed import from PyQt6 to PySide6
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal  # Changed import from PyQt6 to PySide6
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QScreen,
)  # Changed import from PyQt6 to PySide6

from config.app_config import AppConfig


class BaseView(QMainWindow):
    """Base class for all application windows using PySide6."""

    # Signal emitted when window is closing
    closing = Signal()

    def __init__(self, parent=None):
        """Initializes the BaseView."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create central widget first - standard practice
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Call setup_ui which should be overridden by subclasses
        self.setup_ui()
        # Apply common styling after the UI structure might be set
        self.apply_styling()

    def setup_ui(self):
        """
        Setup basic UI structure.
        This method is intended to be overridden by subclasses
        to set their own layouts and widgets within self.central_widget.
        """
        pass  # Base implementation does nothing

    def apply_styling(self):
        """Apply consistent styling to the window and common elements."""
        self.setMinimumSize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(AppConfig.BACKGROUND_COLOR))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {AppConfig.BACKGROUND_COLOR}; /* Fallback */
            }}
            QFrame {{
                /* Default Frame style - can be overridden by specific frames */
                background-color: {AppConfig.SURFACE_COLOR};
                border: 1px solid #dee2e6;
                border-radius: 5px; /* Slightly smaller radius */
            }}
            QLabel {{
                color: {AppConfig.TEXT_COLOR};
                font-family: "{AppConfig.DEFAULT_FONT_FAMILY}"; /* Ensure quotes for font names */
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                background-color: transparent; /* Ensure labels have transparent background */
                padding: 1px; /* Prevent text clipping */
            }}
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: "{AppConfig.DEFAULT_FONT_FAMILY}";
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                font-weight: bold; /* Make buttons stand out more */
                min-height: 32px; /* Ensure minimum button height */
            }}
            QPushButton:hover {{
                background-color: #005a9e; /* Darker blue on hover */
            }}
            QPushButton:pressed {{
                background-color: #004578; /* Even darker blue when pressed */
            }}
            QPushButton:disabled {{
                background-color: #adb5bd; /* Grey out disabled buttons */
                color: #f8f9fa;
            }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
                 background-color: #ffffff;
                 border: 1px solid #ced4da;
                 border-radius: 4px;
                 padding: 5px 8px; /* Standard padding */
                 font-family: "{AppConfig.DEFAULT_FONT_FAMILY}";
                 font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                 color: {AppConfig.TEXT_COLOR};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
                /* Removed unsupported box-shadow property */
            }}
            QComboBox::drop-down {{
                border: none; /* Style dropdown arrow */
            }}
            QComboBox::down-arrow {{
                 /* You might need an image or leave it default */
            }}
            QStatusBar {{
                font-family: "{AppConfig.DEFAULT_FONT_FAMILY}";
                font-size: {AppConfig.SMALL_FONT_SIZE}pt;
            }}
        """
        )

    def set_title(self, title):
        """Set window title prefixed with the application name."""
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {title}")

    # --- Message Box Helpers ---
    def show_error(self, title, message):
        """Show error message box."""
        self.logger.error(f"Displaying Error: {title} - {message}")
        QMessageBox.critical(self, title, str(message))

    def show_warning(self, title, message):
        """Show warning message box."""
        self.logger.warning(f"Displaying Warning: {title} - {message}")
        QMessageBox.warning(self, title, str(message))

    def show_info(self, title, message):
        """Show information message box."""
        self.logger.info(f"Displaying Info: {title} - {message}")
        QMessageBox.information(self, title, str(message))

    def show_question(self, title, message):
        """Show question dialog and return True if Yes is clicked, False otherwise."""
        self.logger.info(f"Asking Question: {title} - {message}")
        reply = QMessageBox.question(
            self,
            title,
            str(message),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # --- Window Positioning ---
    def center_on_screen(self):
        """Center the window on the screen where the mouse cursor is."""
        try:
            screen = self.screen()
            if not screen:
                # Use QApplication.primaryScreen() in PySide6
                screen = QApplication.primaryScreen()

            if screen:
                screen_geometry = screen.availableGeometry()
                window_geometry = self.frameGeometry()
                center_point = screen_geometry.center()
                window_geometry.moveCenter(center_point)
                self.move(window_geometry.topLeft())
            else:
                # Fallback if screen detection fails
                self.logger.warning("Could not detect screen for centering.")
                # Apply a default position
                self.move(100, 100)
        except Exception as e:
            self.logger.error(f"Could not center window: {e}")
            self.move(100, 100)

    # --- Event Handling ---
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.debug(f"Close event triggered for {self.__class__.__name__}")
        self.closing.emit()
        super().closeEvent(event)
