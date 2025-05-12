"""
EDSI Veterinary Management System - Horse Main Screen
Version: 1.0.0
Purpose: Search, select, and navigate to specific horse records for review/update operations.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.0 (2025-05-12): Initial implementation
  - Created horse search and selection interface
  - Implemented real-time search by name and account number
  - Added active/inactive filter toggle (F4)
  - Included navigation keys (F=First, N=Next, P=Previous, S=Search)
  - Added double-click and Enter key horse selection
  - Created proper list display with horse information
  - Implemented scroll capabilities for large horse lists
  - Added keyboard shortcuts for navigation
"""

# views/horse/horse_main_screen.py

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from views.base_view import BaseView
from config.app_config import AppConfig
from controllers.horse_controller import HorseController
import logging


class HorseMainScreen(BaseView):
    """Horse selection screen for review/update operations"""

    # Signals
    horse_selected = pyqtSignal(int)  # Emitted when horse is selected (passes horse_id)
    horse_edit_requested = pyqtSignal(int)  # Emitted when horse edit is requested
    exit_requested = pyqtSignal()  # Emitted when user exits

    def __init__(self, current_user=None):
        self.current_user = current_user or "ADMIN"
        self.controller = HorseController()
        self.horses_list = []
        self.current_search = ""
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        super().__init__()
        self.setup_horse_main_ui()
        self.load_horses()

        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_horse_main_ui(self):
        """Setup the horse main screen UI"""
        self.set_title("Horse Review/Update - Select Horse")
        self.resize(800, 600)
        self.center_on_screen()

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header section
        self.setup_header()

        # Search section
        self.setup_search_section()

        # Horse list section
        self.setup_horse_list_section()

        # Status and navigation section
        self.setup_status_section()

        # Buttons section
        self.setup_buttons_section()

        # Add sections to main layout
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(self.search_frame)
        main_layout.addWidget(self.list_group, 1)  # Take up most space
        main_layout.addWidget(self.status_frame)
        main_layout.addWidget(self.buttons_frame)

    def setup_header(self):
        """Setup header with title and current status"""
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)

        # Title
        title_label = QLabel("Horse Review/Update")
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR}; padding: 10px;")

        # Current user info
        user_label = QLabel(f"Current User: {self.current_user}")
        user_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_label.setStyleSheet(f"color: {AppConfig.TEXT_SECONDARY}; padding: 10px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(user_label)

    def setup_search_section(self):
        """Setup search controls"""
        self.search_frame = QFrame()
        search_layout = QHBoxLayout(self.search_frame)
        search_layout.setContentsMargins(10, 5, 10, 5)

        # Search label
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold;")

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter horse name or account number...")
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
            }}
        """
        )
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # Active filter checkbox
        self.active_only_checkbox = QCheckBox("Active Only")
        self.active_only_checkbox.setChecked(True)
        self.active_only_checkbox.stateChanged.connect(self.on_filter_changed)
        self.active_only_checkbox.setStyleSheet("font-weight: bold;")

        # Clear search button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_search)
        self.clear_button.setMinimumWidth(80)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)  # Take up most space
        search_layout.addWidget(self.active_only_checkbox)
        search_layout.addWidget(self.clear_button)

    def setup_horse_list_section(self):
        """Setup horse list display"""
        self.list_group = QGroupBox("Select a Horse")
        list_layout = QVBoxLayout(self.list_group)
        list_layout.setContentsMargins(10, 15, 10, 10)

        # Create horse list widget
        self.horse_list = QListWidget()
        self.horse_list.setStyleSheet(
            f"""
            QListWidget {{
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: #e9ecef;
            }}
        """
        )

        # Connect double-click event
        self.horse_list.itemDoubleClicked.connect(self.on_horse_double_clicked)
        self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)

        list_layout.addWidget(self.horse_list)

    def setup_status_section(self):
        """Setup status and navigation info"""
        self.status_frame = QFrame()
        status_layout = QHBoxLayout(self.status_frame)

        # Horses count
        self.count_label = QLabel("0 horses found")
        self.count_label.setStyleSheet(f"color: {AppConfig.TEXT_SECONDARY};")

        # Navigation instructions
        nav_label = QLabel(
            "Navigation: F=First, N=Next, P=Previous, S=Search, F4=Toggle Filter"
        )
        nav_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        nav_label.setStyleSheet(
            f"color: {AppConfig.TEXT_SECONDARY}; font-style: italic;"
        )

        status_layout.addWidget(self.count_label)
        status_layout.addWidget(nav_label)

    def setup_buttons_section(self):
        """Setup action buttons"""
        self.buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(self.buttons_frame)
        buttons_layout.setContentsMargins(20, 10, 20, 10)

        # Add stretch to center buttons
        buttons_layout.addStretch()

        # Select button
        self.select_button = QPushButton("Select Horse (Enter)")
        self.select_button.setMinimumSize(150, 40)
        self.select_button.clicked.connect(self.select_horse)
        self.select_button.setDefault(True)
        self.select_button.setEnabled(False)  # Disabled until selection

        # Exit button
        self.exit_button = QPushButton("Exit (X)")
        self.exit_button.setMinimumSize(100, 40)
        self.exit_button.clicked.connect(self.exit_screen)
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

        buttons_layout.addWidget(self.select_button)
        buttons_layout.addWidget(self.exit_button)
        buttons_layout.addStretch()

    def on_search_text_changed(self, text):
        """Handle search text changes with delayed search"""
        self.current_search = text
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay

    def on_filter_changed(self):
        """Handle active filter change"""
        self.perform_search()

    def perform_search(self):
        """Perform the actual search"""
        search_term = self.current_search.strip()
        active_only = self.active_only_checkbox.isChecked()

        self.logger.info(
            f"Searching horses: '{search_term}', active_only={active_only}"
        )

        # Search horses
        self.horses_list = self.controller.search_horses(search_term, active_only)
        self.populate_horse_list()

    def load_horses(self):
        """Load all horses initially"""
        self.logger.info("Loading all horses")
        self.horses_list = self.controller.search_horses("", active_only=True)
        self.populate_horse_list()

    def populate_horse_list(self):
        """Populate the horse list widget"""
        self.horse_list.clear()

        for horse in self.horses_list:
            # Create display text
            display_text = f"{horse.horse_name}"
            if horse.account_number:
                display_text += f" (Acct: {horse.account_number})"
            if horse.breed:
                display_text += f" - {horse.breed}"
            if horse.color:
                display_text += f", {horse.color}"
            if horse.species:
                display_text += f" [{horse.species.species_name}]"

            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)
            self.horse_list.addItem(item)

        # Update count
        self.update_count_label()

    def update_count_label(self):
        """Update the horses count label"""
        count = len(self.horses_list)
        if count == 1:
            self.count_label.setText("1 horse found")
        else:
            self.count_label.setText(f"{count} horses found")

    def on_selection_changed(self):
        """Handle selection changes"""
        current_item = self.horse_list.currentItem()
        self.select_button.setEnabled(current_item is not None)

    def on_horse_double_clicked(self, item):
        """Handle double-click on horse item"""
        self.select_horse()

    def select_horse(self):
        """Select the currently highlighted horse"""
        current_item = self.horse_list.currentItem()
        if not current_item:
            self.show_warning("No Selection", "Please select a horse from the list.")
            return

        horse_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Horse selected: ID {horse_id}")
        self.horse_edit_requested.emit(horse_id)

    def clear_search(self):
        """Clear search and reload all horses"""
        self.search_input.clear()
        self.current_search = ""
        self.load_horses()

    def exit_screen(self):
        """Exit horse main screen"""
        self.logger.info("Exiting horse main screen")
        self.exit_requested.emit()
        self.close()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.select_horse()
        elif key == Qt.Key.Key_X:
            self.exit_screen()
        elif key == Qt.Key.Key_F:
            # Go to first item
            if self.horse_list.count() > 0:
                self.horse_list.setCurrentRow(0)
        elif key == Qt.Key.Key_N:
            # Next item
            current_row = self.horse_list.currentRow()
            if current_row < self.horse_list.count() - 1:
                self.horse_list.setCurrentRow(current_row + 1)
        elif key == Qt.Key.Key_P:
            # Previous item
            current_row = self.horse_list.currentRow()
            if current_row > 0:
                self.horse_list.setCurrentRow(current_row - 1)
        elif key == Qt.Key.Key_S:
            # Focus search
            self.search_input.setFocus()
        elif key == Qt.Key.Key_F4:
            # Toggle active filter
            self.active_only_checkbox.setChecked(
                not self.active_only_checkbox.isChecked()
            )
        else:
            super().keyPressEvent(event)
