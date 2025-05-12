# views/main_menu.py

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from views.base_view import BaseView
from config.app_config import AppConfig
import logging


class MainMenu(BaseView):
    """Primary menu screen - matches the COBOL main menu layout"""

    # Signals for menu selections
    horse_review_update_selected = pyqtSignal()  # Option 1
    add_new_horse_selected = pyqtSignal()  # Option 2
    delete_horse_selected = pyqtSignal()  # Option 3
    table_maintenance_selected = pyqtSignal()  # Option 4
    print_reports_selected = pyqtSignal()  # Option 5
    owners_ar_selected = pyqtSignal()  # Option 6
    system_utilities_selected = pyqtSignal()  # Option 7
    mass_update_selected = pyqtSignal()  # Option 8
    logoff_exit_selected = pyqtSignal()  # Option 9
    logoff_no_exit_selected = pyqtSignal()  # Option X

    def __init__(self, current_user=None):
        self.current_user = current_user or "Unknown"
        super().__init__()
        self.setup_main_menu_ui()
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_main_menu_ui(self):
        """Setup the main menu UI"""
        self.set_title("Primary Menu")
        self.resize(700, 600)
        self.center_on_screen()

        # Header section
        self.setup_header()

        # Main menu options
        self.setup_menu_options()

        # Footer section
        self.setup_footer()

    def setup_header(self):
        """Setup header with title and user info"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        # Main title
        title_label = QLabel("EDSI Primary Menu")
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"""
            color: {AppConfig.PRIMARY_COLOR};
            padding: 10px;
        """
        )

        # User info
        user_info_label = QLabel(f"Current User: {self.current_user}")
        user_info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_info_label.setStyleSheet(
            f"""
            color: {AppConfig.TEXT_SECONDARY};
            font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
            padding: 5px;
        """
        )

        header_layout.addWidget(title_label)
        header_layout.addWidget(user_info_label)

        # Set up the main window layout instead of using the base view methods
        if not hasattr(self, "main_layout"):
            self.main_layout = QVBoxLayout(self.central_widget)
            self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.main_layout.addWidget(header_frame)

    def setup_menu_options(self):
        """Setup main menu options grid"""
        # Create menu group box
        menu_group = QGroupBox("Select an option:")
        menu_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-size: {AppConfig.DEFAULT_FONT_SIZE + 2}pt;
                font-weight: bold;
                color: {AppConfig.TEXT_COLOR};
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }}
        """
        )

        # Create grid layout for menu options
        menu_layout = QGridLayout(menu_group)
        menu_layout.setSpacing(15)
        menu_layout.setContentsMargins(20, 20, 20, 20)

        # Define menu options (number, text, signal)
        menu_options = [
            ("1.", "Review/Update Horse Info", self.horse_review_update_selected),
            ("2.", "Add New Horse", self.add_new_horse_selected),
            ("3.", "Delete Horse", self.delete_horse_selected),
            ("4.", "Table Maintenance", self.table_maintenance_selected),
            ("5.", "Print Reports & Billing", self.print_reports_selected),
            ("6.", "Owners A/R", self.owners_ar_selected),
            ("7.", "System Utilities", self.system_utilities_selected),
            ("8.", "Mass Update", self.mass_update_selected),
            ("9.", "Logoff & Exit", self.logoff_exit_selected),
            ("X.", "Logoff, No Exit", self.logoff_no_exit_selected),
        ]

        # Create buttons for each option
        self.menu_buttons = {}
        row = 0
        col = 0
        max_cols = 2

        for number, text, signal in menu_options:
            button = self.create_menu_button(number, text, signal)
            menu_layout.addWidget(button, row, col)
            self.menu_buttons[number] = button

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Add the menu group to content area
        self.main_layout.addWidget(menu_group, 1)  # Take up most space

    def create_menu_button(self, number, text, signal):
        """Create a styled menu button"""
        button = QPushButton(f"{number} {text}")
        button.setMinimumHeight(50)
        button.setMinimumWidth(280)

        # Special styling for exit options
        if number in ["9.", "X."]:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {AppConfig.SECONDARY_COLOR};
                    color: white;
                    border: none;
                    padding: 10px;
                    text-align: left;
                    font-size: {AppConfig.DEFAULT_FONT_SIZE + 1}pt;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: #5a6268;
                }}
                QPushButton:pressed {{
                    background-color: #495057;
                }}
            """
            )
        else:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {AppConfig.PRIMARY_COLOR};
                    color: white;
                    border: none;
                    padding: 10px;
                    text-align: left;
                    font-size: {AppConfig.DEFAULT_FONT_SIZE + 1}pt;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: #106ebe;
                }}
                QPushButton:pressed {{
                    background-color: #005a9e;
                }}
            """
            )

        button.clicked.connect(lambda checked, s=signal: s.emit())
        return button

    def setup_footer(self):
        """Setup footer with instructions"""
        footer_frame = QFrame()
        footer_layout = QHBoxLayout(footer_frame)

        instruction_label = QLabel(
            "Select an option by clicking or pressing the corresponding number/letter"
        )
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet(
            f"""
            color: {AppConfig.TEXT_SECONDARY};
            font-style: italic;
            font-size: {AppConfig.SMALL_FONT_SIZE + 1}pt;
            padding: 10px;
        """
        )

        footer_layout.addWidget(instruction_label)
        self.main_layout.addWidget(footer_frame)

    def center_on_screen(self):
        """Center the main menu on the display"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
        )

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for menu options"""
        key = event.text().upper()

        # Map keys to signals
        key_mappings = {
            "1": self.horse_review_update_selected,
            "2": self.add_new_horse_selected,
            "3": self.delete_horse_selected,
            "4": self.table_maintenance_selected,
            "5": self.print_reports_selected,
            "6": self.owners_ar_selected,
            "7": self.system_utilities_selected,
            "8": self.mass_update_selected,
            "9": self.logoff_exit_selected,
            "X": self.logoff_no_exit_selected,
        }

        if key in key_mappings:
            self.logger.info(f"Menu option {key} selected via keyboard")
            key_mappings[key].emit()
        else:
            super().keyPressEvent(event)
