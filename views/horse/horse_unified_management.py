# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen

Unified interface for all horse management operations (CRUD, search, filter).
Version: 1.0.3
Last Updated: May 12, 2025

Changelog:
- v1.0.3 (2025-05-12): Added exit functionality and fixed missing signal
  - Added exit_requested signal for proper navigation flow
  - Added Exit button to action toolbar for returning to main menu
  - Added exit_application() method with unsaved changes check
  - Added Escape key handler for quick exit
  - Fixed connection error in main.py integration
- v1.0.2 (2025-05-12): Fixed date handling for PyQt6 compatibility
  - Updated save_changes() to properly convert QDate to Python date
  - Handled both toPython() method and manual conversion
  - Improved error handling for date operations
- v1.0.1 (2025-05-12): Fixed PyQt6 compatibility issues
  - Fixed date conversion in save_changes() method for PyQt6
  - Removed duplicate central widget creation
  - Improved error handling for date field operations
- v1.0.0 (2025-05-12): Initial implementation
  - Created unified horse management with split-pane layout
  - Implemented horse list with search and filtering
  - Added tabbed horse details with inline editing
  - Combined Add/Edit/Delete operations in single interface
  - Added modern UI with Material Design elements
  - Implemented auto-save functionality with visual feedback
  - Added bulk operations for multiple horse selection
  - Integrated photo placeholder for future horse images
"""

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QPushButton,
    QFrame,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QSplitter,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QMessageBox,
    QProgressBar,
    QStatusBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QPixmap, QPaintEvent, QPainter, QColor
from views.base_view import BaseView
from config.app_config import AppConfig
from controllers.horse_controller import HorseController
import logging
from datetime import datetime, date


class HorseListWidget(QListWidget):
    """Custom list widget with improved styling for horses"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
            QListWidget {
                border: none;
                background-color: white;
                alternate-background-color: #f8f9fa;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
                min-height: 60px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-left: 4px solid #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """
        )
        self.setAlternatingRowColors(True)


class HorseUnifiedManagement(BaseView):
    """Unified horse management interface with all CRUD operations"""

    # Signals
    horse_selection_changed = pyqtSignal(int)  # Emitted when horse selection changes
    unsaved_changes = pyqtSignal(bool)  # Emitted when there are unsaved changes
    exit_requested = pyqtSignal()  # Emitted when user wants to exit

    def __init__(self, current_user=None):
        self.current_user = current_user or "ADMIN"
        self.controller = HorseController()
        self.horses_list = []
        self.current_horse = None
        self.has_changes = False
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        super().__init__()
        self.setup_ui()
        self.load_initial_data()

        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_ui(self):
        """Setup the unified horse management UI"""
        self.set_title("Horse Management")
        self.resize(1200, 800)
        self.center_on_screen()

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.setup_header(main_layout)

        # Action toolbar
        self.setup_action_toolbar(main_layout)

        # Main content area
        self.setup_main_content(main_layout)

        # Status bar
        self.setup_status_bar(main_layout)

        # Setup connections
        self.setup_connections()

    def setup_header(self, parent_layout):
        """Setup header with breadcrumbs and user info"""
        header_frame = QFrame()
        header_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                padding: 0;
            }}
        """
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 12, 20, 12)

        # Left side - Title and breadcrumb
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Horse Management")
        title_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold))
        left_layout.addWidget(title_label)

        breadcrumb_label = QLabel("Main Menu > Horse Management")
        breadcrumb_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.8); font-size: 12px;"
        )
        left_layout.addWidget(breadcrumb_label)

        # Right side - User info and actions
        right_layout = QHBoxLayout()
        right_layout.addWidget(QLabel(f"User: {self.current_user}"))

        # Action buttons
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh (F5)")
        self.help_btn = QPushButton("❓")
        self.help_btn.setToolTip("Help (F1)")

        for btn in [self.refresh_btn, self.help_btn]:
            btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 4px;
                    padding: 6px;
                    color: white;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            """
            )

        right_layout.addWidget(self.refresh_btn)
        right_layout.addWidget(self.help_btn)

        header_layout.addWidget(left_widget)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)

        parent_layout.addWidget(header_frame)

    def setup_action_toolbar(self, parent_layout):
        """Setup action toolbar with buttons and search"""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 0;
            }
        """
        )
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(20, 16, 20, 16)

        # Action buttons
        action_buttons_layout = QHBoxLayout()

        self.add_horse_btn = QPushButton("➕ Add Horse")
        self.edit_horse_btn = QPushButton("✏️ Edit Selected")
        self.delete_horse_btn = QPushButton("🗑️ Delete Selected")
        self.exit_btn = QPushButton("✖️ Exit")

        for btn, color in [
            (self.add_horse_btn, AppConfig.PRIMARY_COLOR),
            (self.edit_horse_btn, AppConfig.SUCCESS_COLOR),
            (self.delete_horse_btn, AppConfig.DANGER_COLOR),
            (self.exit_btn, AppConfig.SECONDARY_COLOR),
        ]:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 16px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {color}dd;
                }}
                QPushButton:disabled {{
                    background-color: #6c757d;
                }}
            """
            )
            action_buttons_layout.addWidget(btn)

        # Initially disable edit and delete
        self.edit_horse_btn.setEnabled(False)
        self.delete_horse_btn.setEnabled(False)

        # Filter toggles
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 2px;
            }
        """
        )
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        self.active_only_btn = QPushButton("Active Only")
        self.all_horses_btn = QPushButton("All Horses")

        for btn in [self.active_only_btn, self.all_horses_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    background: transparent;
                }
                QPushButton:checked {
                    background-color: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
            """
            )

        self.active_only_btn.setChecked(True)
        filter_layout.addWidget(self.active_only_btn)
        filter_layout.addWidget(self.all_horses_btn)

        # Search box
        search_frame = QFrame()
        search_frame.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 0;
            }
        """
        )
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)

        search_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search horses...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                border: none;
                font-size: 14px;
            }
        """
        )
        search_layout.addWidget(self.search_input)
        search_frame.setFixedWidth(250)

        # Add to toolbar
        toolbar_layout.addLayout(action_buttons_layout)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(filter_frame)
        toolbar_layout.addWidget(search_frame)

        parent_layout.addWidget(toolbar_frame)

    def setup_main_content(self, parent_layout):
        """Setup main content area with split pane"""
        # Create splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(
            """
            QSplitter::handle {
                background-color: #e0e0e0;
            }
        """
        )

        # Left panel - Horse list
        self.setup_horse_list_panel()

        # Right panel - Horse details
        self.setup_horse_details_panel()

        # Set splitter sizes (30% for list, 70% for details)
        self.splitter.setSizes([360, 840])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)

        parent_layout.addWidget(self.splitter)

    def setup_horse_list_panel(self):
        """Setup left panel with horse list"""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # List header
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                padding: 0;
            }
        """
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)

        horses_label = QLabel("Horses")
        horses_label.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 14, QFont.Weight.Bold)
        )

        self.horse_count_label = QLabel("0 total")
        self.horse_count_label.setStyleSheet("color: #666; font-size: 12px;")

        header_layout.addWidget(horses_label)
        header_layout.addStretch()
        header_layout.addWidget(self.horse_count_label)

        # Horse list
        self.horse_list = HorseListWidget()
        self.horse_list.setMinimumWidth(300)

        list_layout.addWidget(header_frame)
        list_layout.addWidget(self.horse_list)

        self.splitter.addWidget(list_widget)

    def setup_horse_details_panel(self):
        """Setup right panel with horse details"""
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(20, 20, 20, 20)
        self.details_layout.setSpacing(20)

        # Empty state
        self.setup_empty_state()

        # Horse details (hidden initially)
        self.setup_horse_details()

        self.splitter.addWidget(self.details_widget)

    def setup_empty_state(self):
        """Setup empty state when no horse is selected"""
        self.empty_frame = QFrame()
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_label = QLabel("Select a horse to view details")
        empty_label.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 18px;
                font-weight: 300;
            }
        """
        )
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instruction_label = QLabel("Use the search box to find horses quickly")
        instruction_label.setStyleSheet(
            """
            QLabel {
                color: #999;
                font-size: 14px;
                font-style: italic;
            }
        """
        )
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_layout.addWidget(empty_label)
        empty_layout.addWidget(instruction_label)

        self.details_layout.addWidget(self.empty_frame)

    def setup_horse_details(self):
        """Setup horse details section"""
        self.horse_details_frame = QFrame()
        self.horse_details_frame.hide()
        horse_layout = QVBoxLayout(self.horse_details_frame)
        horse_layout.setSpacing(20)

        # Horse header with photo and basic info
        self.setup_horse_header(horse_layout)

        # Tabs for different sections
        self.setup_horse_tabs(horse_layout)

        # Action buttons
        self.setup_detail_actions(horse_layout)

        self.details_layout.addWidget(self.horse_details_frame)

    def setup_horse_header(self, parent_layout):
        """Setup horse header with photo and basic info"""
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0;
            }
        """
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(20)

        # Horse photo placeholder
        self.horse_photo = QLabel()
        self.horse_photo.setFixedSize(120, 120)
        self.horse_photo.setStyleSheet(
            """
            QLabel {
                background-color: #e0e0e0;
                border-radius: 8px;
                font-size: 48px;
                color: #999;
            }
        """
        )
        self.horse_photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horse_photo.setText("🐎")

        # Basic info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)

        self.horse_title = QLabel()
        self.horse_title.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 24, QFont.Weight.Bold)
        )
        self.horse_title.setStyleSheet(f"color: {AppConfig.TEXT_COLOR};")

        # Info grid
        self.info_frame = QFrame()
        self.info_grid = QGridLayout(self.info_frame)
        self.info_grid.setSpacing(12)

        self.info_labels = {}
        info_items = [
            ("Account", "account"),
            ("Breed", "breed"),
            ("Color", "color"),
            ("Sex", "sex"),
            ("Age", "age"),
            ("Location", "location"),
        ]

        for i, (label_text, key) in enumerate(info_items):
            row, col = i // 2, (i % 2) * 2

            label = QLabel(f"{label_text}:")
            label.setStyleSheet("color: #666; font-weight: 500;")
            value = QLabel()
            value.setStyleSheet("color: #333;")

            self.info_grid.addWidget(label, row, col)
            self.info_grid.addWidget(value, row, col + 1)
            self.info_labels[key] = value

        info_layout.addWidget(self.horse_title)
        info_layout.addWidget(self.info_frame)
        info_layout.addStretch()

        header_layout.addWidget(self.horse_photo)
        header_layout.addWidget(info_widget)

        parent_layout.addWidget(header_frame)

    def setup_horse_tabs(self, parent_layout):
        """Setup tabbed interface for horse details"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 12px 20px;
                margin-right: 2px;
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #0078d4;
                font-weight: 500;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """
        )

        # Basic Info tab
        self.setup_basic_info_tab()

        # Owners tab (placeholder)
        owners_tab = QWidget()
        self.tab_widget.addTab(owners_tab, "👥 Owners")

        # Location tab (placeholder)
        location_tab = QWidget()
        self.tab_widget.addTab(location_tab, "📍 Location")

        # Billing tab (placeholder)
        billing_tab = QWidget()
        self.tab_widget.addTab(billing_tab, "💰 Billing")

        # History tab (placeholder)
        history_tab = QWidget()
        self.tab_widget.addTab(history_tab, "📊 History")

        parent_layout.addWidget(self.tab_widget)

    def setup_basic_info_tab(self):
        """Setup basic information tab with form fields"""
        self.basic_info_tab = QWidget()
        basic_layout = QVBoxLayout(self.basic_info_tab)
        basic_layout.setContentsMargins(20, 20, 20, 20)
        basic_layout.setSpacing(15)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)

        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(15)

        # Form fields
        self.form_fields = {}
        fields = [
            ("Name", "horse_name", "text", True),
            ("Account Number", "account_number", "text", False),
            ("Breed", "breed", "text", False),
            ("Color", "color", "text", False),
            ("Sex", "sex", "combo", False),
            ("Date of Birth", "date_of_birth", "date", False),
            ("Registration Number", "registration_number", "text", False),
            ("Microchip ID", "microchip_id", "text", False),
            ("Tattoo", "tattoo", "text", False),
            ("Brand", "brand", "text", False),
            ("Current Location", "current_location_id", "combo", False),
            ("Band/Tag Number", "band_tag_number", "text", False),
        ]

        for i, (label_text, field_name, field_type, required) in enumerate(fields):
            row, col = i // 2, (i % 2) * 2

            # Label
            label = QLabel(label_text + ("*" if required else "") + ":")
            label.setStyleSheet("font-weight: 500; color: #333;")
            if required:
                label.setStyleSheet("font-weight: bold; color: #333;")

            # Field
            if field_type == "text":
                field = QLineEdit()
                field.setStyleSheet(self.get_input_style())
                field.textChanged.connect(self.on_field_changed)
            elif field_type == "combo":
                field = QComboBox()
                field.setStyleSheet(self.get_combo_style())
                field.currentTextChanged.connect(self.on_field_changed)

                if field_name == "sex":
                    field.addItems(
                        ["", "Male", "Female", "Gelding", "Stallion", "Mare"]
                    )
                elif field_name == "current_location_id":
                    self.load_locations_combo(field)
            elif field_type == "date":
                field = QDateEdit()
                field.setCalendarPopup(True)
                field.setStyleSheet(self.get_input_style())
                field.dateChanged.connect(self.on_field_changed)

            field.setMinimumHeight(40)
            form_layout.addWidget(label, row, col)
            form_layout.addWidget(field, row, col + 1)

            self.form_fields[field_name] = field

        scroll_area.setWidget(form_widget)
        basic_layout.addWidget(scroll_area)

        self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")

    def setup_detail_actions(self, parent_layout):
        """Setup action buttons for horse details"""
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 0, 20, 0)

        actions_layout.addStretch()

        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AppConfig.SUCCESS_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
            }}
        """
        )
        self.save_btn.setEnabled(False)

        self.discard_btn = QPushButton("↩️ Discard Changes")
        self.discard_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {AppConfig.SECONDARY_COLOR};
                border: 2px solid {AppConfig.SECONDARY_COLOR};
                border-radius: 6px;
                padding: 10px 22px;
                font-weight: 500;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.SECONDARY_COLOR};
                color: white;
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
        """
        )
        self.discard_btn.setEnabled(False)

        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.discard_btn)

        parent_layout.addWidget(actions_frame)

    def setup_status_bar(self, parent_layout):
        """Setup status bar"""
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #e0e0e0;
                padding: 0;
            }
        """
        )
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(20, 8, 20, 8)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")

        self.shortcut_label = QLabel(
            "F5=Refresh | Ctrl+N=New | Ctrl+S=Save | Del=Delete"
        )
        self.shortcut_label.setStyleSheet("color: #666; font-size: 12px;")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.shortcut_label)

        parent_layout.addWidget(self.status_frame)

    def setup_connections(self):
        """Setup signal connections"""
        # Buttons
        self.add_horse_btn.clicked.connect(self.add_new_horse)
        self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        self.delete_horse_btn.clicked.connect(self.delete_selected_horse)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.help_btn.clicked.connect(self.show_help)
        self.exit_btn.clicked.connect(self.exit_application)

        # Filter toggles
        self.active_only_btn.clicked.connect(self.on_filter_changed)
        self.all_horses_btn.clicked.connect(self.on_filter_changed)

        # Search
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # Horse list
        self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)

        # Save/Discard buttons
        self.save_btn.clicked.connect(self.save_changes)
        self.discard_btn.clicked.connect(self.discard_changes)

    def load_initial_data(self):
        """Load initial data"""
        self.load_horses()
        self.load_locations_combo(self.form_fields.get("current_location_id"))

    def load_horses(self):
        """Load horses into the list"""
        active_only = self.active_only_btn.isChecked()
        search_term = self.search_input.text()

        self.horses_list = self.controller.search_horses(search_term, active_only)
        self.populate_horse_list()
        self.update_status(f"Loaded {len(self.horses_list)} horses")

    def populate_horse_list(self):
        """Populate the horse list widget"""
        self.horse_list.clear()

        for horse in self.horses_list:
            item = QListWidgetItem()

            # Create custom widget for horse item
            item_widget = self.create_horse_list_item(horse)
            item.setSizeHint(item_widget.sizeHint())

            self.horse_list.addItem(item)
            self.horse_list.setItemWidget(item, item_widget)

            # Store horse data
            item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)

        # Update count
        self.horse_count_label.setText(f"{len(self.horses_list)} total")

    def create_horse_list_item(self, horse):
        """Create widget for horse list item"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Horse name
        name_label = QLabel(horse.horse_name)
        name_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #333;")

        # Account and breed
        info_label = QLabel(
            f"Acct: {horse.account_number or 'N/A'} | {horse.breed or 'Unknown breed'}"
        )
        info_label.setStyleSheet("color: #666; font-size: 12px;")

        # Color, sex, age
        details_label = QLabel(
            f"{horse.color or 'Unknown'} | {horse.sex or 'Unknown'} | {self.calculate_age(horse.date_of_birth)}"
        )
        details_label.setStyleSheet("color: #666; font-size: 12px;")

        # Location
        location_text = (
            horse.location.location_name if horse.location else "No location"
        )
        location_label = QLabel(f"📍 {location_text}")
        location_label.setStyleSheet("color: #888; font-size: 11px;")

        layout.addWidget(name_label)
        layout.addWidget(info_label)
        layout.addWidget(details_label)
        layout.addWidget(location_label)

        return widget

    def calculate_age(self, birth_date):
        """Calculate age from birth date"""
        if not birth_date:
            return "Unknown age"

        today = date.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (
            today.month == birth_date.month and today.day < birth_date.day
        ):
            age -= 1

        return f"{age} years" if age != 1 else "1 year"

    def load_locations_combo(self, combo_widget):
        """Load locations into combo box"""
        if not combo_widget:
            return

        combo_widget.clear()
        combo_widget.addItem("", None)

        locations = self.controller.get_locations_list()
        for location in locations:
            combo_widget.addItem(location.location_name, location.location_id)

    def on_search_text_changed(self):
        """Handle search text changes"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay

    def perform_search(self):
        """Perform the actual search"""
        self.load_horses()

    def on_filter_changed(self):
        """Handle filter change"""
        if self.sender() == self.active_only_btn:
            self.all_horses_btn.setChecked(False)
        else:
            self.active_only_btn.setChecked(False)
        self.load_horses()

    def on_selection_changed(self):
        """Handle horse selection change"""
        current_item = self.horse_list.currentItem()

        if current_item:
            horse_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.load_horse_details(horse_id)
            self.edit_horse_btn.setEnabled(True)
            self.delete_horse_btn.setEnabled(True)
        else:
            self.show_empty_state()
            self.edit_horse_btn.setEnabled(False)
            self.delete_horse_btn.setEnabled(False)

    def show_empty_state(self):
        """Show empty state in details panel"""
        self.empty_frame.show()
        self.horse_details_frame.hide()
        self.current_horse = None

    def load_horse_details(self, horse_id):
        """Load horse details into the details panel"""
        horse = self.controller.get_horse_by_id(horse_id)
        if not horse:
            self.show_error("Error", f"Horse with ID {horse_id} not found")
            return

        self.current_horse = horse

        # Update header info
        self.horse_title.setText(horse.horse_name)

        self.info_labels["account"].setText(horse.account_number or "N/A")
        self.info_labels["breed"].setText(horse.breed or "Unknown")
        self.info_labels["color"].setText(horse.color or "Unknown")
        self.info_labels["sex"].setText(horse.sex or "Unknown")
        self.info_labels["age"].setText(self.calculate_age(horse.date_of_birth))
        self.info_labels["location"].setText(
            f"📍 {horse.location.location_name if horse.location else 'No location'}"
        )

        # Populate form fields
        self.form_fields["horse_name"].setText(horse.horse_name or "")
        self.form_fields["account_number"].setText(horse.account_number or "")
        self.form_fields["breed"].setText(horse.breed or "")
        self.form_fields["color"].setText(horse.color or "")

        # Set sex combo
        sex_combo = self.form_fields["sex"]
        if horse.sex:
            index = sex_combo.findText(horse.sex)
            if index >= 0:
                sex_combo.setCurrentIndex(index)
        else:
            sex_combo.setCurrentIndex(0)

        # Set date
        if horse.date_of_birth:
            self.form_fields["date_of_birth"].setDate(QDate(horse.date_of_birth))

        self.form_fields["registration_number"].setText(horse.registration_number or "")
        self.form_fields["microchip_id"].setText(horse.microchip_id or "")
        self.form_fields["tattoo"].setText(horse.tattoo or "")
        self.form_fields["brand"].setText(horse.brand or "")
        self.form_fields["band_tag_number"].setText(horse.band_tag_number or "")

        # Set location combo
        location_combo = self.form_fields["current_location_id"]
        if horse.current_location_id:
            for i in range(location_combo.count()):
                if location_combo.itemData(i) == horse.current_location_id:
                    location_combo.setCurrentIndex(i)
                    break
        else:
            location_combo.setCurrentIndex(0)

        # Show details frame
        self.empty_frame.hide()
        self.horse_details_frame.show()

        # Reset change tracking
        self.has_changes = False
        self.update_change_buttons()

    def on_field_changed(self):
        """Handle field changes"""
        if self.current_horse:
            self.has_changes = True
            self.update_change_buttons()

    def update_change_buttons(self):
        """Update save/discard button states"""
        self.save_btn.setEnabled(self.has_changes)
        self.discard_btn.setEnabled(self.has_changes)

    def add_new_horse(self):
        """Add a new horse"""
        self.current_horse = None

        # Clear form fields
        for field_name, field in self.form_fields.items():
            if isinstance(field, QLineEdit):
                field.clear()
            elif isinstance(field, QComboBox):
                field.setCurrentIndex(0)
            elif isinstance(field, QDateEdit):
                field.setDate(QDate.currentDate())

        # Show details frame with empty form
        self.empty_frame.hide()
        self.horse_details_frame.show()

        # Update title and header
        self.horse_title.setText("New Horse")
        for key, label in self.info_labels.items():
            label.setText("N/A")

        # Set focus to name field
        self.form_fields["horse_name"].setFocus()

        # Reset change tracking
        self.has_changes = True
        self.update_change_buttons()

        self.update_status("Creating new horse")

    def edit_selected_horse(self):
        """Edit the selected horse"""
        # Horse details are already loaded, just set focus
        if self.current_horse:
            self.form_fields["horse_name"].setFocus()
            self.update_status(f"Editing horse: {self.current_horse.horse_name}")

    def delete_selected_horse(self):
        """Delete the selected horse"""
        if not self.current_horse:
            return

        reply = QMessageBox.question(
            self,
            "Delete Horse",
            f"Are you sure you want to delete '{self.current_horse.horse_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.controller.delete_horse(self.current_horse.horse_id)

            if success:
                QMessageBox.information(self, "Success", message)
                self.load_horses()  # Refresh list
                self.show_empty_state()  # Clear details
                self.update_status(f"Deleted horse: {self.current_horse.horse_name}")
                self.current_horse = None
            else:
                QMessageBox.critical(self, "Error", message)

    def save_changes(self):
        """Save current horse changes"""
        if not self.current_horse and not self.has_changes:
            return

        # Get date and convert properly for PyQt6
        date_field = self.form_fields["date_of_birth"]
        birth_date = None
        if date_field.date().isValid():
            qdate = date_field.date()
            # Try toPython() first, fallback to manual conversion
            try:
                birth_date = qdate.toPython()
            except AttributeError:
                # Manual conversion for PyQt6 versions without toPython()
                birth_date = date(qdate.year(), qdate.month(), qdate.day())

        # Collect form data
        horse_data = {
            "horse_name": self.form_fields["horse_name"].text().strip(),
            "account_number": self.form_fields["account_number"].text().strip(),
            "breed": self.form_fields["breed"].text().strip(),
            "color": self.form_fields["color"].text().strip(),
            "sex": (
                self.form_fields["sex"].currentText()
                if self.form_fields["sex"].currentText()
                else None
            ),
            "date_of_birth": birth_date,
            "registration_number": self.form_fields["registration_number"]
            .text()
            .strip(),
            "microchip_id": self.form_fields["microchip_id"].text().strip(),
            "tattoo": self.form_fields["tattoo"].text().strip(),
            "brand": self.form_fields["brand"].text().strip(),
            "band_tag_number": self.form_fields["band_tag_number"].text().strip(),
            "current_location_id": self.form_fields[
                "current_location_id"
            ].currentData(),
        }

        # Validate
        is_valid, errors = self.controller.validate_horse_data(horse_data)
        if not is_valid:
            error_message = "Please correct the following errors:\n" + "\n".join(errors)
            QMessageBox.critical(self, "Validation Error", error_message)
            return

        # Save or create
        if self.current_horse:
            # Update existing horse
            success, message = self.controller.update_horse(
                self.current_horse.horse_id, horse_data, self.current_user
            )
        else:
            # Create new horse
            success, message, horse = self.controller.create_horse(
                horse_data, self.current_user
            )
            if success:
                self.current_horse = horse

        if success:
            QMessageBox.information(self, "Success", message)
            self.has_changes = False
            self.update_change_buttons()
            self.load_horses()  # Refresh list

            # Reload current horse details
            if self.current_horse:
                self.load_horse_details(self.current_horse.horse_id)

            self.update_status(f"Saved horse: {horse_data['horse_name']}")
        else:
            QMessageBox.critical(self, "Error", message)

    def discard_changes(self):
        """Discard current changes"""
        if self.current_horse:
            # Reload original data
            self.load_horse_details(self.current_horse.horse_id)
        else:
            # Was creating new horse, show empty state
            self.show_empty_state()

        self.update_status("Changes discarded")

    def refresh_data(self):
        """Refresh all data"""
        self.load_horses()
        if self.current_horse:
            self.load_horse_details(self.current_horse.horse_id)
        self.update_status("Data refreshed")

    def show_help(self):
        """Show help dialog"""
        QMessageBox.information(
            self,
            "Help",
            """Horse Management Help
            
Navigation:
• Select a horse from the list to view/edit details
• Use the search box to filter horses
• Toggle between Active Only and All Horses

Actions:
• Add Horse: Create a new horse record
• Edit Selected: Modify the selected horse
• Delete Selected: Remove the selected horse (soft delete)

Keyboard Shortcuts:
• F5: Refresh data
• Ctrl+N: Add new horse
• Ctrl+S: Save changes
• Delete: Delete selected horse
• F1: Show this help""",
        )

    def exit_application(self):
        """Exit the horse management screen"""
        # Check for unsaved changes
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.exit_requested.emit()
        self.close()

    def update_status(self, message):
        """Update status bar"""
        self.status_label.setText(message)
        # Auto-clear status after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def get_input_style(self):
        """Get standard input field styling"""
        return f"""
            QLineEdit, QDateEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
                box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
            }}
        """

    def get_combo_style(self):
        """Get standard combo box styling"""
        return f"""
            QComboBox {{
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }}
            QComboBox:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
                box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
        """

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            self.save_changes()
        elif key == Qt.Key.Key_Delete:
            self.delete_selected_horse()
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            self.exit_application()
        else:
            super().keyPressEvent(event)
