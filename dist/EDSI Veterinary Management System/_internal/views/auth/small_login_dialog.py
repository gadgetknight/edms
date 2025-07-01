# views/auth/small_login_dialog.py

"""
EDSI Veterinary Management System - Simplified Login Dialog
Version: 2.0.4
Purpose: Clean, simple login dialog using UserController for authentication.
         Ensures consistent authentication mechanism (bcrypt) across the application.
Last Updated: May 29, 2025
Author: Claude Assistant (Refactored by Gemini)

Changelog:
- v2.0.4 (2025-05-29):
    - Refactored to use UserController.authenticate_user() for login attempts.
    - Removed internal _authenticate_user and _verify_password methods.
    - Removed hashlib import and direct database session usage for authentication.
    - Login ID is now passed to UserController without uppercasing;
      controller handles case-insensitive lookup.
    - User feedback messages now sourced from UserController.
- v2.0.3 (2025-05-24):
    - Fixed RuntimeError: Internal C++ object already deleted
    - Added early return on successful login to prevent widget access after dialog closure
    - Added proper error handling for widget cleanup
- v2.0.2 (2025-05-24):
    - Updated database session handling for login attempts
    - Added last login timestamp update on successful authentication
- v2.0.1 (2025-05-24):
    - Fixed authentication to work with simplified database structure
    - Improved error handling and user feedback
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Removed UserController dependency and complex validation
    - Simplified to direct database authentication
    - Clean signal handling without over-engineering
    - Proper error handling and user feedback
    - Consistent dark theme styling
    - Focused on working login flow
    - Removed circular import issues
    - Clear separation of concerns
"""

import logging

# REMOVED: import hashlib - No longer used
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialogButtonBox,
    QHBoxLayout,  # Retained, though not explicitly used in this version's example layout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from config.app_config import AppConfig

# REMOVED: from config.database_config import get_db_session - Controller handles session
# REMOVED: from models.user_models import User - Controller returns user info
from controllers.user_controller import UserController  # ADDED


class SmallLoginDialog(QDialog):
    """
    Simple login dialog for user authentication.
    Displays over the splash screen and handles user login.
    """

    # Signals
    login_successful = Signal(str)  # Emits user_id on successful login
    dialog_closed = Signal()  # Emits when dialog is closed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_controller = UserController()  # ADDED UserController instance

        self.setWindowTitle("EDSI Login")
        self.setModal(True)
        self.setFixedSize(380, 250)

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup the login dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("User Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
        """
        )
        layout.addWidget(title_label)

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("Login ID")
        self.user_id_input.setMaxLength(20)
        layout.addWidget(self.user_id_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaxLength(255)  # Max length for input field
        layout.addWidget(self.password_input)

        self.password_input.returnPressed.connect(self._attempt_login)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Login")

        self.button_box.accepted.connect(self._attempt_login)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)
        self.user_id_input.setFocus()

    def _apply_theme(self):
        """Apply dark theme to the dialog"""
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

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
            QLabel {{
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
            QLineEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.DARK_BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {AppConfig.DARK_ITEM_HOVER};
            }}
            QPushButton[text="Login"] {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
            QPushButton[text="Login"]:hover {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION}dd; /* Assuming alpha modification if supported */
            }}
        """
        )

    def _attempt_login(self):
        """Attempt to authenticate the user using UserController"""
        login_id = self.user_id_input.text().strip()  # REMOVED .upper()
        password = self.password_input.text()

        if not login_id:
            self._show_error("Login ID is required.")
            self.user_id_input.setFocus()
            return

        if not password:
            self._show_error("Password is required.")
            self.password_input.setFocus()
            return

        # Authenticate user via UserController
        try:
            # UserController.authenticate_user returns -> Tuple[bool, str, Optional[Dict[str, Any]]]
            success, message, user_info = self.user_controller.authenticate_user(
                login_id, password
            )

            if success and user_info:
                actual_user_id = user_info.get(
                    "user_id", login_id
                )  # Use actual user_id from DB
                self.logger.info(f"User '{actual_user_id}' logged in successfully")
                # UserController's authenticate_user now handles updating last_login and committing
                self.login_successful.emit(actual_user_id)
                # self.accept() # No need to call accept() here, login_successful signal triggers closure in main.py
                return  # Exit immediately on success

            else:
                # Display the message from UserController (e.g., "Invalid login ID or password", "User inactive")
                self._show_error(
                    message or "Login failed. Please check your credentials."
                )
                self.logger.warning(
                    f"Failed login attempt for user input: {login_id}. Reason: {message}"
                )

        except Exception as e:  # Catch any unexpected errors from controller call
            self.logger.error(
                f"Login error during controller interaction: {e}", exc_info=True
            )
            self._show_error(
                "An unexpected error occurred during login. Please try again."
            )

        # Only clear password on failed login (we return early on success)
        try:
            self.password_input.clear()
            self.password_input.setFocus()
        except RuntimeError:
            self.logger.debug(
                "Password input widget might be deleted, skipping clear/focus."
            )

    # REMOVED: _authenticate_user(self, login_id: str, password: str) -> Optional[User]:
    # REMOVED: _verify_password(self, plain_password: str, password_hash: str) -> bool:

    def _show_error(self, message: str):
        """Show error message to user"""
        # Ensure widget exists before showing message box, in case dialog is closing.
        if self.isVisible():
            QMessageBox.critical(self, "Login Failed", message)
        else:
            self.logger.warning(
                f"Login dialog not visible, error not shown to user: {message}"
            )

    def reject(self):
        """Handle dialog rejection (Cancel button or Esc key)"""
        self.logger.debug("Login dialog cancelled by user")
        self.dialog_closed.emit()
        super().reject()

    # accept() is implicitly handled by login_successful signal flow in main.py;
    # direct call to self.accept() after emitting login_successful is removed
    # to let main.py manage the dialog closure after successful signal processing.
    # If accept() is needed for other QDialogButtonBox scenarios, it could be:
    # def accept(self):
    #     # This might be called if _attempt_login directly calls self.accept()
    #     # For now, _attempt_login calls return on success.
    #     self.logger.debug("Login dialog accepted (e.g. if OK directly called accept)")
    #     super().accept()

    def closeEvent(self, event):
        """Handle dialog close event (e.g., window 'X' button)"""
        # Check if login was successful; if so, accept() might have already been called
        # or login_successful emitted. If not, it's like a reject.
        self.logger.debug("Login dialog closed via closeEvent (e.g., X button)")
        self.dialog_closed.emit()  # Ensure dialog_closed is emitted
        super().closeEvent(event)
