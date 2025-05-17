# views/auth/splash_screen.py

"""
EDSI Veterinary Management System - Image-Based Splash Screen with Interactive Areas
Version: 1.3.0
Purpose: Displays an image-based splash screen with clickable login/exit areas.
Last Updated: May 16, 2025
Author: Claude Assistant

Changelog:
- v1.3.0 (2025-05-16): Implemented interactive image splash screen.
  - Loads splash_screen.jpg from assets.
  - Overlays transparent QPushButtons for "Login" and "Exit" areas based on coordinates.
  - Emits `login_area_clicked` or `exit_area_clicked` signals.
  - Removed old timer and generic key/mouse press handlers.
- v1.2.0 (2025-05-15): Attempted image display (placeholder).
- v1.1.0 (2025-05-12): Original text-based splash screen.
"""

import os
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QPixmap, QPalette, QColor

from views.base_view import (
    BaseView,
)  # BaseView might not be ideal if we want a raw QWidget
from config.app_config import AppConfig


class SplashScreen(QWidget):  # Changed from BaseView to QWidget for more control
    """EDSI splash screen that appears on startup, image-based with interactive areas."""

    login_area_clicked = Signal()
    exit_area_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.pixmap = None
        self.setup_splash_ui()

    def setup_splash_ui(self):
        image_path = os.path.join(
            AppConfig.get_app_dir(), "assets", "splash_screen.jpg"
        )
        self.pixmap = QPixmap(image_path)

        if self.pixmap.isNull():
            self.logger.error(
                f"CRITICAL: Could not load splash image from {image_path}. Using fallback."
            )
            self.resize(300, 100)
            fallback_label = QLabel("EDSI Loading...", self)
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet(
                "background-color: #2b2b2b; color: white; font-size: 18px; padding: 20px;"
            )
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(fallback_label)
            self.center_on_screen()
            return

        self.setFixedSize(self.pixmap.size())
        self.center_on_screen()

        # Background label for the image
        self.image_label = QLabel(self)
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setGeometry(0, 0, self.pixmap.width(), self.pixmap.height())

        # Coordinates for buttons (as provided by user)
        # Login Button: X=460, Y=690, Width=110, Height=40
        # Exit Button: X=590, Y=690, Width=110, Height=40

        login_coords = QRect(550, 690, 180, 40)
        exit_coords = QRect(760, 690, 180, 40)

        self.login_button_overlay = QPushButton(
            self.image_label
        )  # Parent to image_label
        self.login_button_overlay.setGeometry(login_coords)
        self.login_button_overlay.setFlat(True)  # Makes it look less like a button
        self.login_button_overlay.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; }"
        )
        self.login_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button_overlay.clicked.connect(self.login_area_clicked.emit)
        self.login_button_overlay.setToolTip("Login to EDSI System")

        self.exit_button_overlay = QPushButton(
            self.image_label
        )  # Parent to image_label
        self.exit_button_overlay.setGeometry(exit_coords)
        self.exit_button_overlay.setFlat(True)
        self.exit_button_overlay.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; }"
        )
        self.exit_button_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_button_overlay.clicked.connect(self.exit_area_clicked.emit)
        self.exit_button_overlay.setToolTip("Exit Application")

        # No main layout needed if we are just placing buttons on an image label
        # The image_label itself will be the only child of the SplashScreen QWidget.
        # However, to ensure image_label fills the SplashScreen QWidget:
        v_layout = QVBoxLayout(self)
        v_layout.addWidget(self.image_label)
        v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(v_layout)

    def center_on_screen(self):
        if self.screen():  # Check if screen is available
            screen_geometry = self.screen().availableGeometry()
            self.move(
                (screen_geometry.width() - self.width()) // 2,
                (screen_geometry.height() - self.height()) // 2,
            )
        else:  # Fallback for headless environments or early init
            self.logger.warning(
                "Screen not available for centering splash, using default position."
            )
            self.move(100, 100)

    # We don't want generic key/mouse presses to close it anymore
    # def keyPressEvent(self, event):
    #     pass # Or handle specific keys if needed, e.g. ESC for exit_area_clicked

    # def mousePressEvent(self, event):
    #     pass
