# views/auth/login_screen.py

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from views.base_view import BaseView
from config.app_config import AppConfig
import logging


class LoginScreen(BaseView):
    """User ID entry screen for authentication"""

    # Signal emitted when login is successful
    login_successful = pyqtSignal(str)  # Passes user_id

    # Signal emitted when user wants to exit
    exit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_login_ui()
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_login_ui(self):
        """Setup the login screen UI"""
        self.set_title("Enter User ID")
        self.resize(400, 300)
        self.center_on_screen()

        # Create login layout directly

        # Main login layout
        login_layout = QVBoxLayout(self.central_widget)
        login_layout.setContentsMargins(20, 20, 20, 20)
        login_layout.setSpacing(20)

        # Create login form frame
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        form_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {AppConfig.SURFACE_COLOR};
                border: 1px solid {AppConfig.PRIMARY_COLOR};
                border-radius: 8px;
                padding: 20px;
            }}
        """
        )

        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        # Title
        title_label = QLabel("EDSI Login")
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR};")
        form_layout.addWidget(title_label)

        # Add some space
        spacer1 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        form_layout.addItem(spacer1)

        # User ID label
        user_id_label = QLabel("User ID:")
        user_id_label.setStyleSheet(
            f"""
            font-size: {AppConfig.DEFAULT_FONT_SIZE + 2}pt;
            font-weight: bold;
            color: {AppConfig.TEXT_COLOR};
        """
        )
        form_layout.addWidget(user_id_label)

        # User ID input
        self.user_id_input = QLineEdit()
        self.user_id_input.setFixedHeight(40)
        self.user_id_input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: {AppConfig.DEFAULT_FONT_SIZE + 2}pt;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
            }}
        """
        )
        self.user_id_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.user_id_input)

        # Add some space
        spacer2 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        form_layout.addItem(spacer2)

        # Button layout
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("Enter")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setMinimumHeight(40)
        self.login_button.setMinimumWidth(100)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.handle_exit)
        self.exit_button.setMinimumHeight(40)
        self.exit_button.setMinimumWidth(100)
        self.exit_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
            QPushButton:hover {{
                background-color: #5a6268;
            }}
        """
        )

        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.exit_button)
        button_layout.addStretch()

        form_layout.addLayout(button_layout)

        # Instructions
        instruction_label = QLabel("Enter your User ID and press Enter")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet(
            f"""
            color: {AppConfig.TEXT_SECONDARY};
            font-style: italic;
            font-size: {AppConfig.SMALL_FONT_SIZE + 1}pt;
        """
        )
        form_layout.addWidget(instruction_label)

        # Add the form frame to main layout
        login_layout.addStretch()
        login_layout.addWidget(form_frame)
        login_layout.addStretch()

        # Set focus to input field
        self.user_id_input.setFocus()

        # Make window modal
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def center_on_screen(self):
        """Center the login screen on the display"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
        )

    def handle_login(self):
        """Handle login attempt"""
        user_id = self.user_id_input.text().strip().upper()

        if not user_id:
            self.show_error("Error", "Please enter a User ID")
            self.user_id_input.setFocus()
            return

        # Validate user ID (basic check - should be enhanced with actual authentication)
        if self.validate_user_id(user_id):
            self.logger.info(f"User '{user_id}' logged in successfully")
            self.login_successful.emit(user_id)
            self.close()
        else:
            self.show_error("Invalid User ID", f"User ID '{user_id}' not found")
            self.user_id_input.clear()
            self.user_id_input.setFocus()

    def validate_user_id(self, user_id):
        """Validate user ID against database"""
        # TODO: Implement actual database validation
        # For now, accept any non-empty user ID
        # In production, this should check against the users table
        from config.database_config import db_manager
        from models import User

        try:
            session = db_manager.get_session()
            user = session.query(User).filter(User.user_id == user_id).first()
            session.close()
            return user is not None and user.is_active
        except Exception as e:
            self.logger.error(f"Error validating user: {e}")
            return False

    def handle_exit(self):
        """Handle exit button click"""
        self.exit_requested.emit()
        self.close()

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Allow ESC to exit
        if event.key() == Qt.Key.Key_Escape:
            self.handle_exit()
        else:
            super().keyPressEvent(event)
