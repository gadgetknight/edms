# views/auth/splash_screen.py

"""
EDSI Veterinary Management System - Image-Based Splash Screen with Interactive Areas
Version: 1.3.1
Purpose: Displays an image-based splash screen with clickable login/exit areas.
         Corrected signal names to match usage in main.py.
Last Updated: May 18, 2025
Author: Claude Assistant (Correcting user's v1.3.0)

Changelog:
- v1.3.1 (2025-05-18):
    - Renamed signal `login_area_clicked` to `login_requested`.
    - Renamed signal `exit_area_clicked` to `exit_requested`.
- v1.3.0 (2025-05-16): (User's Base Version)
    - Implemented interactive image splash screen.
    - Loads splash_screen.jpg from assets.
    - Overlays transparent QPushButtons for "Login" and "Exit" areas based on coordinates.
    - Emits `login_area_clicked` or `exit_area_clicked` signals.
    - Removed old timer and generic key/mouse press handlers.
- v1.2.0 (2025-05-15): Attempted image display (placeholder).
- v1.1.0 (2025-05-12): Original text-based splash screen.
"""

import os
import logging
from typing import Optional  # Added for type hinting Optional[QPixmap]

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import (
    Qt,
    Signal,
    QSize,
    QRect,
    QTimer,
)  # Added QTimer for potential error fallback
from PySide6.QtGui import QPixmap, QPalette, QColor

# from views.base_view import BaseView # Not used in user's v1.3.0
from config.app_config import AppConfig


class SplashScreen(QWidget):
    """EDSI splash screen that appears on startup, image-based with interactive areas."""

    # --- CORRECTED SIGNAL NAMES ---
    login_requested = Signal()
    exit_requested = Signal()
    # --- END CORRECTION ---

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.pixmap: Optional[QPixmap] = None  # Added type hint
        self.image_label: Optional[QLabel] = None
        self.login_button_overlay: Optional[QPushButton] = None
        self.exit_button_overlay: Optional[QPushButton] = None

        self.setup_splash_ui()

    def setup_splash_ui(self):
        try:
            image_path = os.path.join(
                AppConfig.get_app_dir(), "assets", "splash_screen.jpg"
            )
            self.logger.info(f"Attempting to load splash image from: {image_path}")

            if not os.path.exists(image_path):
                self.logger.error(
                    f"Splash screen image not found at {image_path}. Using fallback."
                )
                self._setup_fallback_ui()
                return

            self.pixmap = QPixmap(image_path)

            if self.pixmap.isNull():
                self.logger.error(
                    f"CRITICAL: Could not load splash image from {image_path}. Using fallback."
                )
                self._setup_fallback_ui()
                return

            self.setFixedSize(self.pixmap.size())
            self.center_on_screen()

            self.image_label = QLabel(self)
            self.image_label.setPixmap(self.pixmap)
            self.image_label.setGeometry(
                0, 0, self.pixmap.width(), self.pixmap.height()
            )
            self.image_label.setScaledContents(True)

            # Coordinates for buttons (as provided by user in v1.3.0)
            login_coords = QRect(280, 340, 95, 35)
            exit_coords = QRect(380, 340, 95, 35)

            self.login_button_overlay = QPushButton(self.image_label)
            self.login_button_overlay.setGeometry(login_coords)
            self.login_button_overlay.setFlat(True)
            self.login_button_overlay.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; }"
            )
            self.login_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            # --- EMIT CORRECTED SIGNAL ---
            self.login_button_overlay.clicked.connect(self.login_requested.emit)
            # --- END CORRECTION ---
            self.login_button_overlay.setToolTip("Login to EDSI System")

            self.exit_button_overlay = QPushButton(self.image_label)
            self.exit_button_overlay.setGeometry(exit_coords)
            self.exit_button_overlay.setFlat(True)
            self.exit_button_overlay.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; }"
            )
            self.exit_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            # --- EMIT CORRECTED SIGNAL ---
            self.exit_button_overlay.clicked.connect(self.exit_requested.emit)
            # --- END CORRECTION ---
            self.exit_button_overlay.setToolTip("Exit Application")

            # Ensure image_label fills the SplashScreen QWidget
            # This was present in user's v1.3.0, so keeping it.
            v_layout = QVBoxLayout(self)
            v_layout.addWidget(self.image_label)
            v_layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(
                v_layout
            )  # This might not be strictly necessary if image_label.setGeometry covers it.

            self.logger.info("Splash screen UI setup complete.")

        except Exception as e:
            self.logger.error(f"Error setting up splash screen UI: {e}", exc_info=True)
            self._setup_fallback_ui()  # Ensure fallback is called on any error during setup
            QTimer.singleShot(
                0, self.show
            )  # Attempt to show fallback if main setup fails

    def _setup_fallback_ui(self):
        """Sets up a simple text-based fallback if the image cannot be loaded."""
        self.logger.info("Setting up fallback UI for splash screen.")
        # Ensure previous UI elements are cleared if any partial setup occurred
        if self.image_label:
            self.image_label.deleteLater()
            self.image_label = None
        if self.login_button_overlay:
            self.login_button_overlay.deleteLater()
            self.login_button_overlay = None
        if self.exit_button_overlay:
            self.exit_button_overlay.deleteLater()
            self.exit_button_overlay = None

        # Clear existing layout if one was set
        current_layout = self.layout()
        if current_layout is not None:
            # Properly remove and delete widgets from the layout
            while current_layout.count():
                child = current_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            # Or, simply delete the old layout
            # sip.delete(current_layout) # If using sip
            # For PySide6, just setting a new layout should be fine, or clear items.

        self.setFixedSize(350, 150)  # Adjusted size for fallback
        fallback_label = QLabel("EDSI Loading...", self)
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet(
            "background-color: #2D3748; color: white; font-size: 18px; padding: 20px; border-radius: 5px;"
        )
        main_layout = QVBoxLayout(self)  # Create a new layout
        main_layout.addWidget(fallback_label)
        self.setLayout(main_layout)
        self.center_on_screen()

    def center_on_screen(self):
        # Using QApplication.primaryScreen() is more robust
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            screen_geometry = primary_screen.availableGeometry()
            self.move(screen_geometry.center() - self.rect().center())
        else:
            self.logger.warning(
                "Primary screen not available for centering splash, using default position."
            )
            # Fallback position if no screen info (e.g., very early init or specific environments)
            self.move(100, 100)

    def showEvent(self, event):
        """Log when the splash screen is shown."""
        self.logger.debug("Splash screen shown.")
        super().showEvent(event)

    def closeEvent(self, event):
        """Log when the splash screen is closed."""
        self.logger.debug("Splash screen closed.")
        super().closeEvent(event)
