# views/auth/small_login_dialog.py

"""
EDSI Veterinary Management System - Simplified Login Dialog
Version: 2.0.3
Purpose: Clean, simple login dialog with proper authentication flow.
         Removed over-engineered complexity and focused on stable login process.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
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
import hashlib
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialogButtonBox,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from config.app_config import AppConfig
from config.database_config import get_db_session
from models.user_models import User


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

        # Title
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

        # User ID input
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("Login ID")
        self.user_id_input.setMaxLength(20)
        layout.addWidget(self.user_id_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaxLength(255)
        layout.addWidget(self.password_input)

        # Connect Enter key to login
        self.password_input.returnPressed.connect(self._attempt_login)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # Customize buttons
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Login")

        # Connect signals
        self.button_box.accepted.connect(self._attempt_login)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

        # Set focus to user ID input
        self.user_id_input.setFocus()

    def _apply_theme(self):
        """Apply dark theme to the dialog"""
        # Set palette
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

        # Apply stylesheet
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
                background-color: {AppConfig.DARK_PRIMARY_ACTION}dd;
            }}
        """
        )

    def _attempt_login(self):
        """Attempt to authenticate the user"""
        login_id = self.user_id_input.text().strip().upper()
        password = self.password_input.text()

        # Validate input
        if not login_id:
            self._show_error("Login ID is required.")
            self.user_id_input.setFocus()
            return

        if not password:
            self._show_error("Password is required.")
            self.password_input.setFocus()
            return

        # Authenticate user
        try:
            user = self._authenticate_user(login_id, password)
            if user:
                if user.is_active:
                    self.logger.info(f"User '{login_id}' logged in successfully")

                    # Update last login
                    user.update_last_login()

                    # Commit the session to save last login update
                    session = get_db_session()
                    try:
                        session.commit()
                    except Exception as e:
                        self.logger.warning(f"Could not update last login: {e}")
                        session.rollback()
                    finally:
                        session.close()

                    # Emit success signal and return immediately
                    self.login_successful.emit(user.user_id)
                    return  # Exit immediately on success - don't clear password

                else:
                    self._show_error(f"User account '{login_id}' is inactive.")
                    self.logger.warning(f"Login attempt for inactive user: {login_id}")
            else:
                self._show_error("Invalid login ID or password.")
                self.logger.warning(f"Failed login attempt for user: {login_id}")

        except Exception as e:
            self.logger.error(f"Login error: {e}", exc_info=True)
            self._show_error("An error occurred during login. Please try again.")

        # Only clear password on failed login (we return early on success)
        try:
            self.password_input.clear()
            self.password_input.setFocus()
        except RuntimeError:
            # Widget already deleted, ignore
            self.logger.debug("Password input widget already deleted, skipping clear")

    def _authenticate_user(self, login_id: str, password: str) -> Optional[User]:
        """
        Authenticate user against database.

        Args:
            login_id: User login ID
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        session = get_db_session()
        try:
            # Find user by login ID
            user = session.query(User).filter(User.user_id == login_id).first()

            if user and self._verify_password(password, user.password_hash):
                return user

            return None

        except Exception as e:
            self.logger.error(f"Database error during authentication: {e}")
            return None
        finally:
            session.close()

    def _verify_password(self, plain_password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            plain_password: Plain text password
            password_hash: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        # Simple SHA-256 hashing for Phase 1
        # In production, use bcrypt or similar
        computed_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return computed_hash == password_hash

    def _show_error(self, message: str):
        """Show error message to user"""
        QMessageBox.critical(self, "Login Failed", message)

    def reject(self):
        """Handle dialog rejection (Cancel button or Esc key)"""
        self.logger.debug("Login dialog cancelled by user")
        self.dialog_closed.emit()
        super().reject()

    def accept(self):
        """Handle dialog acceptance"""
        self.logger.debug("Login dialog accepted")
        self.dialog_closed.emit()
        super().accept()

    def closeEvent(self, event):
        """Handle dialog close event"""
        self.logger.debug("Login dialog closed via close button")
        self.dialog_closed.emit()
        super().closeEvent(event)
