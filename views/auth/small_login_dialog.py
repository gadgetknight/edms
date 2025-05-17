# views/auth/small_login_dialog.py

"""
EDSI Veterinary Management System - Small Login Dialog
Version: 1.0.1
Purpose: Provides a compact dialog for username and password entry.
         Uses centralized AppConfig for dark theme colors.
Last Updated: May 16, 2025
Author: Claude Assistant

Changelog:
- v1.0.1 (2025-05-16): Updated to use centralized dark theme colors from AppConfig.
- v1.0.0 (2025-05-16): Initial implementation.
"""

import logging
import hashlib
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPalette, QColor

from config.database_config import db_manager
from models import User
from config.app_config import AppConfig  # Import AppConfig for colors


class SmallLoginDialog(QDialog):
    """A small dialog for username and password input."""

    login_successful = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setMinimumWidth(350)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Apply dark theme palette
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)

        # General styles for labels and specific input field styles
        dialog_styles = f"""
            QLabel {{ 
                color: {AppConfig.DARK_TEXT_SECONDARY}; 
                background-color: transparent; 
                padding-top: 3px; /* Align with input fields */
            }}
            QLineEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; 
                color: {AppConfig.DARK_TEXT_PRIMARY}; 
                border: 1px solid {AppConfig.DARK_BORDER}; 
                border-radius: 4px; 
                padding: 6px; 
                min-height: 20px;
            }}
            QLineEdit:focus {{ 
                border-color: {AppConfig.DARK_PRIMARY_ACTION}; 
            }}
        """
        self.setStyleSheet(dialog_styles)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        # Input field style is now part of dialog_styles or inherited via palette
        form_layout.addRow(QLabel("Username:"), self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow(QLabel("Password:"), self.password_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("Login")  # Check if button exists

        self.button_box.accepted.connect(self.handle_login_attempt)
        self.button_box.rejected.connect(self.reject)

        # Consistent button styling
        generic_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px;
                padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
            QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; }}
        """
        ok_button_specific_style = (
            generic_button_style
            + f"QPushButton {{ background-color: {AppConfig.DARK_SUCCESS_ACTION}; color: white; }}"
        )

        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                button.setStyleSheet(ok_button_specific_style)
            else:
                button.setStyleSheet(generic_button_style)

        layout.addWidget(self.button_box)
        self.username_input.setFocus()

    def handle_login_attempt(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self, "Login Failed", "Username and Password are required."
            )
            return

        is_valid, user_id_validated = self._validate_credentials(username, password)

        if is_valid:
            self.logger.info(
                f"User '{user_id_validated}' logged in successfully via small dialog."
            )
            self.login_successful.emit(user_id_validated)
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.username_input.setFocus()
            self.username_input.selectAll()

    def _validate_credentials(
        self, username_entered: str, password_entered: str
    ) -> tuple[bool, str | None]:
        session = None
        target_user_id = username_entered.upper()
        self.logger.debug(f"Attempting validation for user: {target_user_id}")
        try:
            session = db_manager.get_session()
            user = session.query(User).filter(User.user_id == target_user_id).first()
            if user:
                if user.is_active:
                    entered_password_hash = hashlib.sha256(
                        password_entered.lower().encode("utf-8")
                    ).hexdigest()
                    if entered_password_hash == user.password_hash:
                        self.logger.info(
                            f"Password validation successful for user '{user.user_id}'."
                        )
                        return True, user.user_id
                    else:
                        self.logger.warning(
                            f"Password hash mismatch for user '{user.user_id}'."
                        )
                        return False, None
                else:
                    self.logger.warning(f"User '{user.user_id}' is inactive.")
                    return False, None
            else:
                self.logger.warning(f"User '{target_user_id}' not found in database.")
                return False, None
        except Exception as e:
            self.logger.error(
                f"Error during credential validation for '{target_user_id}': {e}",
                exc_info=True,
            )
            return False, None
        finally:
            if session:
                db_manager.close_session()
