# views/auth/splash_screen.py

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from views.base_view import BaseView
from config.app_config import AppConfig


class SplashScreen(BaseView):
    """EDSI splash screen that appears on startup"""

    # Signal emitted when user presses any key or clicks
    splash_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_splash_ui()
        self.setup_timer()

    def setup_splash_ui(self):
        """Setup the splash screen UI"""
        self.set_title("EDSI Splash Screen")
        self.resize(600, 400)

        # Center the window on screen
        self.center_on_screen()

        # Create splash layout directly

        # Main splash layout
        splash_layout = QVBoxLayout(self.central_widget)
        splash_layout.setContentsMargins(20, 20, 20, 20)
        splash_layout.setSpacing(20)
        splash_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create main content frame
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        content_frame.setFixedSize(500, 300)
        content_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {AppConfig.SURFACE_COLOR};
                border: 2px solid {AppConfig.PRIMARY_COLOR};
                border-radius: 12px;
            }}
        """
        )

        content_layout = QVBoxLayout(content_frame)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)

        # Application title
        title_label = QLabel("EDSI")
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 36, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR};")
        content_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Veterinary Management System")
        subtitle_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 18)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {AppConfig.TEXT_COLOR};")
        content_layout.addWidget(subtitle_label)

        # Version info
        version_label = QLabel(f"Version {AppConfig.APP_VERSION}")
        version_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {AppConfig.TEXT_SECONDARY};")
        content_layout.addWidget(version_label)

        # Add some stretch
        content_layout.addStretch()

        # Press any key message
        instruction_label = QLabel("Press any key to continue...")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet(
            f"""
            color: {AppConfig.TEXT_SECONDARY};
            font-style: italic;
            font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
        """
        )
        content_layout.addWidget(instruction_label)

        # Add content frame to splash layout
        splash_layout.addWidget(content_frame)

        # Make window modal
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def center_on_screen(self):
        """Center the splash screen on the display"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
        )

    def setup_timer(self):
        """Setup auto-advance timer (optional)"""
        # Optional: Auto-advance after 3 seconds
        self.auto_advance_timer = QTimer()
        self.auto_advance_timer.timeout.connect(self.close_splash)
        self.auto_advance_timer.setSingleShot(True)
        self.auto_advance_timer.start(3000)  # 3 seconds

    def keyPressEvent(self, event):
        """Handle any key press"""
        self.close_splash()

    def mousePressEvent(self, event):
        """Handle mouse click"""
        self.close_splash()

    def close_splash(self):
        """Close splash screen and emit signal"""
        if hasattr(self, "auto_advance_timer"):
            self.auto_advance_timer.stop()
        self.splash_closed.emit()
        self.close()
