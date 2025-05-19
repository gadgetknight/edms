# views/auth/small_login_dialog.py

"""
EDSI Veterinary Management System - Small Login Dialog
Version: 1.1.6
Purpose: Provides a compact login dialog that appears over the splash screen.
         Uses user details dictionary returned by UserController.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.6 (2025-05-18):
    - Modified `_attempt_login` to use the dictionary of user details
      (user_id, is_active) returned by `UserController.validate_password`.
- v1.1.5 (2025-05-18):
    - Re-confirmed method call is `self.user_controller.validate_password`.
- v1.1.4 (2025-05-18):
    - (Incorrectly changed to check_password, now reverted)
- v1.1.3 (2025-05-18):
    - (Incorrectly changed to check_password)
- v1.1.2 (2025-05-18):
    - Added DARK_HEADER_FOOTER to the direct imports from config.app_config.
- v1.1.1 (2025-05-18):
    - Corrected how AppConfig color constants are imported and used.
- v1.1.0 (2025-05-16):
    - Updated to use centralized dark theme colors from AppConfig.
"""

import logging
from typing import Optional, Dict  # Added Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QApplication,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor, QIcon, QPixmap

from controllers.user_controller import UserController
from config.app_config import (
    AppConfig,
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_BORDER,
    DARK_PRIMARY_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DEFAULT_FONT_FAMILY,
    DARK_HEADER_FOOTER,
)


class SmallLoginDialog(QDialog):
    """A compact login dialog, typically shown over the splash screen."""

    login_successful = Signal(str)
    dialog_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_controller = UserController()

        self.setWindowTitle("EDSI Login")
        self._setup_palette()
        self._setup_ui()
        self.setFixedSize(380, 250)

    def _setup_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_INPUT_FIELD_BACKGROUND))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        title_label = QLabel("User Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {DARK_TEXT_PRIMARY};"
        )
        self.main_layout.addWidget(title_label)

        input_style = f"""
            QLineEdit {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
        """

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("User ID (e.g., TM)")
        self.user_id_input.setStyleSheet(input_style)
        self.main_layout.addWidget(self.user_id_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)
        self.main_layout.addWidget(self.password_input)

        self.password_input.returnPressed.connect(self._attempt_login)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Login")

        button_base_style = f"""
            QPushButton {{
                background-color: {DARK_BUTTON_BG};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {DARK_BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {QColor(DARK_BUTTON_HOVER).darker(110).name()};
            }}
            QPushButton:disabled {{
                background-color: {DARK_HEADER_FOOTER}; 
                color: {DARK_TEXT_TERTIARY};
            }}
        """
        ok_button.setStyleSheet(
            button_base_style.replace(DARK_BUTTON_BG, DARK_PRIMARY_ACTION).replace(
                DARK_TEXT_PRIMARY, "#FFFFFF"
            )
        )

        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setStyleSheet(button_base_style)

        self.button_box.accepted.connect(self._attempt_login)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.button_box)
        self.user_id_input.setFocus()

    def _attempt_login(self):
        user_id_input_val = self.user_id_input.text().strip().upper()
        password = self.password_input.text()

        if not user_id_input_val or not password:
            QMessageBox.warning(
                self, "Login Failed", "User ID and Password are required."
            )
            return

        # UserController.validate_password now returns a dictionary or None
        is_valid, message, user_details = self.user_controller.validate_password(
            user_id_input_val, password
        )

        if is_valid and user_details:  # user_details is now a dict
            self.logger.info(
                f"Password validation successful for user '{user_details['user_id']}'."
            )
            if user_details["is_active"]:
                self.logger.info(
                    f"User '{user_details['user_id']}' logged in successfully via small dialog."
                )
                self.login_successful.emit(user_details["user_id"])
            else:
                self.logger.warning(
                    f"Login attempt for inactive user '{user_details['user_id']}'."
                )
                QMessageBox.critical(
                    self,
                    "Login Failed",
                    f"User account '{user_details['user_id']}' is inactive.",
                )
        else:
            # If user_details is None (e.g. user not found), use the input user_id for logging
            log_user_id = user_details["user_id"] if user_details else user_id_input_val
            self.logger.warning(f"Login failed for user '{log_user_id}': {message}")
            QMessageBox.critical(self, "Login Failed", message)
            self.password_input.clear()
            self.password_input.setFocus()

    def reject(self):
        self.logger.debug("Login dialog rejected by user (Cancel or Esc).")
        self.dialog_closed.emit()
        super().reject()

    def accept(self):
        self.logger.debug("Login dialog accepted (likely after successful login).")
        self.dialog_closed.emit()
        super().accept()

    def closeEvent(self, event):
        self.logger.debug("Login dialog closed via window X button.")
        self.dialog_closed.emit()
        super().closeEvent(event)
