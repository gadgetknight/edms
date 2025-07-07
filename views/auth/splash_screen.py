# views/auth/splash_screen.py

"""
EDSI Veterinary Management System - Image-Based Splash Screen with Interactive Areas
Version: 1.3.4
Purpose: Displays an image-based splash screen with clickable login/exit areas, and now includes application version and copyright display.
Last Updated: July 1, 2025
Author: Claude Assistant (Correcting user's v1.3.0, further modified by Gemini)

Changelog:
- v1.3.4 (2025-07-01):
    - Added a QLabel to the splash screen to display a copyright notice (e.g., "© 2025 EDSI. All rights reserved.").
    - Positioned the copyright label near the bottom-center of the splash image.
    - Styled the copyright label for visibility and theme consistency.
- v1.3.3 (2025-07-01):
    - Added a QLabel to the splash screen to display `AppConfig.APP_VERSION`.
    - Positioned the version label in the bottom-right corner of the splash image.
    - Styled the version label for visibility and theme consistency.
- v1.3.2 (2025-05-24):
    - Changed image_path construction in setup_splash_ui to use AppConfig.ASSETS_DIR
      resolving AttributeError for AppConfig.get_app_dir().
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
from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import (
    Qt,
    Signal,
    QSize,
    QRect,
    QTimer,
)
from PySide6.QtGui import QPixmap, QPalette, QColor, QFont


from config.app_config import AppConfig


class SplashScreen(QWidget):
    """EDSI splash screen that appears on startup, image-based with interactive areas."""

    login_requested = Signal()
    exit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.pixmap: Optional[QPixmap] = None
        self.image_label: Optional[QLabel] = None
        self.login_button_overlay: Optional[QPushButton] = None
        self.exit_button_overlay: Optional[QPushButton] = None
        self.version_label: Optional[QLabel] = None
        self.copyright_label: Optional[QLabel] = None  # NEW: Declare copyright label

        self.setup_splash_ui()

    def setup_splash_ui(self):
        try:
            # MODIFIED: Use AppConfig.ASSETS_DIR directly
            image_path = os.path.join(AppConfig.ASSETS_DIR, "splash_screen.jpg")
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

            # Add version label
            self.version_label = QLabel(
                f"Version {AppConfig.APP_VERSION}", self.image_label
            )
            self.version_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 9))
            self.version_label.setStyleSheet("color: white; background: rgba(0,0,0,0);")

            version_label_padding_x = 10
            version_label_padding_y = 10
            version_label_width = 100
            version_label_height = 20

            self.version_label.setGeometry(
                self.pixmap.width() - version_label_width - version_label_padding_x,
                self.pixmap.height() - version_label_height - version_label_padding_y,
                version_label_width,
                version_label_height,
            )
            self.version_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
            )

            # NEW: Add copyright label
            self.copyright_label = QLabel(
                "© 2025 EDSI. All rights reserved.", self.image_label
            )
            self.copyright_label.setFont(
                QFont(AppConfig.DEFAULT_FONT_FAMILY, 8)
            )  # Smaller font for copyright
            self.copyright_label.setStyleSheet(
                "color: lightgray; background: rgba(0,0,0,0);"
            )  # Lighter gray text

            # Position the copyright label (e.g., bottom-center)
            copyright_label_height = 15
            copyright_label_y_offset = 5  # Offset from bottom
            self.copyright_label.setGeometry(
                0,  # X position starts from left
                self.pixmap.height()
                - copyright_label_height
                - copyright_label_y_offset,
                self.pixmap.width(),  # Full width to center text
                copyright_label_height,
            )
            self.copyright_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom
            )

            login_coords = QRect(280, 340, 95, 35)
            exit_coords = QRect(380, 340, 95, 35)

            self.login_button_overlay = QPushButton(self.image_label)
            self.login_button_overlay.setGeometry(login_coords)
            self.login_button_overlay.setFlat(True)
            self.login_button_overlay.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; }"
            )
            self.login_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            self.login_button_overlay.clicked.connect(self.login_requested.emit)
            self.login_button_overlay.setToolTip("Login to EDSI System")

            self.exit_button_overlay = QPushButton(self.image_label)
            self.exit_button_overlay.setGeometry(exit_coords)
            self.exit_button_overlay.setFlat(True)
            self.exit_button_overlay.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; }"
            )
            self.exit_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
            self.exit_button_overlay.clicked.connect(self.exit_requested.emit)
            self.exit_button_overlay.setToolTip("Exit Application")

            v_layout = QVBoxLayout(self)
            v_layout.addWidget(self.image_label)
            v_layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(v_layout)

            self.logger.info("Splash screen UI setup complete.")

        except Exception as e:
            self.logger.error(f"Error setting up splash screen UI: {e}", exc_info=True)
            self._setup_fallback_ui()
            QTimer.singleShot(0, self.show)

    def _setup_fallback_ui(self):
        self.logger.info("Setting up fallback UI for splash screen.")
        if self.image_label:
            self.image_label.deleteLater()
            self.image_label = None
        if self.login_button_overlay:
            self.login_button_overlay.deleteLater()
            self.login_button_overlay = None
        if self.exit_button_overlay:
            self.exit_button_overlay.deleteLater()
            self.exit_button_overlay = None
        if self.version_label:
            self.version_label.deleteLater()
            self.version_label = None
        if self.copyright_label:  # NEW: Clean up copyright label too
            self.copyright_label.deleteLater()
            self.copyright_label = None

        current_layout = self.layout()
        if current_layout is not None:
            while current_layout.count():
                child = current_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        self.setFixedSize(350, 150)
        fallback_label = QLabel("EDSI Loading...", self)
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet(
            "background-color: #2D3748; color: white; font-size: 18px; padding: 20px; border-radius: 5px;"
        )
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(fallback_label)
        self.setLayout(main_layout)
        self.center_on_screen()

    def center_on_screen(self):
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            screen_geometry = primary_screen.availableGeometry()
            self.move(screen_geometry.center() - self.rect().center())
        else:
            self.logger.warning(
                "Primary screen not available for centering splash, using default position."
            )
            self.move(100, 100)

    def showEvent(self, event):
        self.logger.debug("Splash screen shown.")
        super().showEvent(event)

    def closeEvent(self, event):
        self.logger.debug("Splash screen closed.")
        super().closeEvent(event)
