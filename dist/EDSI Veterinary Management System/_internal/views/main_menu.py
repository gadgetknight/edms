# views/main_menu.py

"""
EDSI Veterinary Management System - Main Menu
Version: 1.0.2
Purpose: Modern unified main menu with consolidated management screens.
         Fixed PyQt6 to PySide6 imports for consistency.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
- v1.0.2 (2025-05-24):
    - Fixed imports from PyQt6 to PySide6 for consistency with rest of application
    - Changed pyqtSignal to Signal from PySide6.QtCore
- v1.0.1 (2025-05-12): Updated for unified management approach
  - Replaced separate horse operations (Add, Edit, Delete) with single "Horse Management"
  - Removed horse_review_update_selected, add_new_horse_selected, delete_horse_selected signals
  - Added horse_management_selected signal for unified interface
  - Updated menu options to reflect modern management screens
  - Simplified menu structure for better user experience
- v1.0.0 (2025-05-12): Initial implementation
  - Created complete main menu matching COBOL layout
  - Implemented all menu option signals
  - Added keyboard navigation support
  - Included proper styling and layout
"""

from PySide6.QtWidgets import (
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
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from views.base_view import BaseView
from config.app_config import AppConfig
import logging


class MainMenu(BaseView):
    """Primary menu screen with unified management approach"""

    # Signals for menu selections
    horse_management_selected = Signal()  # Option 1 - Unified horse operations
    table_maintenance_selected = Signal()  # Option 2
    print_reports_selected = Signal()  # Option 3
    owners_ar_selected = Signal()  # Option 4
    system_utilities_selected = Signal()  # Option 5
    mass_update_selected = Signal()  # Option 6
    logoff_exit_selected = Signal()  # Option 9
    logoff_no_exit_selected = Signal()  # Option X

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
            color: {AppConfig.DARK_PRIMARY_ACTION};
            padding: 10px;
        """
        )

        # User info
        user_info_label = QLabel(f"Current User: {self.current_user}")
        user_info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_info_label.setStyleSheet(
            f"""
            color: {AppConfig.DARK_TEXT_SECONDARY};
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
                color: {AppConfig.DARK_TEXT_PRIMARY};
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

        # Define menu options (number, text, signal) - Updated for unified approach
        menu_options = [
            ("1.", "Horse Management", self.horse_management_selected),
            ("2.", "Table Maintenance", self.table_maintenance_selected),
            ("3.", "Print Reports & Billing", self.print_reports_selected),
            ("4.", "Owners A/R", self.owners_ar_selected),
            ("5.", "System Utilities", self.system_utilities_selected),
            ("6.", "Mass Update", self.mass_update_selected),
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
                    background-color: {AppConfig.DARK_DANGER_ACTION};
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
                    background-color: {AppConfig.DARK_PRIMARY_ACTION};
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
            color: {AppConfig.DARK_TEXT_SECONDARY};
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

        # Map keys to signals - Updated for unified approach
        key_mappings = {
            "1": self.horse_management_selected,
            "2": self.table_maintenance_selected,
            "3": self.print_reports_selected,
            "4": self.owners_ar_selected,
            "5": self.system_utilities_selected,
            "6": self.mass_update_selected,
            "9": self.logoff_exit_selected,
            "X": self.logoff_no_exit_selected,
        }

        if key in key_mappings:
            self.logger.info(f"Menu option {key} selected via keyboard")
            key_mappings[key].emit()
        else:
            super().keyPressEvent(event)
