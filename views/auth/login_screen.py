# views/auth/login_screen.py

"""
EDSI Veterinary Management System - Login Screen
Version: 1.1.2
Purpose: Handles user authentication (username and password).
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.1.2 (2025-05-12): Debug password validation and fix styling.
  - Added detailed logging in `validate_credentials` to compare input hash vs stored hash.
  - Removed unsupported 'box-shadow' property from input field focus style.
- v1.1.1 (2025-05-12): Fixed TypeError on layout initialization.
  - Changed layout creation in setup_ui from `QVBoxLayout(parent)`
    to `QVBoxLayout()` followed by `parent.setLayout()`.
- v1.1.0 (2025-05-12): Refactored for Username/Password and PySide6
- v1.0.0 (2025-05-12): Initial implementation (PyQt6, User ID only)
"""

import logging
import hashlib
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QScreen,
)  # Added imports for styling if needed

from views.base_view import BaseView
from config.app_config import AppConfig
from config.database_config import db_manager
from models import User


class LoginScreen(BaseView):
    """User login screen for authentication with username and password."""

    login_successful = Signal(str)
    exit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        # Apply specific palette/styling for this screen if needed,
        # otherwise it inherits from BaseView
        self.apply_login_screen_styling()

    def apply_login_screen_styling(self):
        """Apply styles specific to the Login Screen, potentially overriding BaseView."""
        # Example: Set a specific background if different from BaseView
        # palette = self.palette()
        # palette.setColor(QPalette.ColorRole.Window, QColor("#e9ecef")) # Light grey example
        # self.setPalette(palette)
        # self.setAutoFillBackground(True)
        pass  # No specific overrides for now, using BaseView style

    def setup_ui(self):
        """Setup the login screen UI elements."""
        self.set_title("Login")
        self.setMinimumSize(450, 400)
        self.center_on_screen()

        # Main login layout for the central widget
        login_layout = QVBoxLayout()
        self.central_widget.setLayout(login_layout)  # Correct way to set layout

        login_layout.setContentsMargins(30, 30, 30, 30)
        login_layout.setSpacing(20)
        login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Login form frame
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        # Use object name for more specific styling if needed later
        form_frame.setObjectName("LoginFormFrame")
        form_frame.setStyleSheet(
            f"""
            #LoginFormFrame {{
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 30px;
                max-width: 400px;
            }}
            """
        )

        form_layout = QVBoxLayout(form_frame)  # Layout for the frame's content
        form_layout.setSpacing(15)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_label = QLabel(AppConfig.APP_NAME)
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"color: {AppConfig.PRIMARY_COLOR}; margin-bottom: 5px; background: transparent;"
        )
        form_layout.addWidget(title_label)

        # Version Label
        version_label = QLabel(f"Version {AppConfig.APP_VERSION}")
        version_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 10)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(
            f"color: {AppConfig.TEXT_SECONDARY}; margin-bottom: 20px; background: transparent;"
        )
        form_layout.addWidget(version_label)

        # Username label and input
        username_label = QLabel("Username:")
        username_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(40)
        self.username_input.setStyleSheet(self.get_input_style())  # Apply input style
        self.username_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.username_input)

        # Password label and input
        password_label = QLabel("Password:")
        password_label.setStyleSheet(self.get_label_style())
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setFixedHeight(40)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.get_input_style())  # Apply input style
        self.password_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.password_input)

        # Spacer
        spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        form_layout.addItem(spacer)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setMinimumHeight(40)
        self.login_button.setStyleSheet(self.get_button_style(AppConfig.PRIMARY_COLOR))

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.handle_exit)
        self.exit_button.setMinimumHeight(40)
        self.exit_button.setStyleSheet(self.get_button_style(AppConfig.SECONDARY_COLOR))

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.exit_button)
        form_layout.addLayout(button_layout)

        # Add the form frame to the main layout
        login_layout.addWidget(form_frame)

        # Set focus
        self.username_input.setFocus()

        # Set modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def get_label_style(self):
        """Returns the standard style for labels."""
        # Ensure background is transparent to inherit window background
        return f"""
            QLabel {{
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                font-weight: bold;
                color: {AppConfig.TEXT_COLOR};
                margin-bottom: 2px;
                background-color: transparent;
            }}
        """

    def get_input_style(self):
        """Returns the standard style for input fields, removing box-shadow."""
        # Inherits from BaseView stylesheet, but we define focus explicitly here
        # to ensure box-shadow is removed from this specific context too.
        return f"""
            QLineEdit {{
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                background-color: white;
                color: {AppConfig.TEXT_COLOR}; /* Ensure text color is set */
            }}
            QLineEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
                /* Removed unsupported box-shadow */
            }}
        """

    def get_button_style(self, background_color, hover_color=None):
        """Returns the standard style for buttons."""
        # Calculate hover color if not provided
        if hover_color is None:
            try:
                r = int(background_color[1:3], 16)
                g = int(background_color[3:5], 16)
                b = int(background_color[5:7], 16)
                hover_color = f"#{max(0, r-20):02x}{max(0, g-20):02x}{max(0, b-20):02x}"
            except:
                hover_color = background_color

        return f"""
            QPushButton {{
                background-color: {background_color};
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-family: "{AppConfig.DEFAULT_FONT_FAMILY}";
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {background_color};
            }}
            QPushButton:disabled {{
                background-color: #adb5bd;
                color: #f8f9fa;
            }}
        """

    def handle_login(self):
        """Handle login attempt using username and password."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.show_warning("Login Failed", "Please enter a username.")
            self.username_input.setFocus()
            return
        if not password:
            self.show_warning("Login Failed", "Please enter a password.")
            self.password_input.setFocus()
            return

        is_valid, user_id = self.validate_credentials(username, password)

        if is_valid:
            self.logger.info(f"User '{user_id}' logged in successfully")
            self.login_successful.emit(user_id)
            self.close()
        else:
            self.show_error("Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.username_input.setFocus()
            self.username_input.selectAll()

    def validate_credentials(self, username, password):
        """Validate username and password against the database."""
        session = None
        target_user_id = username.upper()  # Standardize username for query
        self.logger.debug(f"Attempting validation for user: {target_user_id}")
        try:
            session = db_manager.get_session()
            user = session.query(User).filter(User.user_id == target_user_id).first()

            if user:
                self.logger.debug(
                    f"User found in DB: ID={user.user_id}, Active={user.is_active}"
                )
                if user.is_active:
                    # Hash the entered password using SHA-256
                    entered_password_hash = hashlib.sha256(
                        password.encode("utf-8")
                    ).hexdigest()

                    # --- DEBUG LOGGING START ---
                    self.logger.debug(f"Comparing Hashes for user '{user.user_id}':")
                    self.logger.debug(f"  Entered Hash: {entered_password_hash}")
                    self.logger.debug(f"  Stored Hash : {user.password_hash}")
                    # --- DEBUG LOGGING END ---

                    # Compare the hash with the stored hash
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
            self.show_error(
                "Login Error", "An error occurred during login. Please check logs."
            )
            return False, None
        finally:
            if session:
                db_manager.close_session()

    def handle_exit(self):
        """Handle exit button click."""
        self.logger.info("Exit requested from login screen.")
        self.exit_requested.emit()
        self.close()

    def keyPressEvent(self, event):
        """Handle key press events (e.g., ESC to exit)."""
        if event.key() == Qt.Key.Key_Escape:
            self.handle_exit()
        else:
            super().keyPressEvent(event)

    # --- Message Box Helpers (Inherited from BaseView) ---
    # No need to override if BaseView uses PySide6 QMessageBox correctly.
    # def show_error(self, title, message): ...
    # def show_warning(self, title, message): ...
    # def show_info(self, title, message): ...
