# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen (Dark Theme)
Version: 1.7.2
Purpose: Unified interface for horse management.
         Added logging in save_changes for location_id.
Last Updated: May 21, 2025
Author: Gemini

Changelog:
- v1.7.2 (2025-05-21):
    - Added logging in `save_changes` to display the `current_location_id`
      from the data being sent to the horse controller.
- v1.7.1 (2025-05-20):
    - (Based on GitHub v1.7.0)
    - Modified `__init__` to call `self.load_initial_data()` via a
      `QTimer.singleShot` with a short delay (e.g., 100ms).
- v1.7.0 (2025-05-20):
    - Integrated LocationTab, connected its signals, and updated related logic.
# ... other previous changelog entries
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QSplitter,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QMenu,
    QDialog,
    QMessageBox,
    QStatusBar,
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QAction,
    QKeyEvent,
    QShowEvent,
    QCloseEvent,
)

from views.base_view import BaseView
from config.app_config import (
    DARK_BACKGROUND,
    DARK_WIDGET_BACKGROUND,
    DARK_HEADER_FOOTER,
    DARK_BORDER,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DARK_PRIMARY_ACTION,
    DARK_SUCCESS_ACTION,
    DARK_WARNING_ACTION,
    DARK_DANGER_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_ITEM_HOVER,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_INPUT_FIELD_BACKGROUND,
    DEFAULT_FONT_FAMILY,
)
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController
from controllers.location_controller import LocationController
from models import Horse, Location as LocationModel

from .tabs.basic_info_tab import BasicInfoTab
from .tabs.owners_tab import OwnersTab
from .tabs.location_tab import LocationTab  # Make sure this import is correct
from .widgets.horse_list_widget import HorseListWidget


class HorseUnifiedManagement(BaseView):
    horse_selection_changed = Signal(int)
    exit_requested = Signal()
    setup_requested = Signal()
    closing = Signal()

    def __init__(self, current_user=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"HorseUnifiedManagement __init__ started for user: {current_user}"
        )
        self.current_user = current_user or "ADMIN"  # Default to ADMIN if None
        self.horse_controller = HorseController()
        self.owner_controller = OwnerController()
        self.location_controller = LocationController()

        super().__init__()  # This calls self.setup_ui() which should be defined below

        self.horses_list: List[Horse] = []
        self.current_horse: Optional[Horse] = None
        self._has_changes_in_active_tab: bool = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # UI elements will be initialized in setup_ui
        self.basic_info_tab: Optional[BasicInfoTab] = None
        self.owners_tab: Optional[OwnersTab] = None
        self.location_tab: Optional[LocationTab] = None
        self.tab_widget: Optional[QTabWidget] = None

        QTimer.singleShot(100, self.load_initial_data)

        self.logger.info(
            "HorseUnifiedManagement screen __init__ finished (initial data load deferred)."
        )

    def showEvent(self, event: QShowEvent):
        self.logger.info("HorseUnifiedManagement showEvent triggered.")
        super().showEvent(event)
        self.logger.info("HorseUnifiedManagement is now visible.")

    def closeEvent(self, event: QCloseEvent):
        self.logger.warning(
            f"HorseUnifiedManagement closeEvent triggered. Event type: {event.type()}"
        )
        self.closing.emit()
        super().closeEvent(event)
        self.logger.warning(
            "HorseUnifiedManagement has finished processing closeEvent."
        )

    def get_form_input_style(self, base_bg=DARK_INPUT_FIELD_BACKGROUND):
        return f"""
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
                background-color: {base_bg}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 10px; font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
            QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QDoubleSpinBox:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent; width: 15px; }}
            QComboBox::down-arrow {{ /*image: url(:/icons/down_arrow.svg);*/ /* Replace with actual icon path or keep color */ color: {DARK_TEXT_SECONDARY}; }}
            QDateEdit::up-button, QDateEdit::down-button {{ width: 18px; /* Adjust as needed */ }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }}
        """

    def get_generic_button_style(self):
        return f"""
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}
        """

    def get_toolbar_button_style(self, bg_color_hex, text_color_hex="#ffffff"):
        if len(bg_color_hex) == 4 and bg_color_hex.startswith(
            "#"
        ):  # Expand 3-digit hex if needed
            bg_color_hex = f"#{bg_color_hex[1]*2}{bg_color_hex[2]*2}{bg_color_hex[3]*2}"
        try:
            r = int(bg_color_hex[1:3], 16)
            g = int(bg_color_hex[3:5], 16)
            b = int(bg_color_hex[5:7], 16)
            hover_bg = f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
            pressed_bg = f"#{max(0,r-40):02x}{max(0,g-40):02x}{max(0,b-40):02x}"
        except ValueError:  # Fallback if color parsing fails
            hover_bg = DARK_BUTTON_HOVER
            pressed_bg = DARK_BUTTON_BG
            self.logger.warning(
                f"Could not parse color for hover/pressed state: {bg_color_hex}"
            )
        return f"""
            QPushButton {{
                background-color: {bg_color_hex}; color: {text_color_hex};
                border: none; border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {hover_bg}; }}
            QPushButton:pressed {{ background-color: {pressed_bg}; }}
            QPushButton:disabled {{ background-color: #adb5bd; color: #f8f9fa; }}
        """

    def setup_ui(self):  # This method is called by BaseView.__init__
        self.logger.debug("HorseUnifiedManagement.setup_ui: START")
        self.set_title("Horse Management")
        self.resize(1200, 800)  # Default size

        main_layout = QVBoxLayout(
            self.central_widget
        )  # This also sets layout on central_widget
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_header(main_layout)
        self.setup_action_bar(main_layout)
        self.setup_main_content(
            main_layout
        )  # This will setup splitter, list, and details panels
        self.setup_footer(main_layout)
        self.setup_connections()  # Connect signals after all UI elements are created
        self.logger.debug("HorseUnifiedManagement.setup_ui: END")

    def setup_header(self, parent_layout):
        self.logger.debug("setup_header: START")
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setFixedHeight(55)
        header_frame.setStyleSheet(
            f"""
            #HeaderFrame {{ background-color: {DARK_HEADER_FOOTER}; border: none; padding: 0 20px; }}
            QLabel {{ color: {DARK_TEXT_PRIMARY}; background-color: transparent; }}
            QPushButton#UserMenuButton {{ 
                color: {DARK_TEXT_SECONDARY}; font-size: 12px;
                background-color: transparent; border: none; padding: 5px; text-align: right;
            }}
            QPushButton#UserMenuButton::menu-indicator {{ image: none; }} /* Hide default menu arrow */
            QPushButton#UserMenuButton:hover {{ 
                color: {DARK_TEXT_PRIMARY}; 
                background-color: {QColor(DARK_ITEM_HOVER).lighter(110).name(QColor.NameFormat.HexRgb)}33; /* Lighten hover with alpha */
            }}
        """
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addStretch()
        title_label = QLabel("EDSI - Horse Management")
        title_label.setFont(QFont(DEFAULT_FONT_FAMILY, 15, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        breadcrumb_label = QLabel("🏠 Horse Management")  # Example breadcrumb
        breadcrumb_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 11px; background: transparent;"
        )
        left_layout.addWidget(breadcrumb_label)
        left_layout.addStretch()

        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh Data (F5)")
        self.help_btn = QPushButton("❓")
        self.help_btn.setToolTip("Help (F1)")
        self.print_btn = QPushButton("🖨️")
        self.print_btn.setToolTip("Print Options")
        self.setup_icon_btn = QPushButton("⚙️")
        self.setup_icon_btn.setToolTip("System Setup")

        header_button_style = (
            f"QPushButton {{ "
            f"background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 5px; "
            f"font-size: 14px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; "
            f"}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:pressed {{ background-color: {DARK_BUTTON_BG}; }}"
        )
        self.refresh_btn.setStyleSheet(header_button_style)
        self.help_btn.setStyleSheet(header_button_style)
        self.print_btn.setStyleSheet(header_button_style)
        self.setup_icon_btn.setStyleSheet(header_button_style)

        self.user_menu_button = QPushButton(f"👤 User: {self.current_user}")
        self.user_menu_button.setObjectName("UserMenuButton")
        self.user_menu_button.setToolTip("User options")
        self.user_menu_button.setFlat(
            True
        )  # Makes it look less like a button until hovered

        self.user_menu = QMenu(self)  # Parent is self (HorseUnifiedManagement)
        self.user_menu.setStyleSheet(
            f"""
            QMenu {{ 
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; 
                border: 1px solid {DARK_BORDER}; padding: 5px;
            }}
            QMenu::item {{ padding: 5px 20px 5px 20px; min-width: 100px; }}
            QMenu::item:selected {{ 
                background-color: {DARK_HIGHLIGHT_BG}70; /* Alpha for selection */
                color: {DARK_HIGHLIGHT_TEXT}; 
            }}
            QMenu::separator {{ 
                height: 1px; background: {DARK_BORDER}; 
                margin-left: 5px; margin-right: 5px;
            }}
        """
        )
        logout_action = QAction("Log Out", self)
        logout_action.triggered.connect(self.handle_logout_request_from_menu)
        self.user_menu.addAction(logout_action)
        self.user_menu_button.setMenu(self.user_menu)

        right_layout.addWidget(self.refresh_btn)
        right_layout.addWidget(self.help_btn)
        right_layout.addWidget(self.print_btn)
        right_layout.addWidget(self.setup_icon_btn)
        right_layout.addWidget(self.user_menu_button)

        header_layout.addWidget(left_widget)
        header_layout.addStretch()
        header_layout.addWidget(right_widget)
        parent_layout.addWidget(header_frame)
        self.logger.debug("setup_header: END")

    def setup_action_bar(self, parent_layout):
        self.logger.debug("setup_action_bar: START")
        action_bar_frame = QFrame()
        action_bar_frame.setObjectName("ActionBarFrame")
        action_bar_frame.setFixedHeight(50)
        action_bar_frame.setStyleSheet(
            f"""
            #ActionBarFrame {{ 
                background-color: {DARK_BACKGROUND}; border: none; 
                border-bottom: 1px solid {DARK_BORDER}; padding: 0 20px; 
            }}
            QPushButton {{ min-height: 30px; }} /* Ensure buttons are tall enough */
            QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; }}
            QRadioButton::indicator {{ width: 13px; height: 13px; }}
            QRadioButton {{ color: {DARK_TEXT_SECONDARY}; background: transparent; padding: 5px; }}
        """
        )
        action_bar_layout = QHBoxLayout(action_bar_frame)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)  # Use frame padding
        action_bar_layout.setSpacing(12)
        action_bar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.add_horse_btn = QPushButton("➕ Add Horse")
        self.edit_horse_btn = QPushButton("✓ Edit Selected")
        action_button_style = self.get_generic_button_style()
        add_btn_bg_color = DARK_PRIMARY_ACTION
        if len(add_btn_bg_color) == 4:
            add_btn_bg_color = f"#{add_btn_bg_color[1]*2}{add_btn_bg_color[2]*2}{add_btn_bg_color[3]*2}"

        self.add_horse_btn.setStyleSheet(
            action_button_style.replace(
                DARK_BUTTON_BG, add_btn_bg_color + "B3"
            ).replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;")
        )  # Primary with alpha
        self.edit_horse_btn.setStyleSheet(action_button_style)

        action_bar_layout.addWidget(self.add_horse_btn)
        action_bar_layout.addWidget(self.edit_horse_btn)

        self.filter_group = QButtonGroup(self)
        self.active_only_radio = QRadioButton("Active Only")
        self.all_horses_radio = QRadioButton("All Horses")
        self.deactivated_radio = QRadioButton("Deactivated")
        self.filter_group.addButton(self.active_only_radio)
        self.filter_group.addButton(self.all_horses_radio)
        self.filter_group.addButton(self.deactivated_radio)
        self.active_only_radio.setChecked(True)

        action_bar_layout.addWidget(self.active_only_radio)
        action_bar_layout.addWidget(self.all_horses_radio)
        action_bar_layout.addWidget(self.deactivated_radio)
        action_bar_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(
            self.get_form_input_style(base_bg=DARK_HEADER_FOOTER)
        )  # Slightly different bg for search

        action_bar_layout.addWidget(self.search_input)
        self.edit_horse_btn.setEnabled(False)  # Initially disabled
        parent_layout.addWidget(action_bar_frame)
        self.logger.debug("setup_action_bar: END")

    def setup_main_content(self, parent_layout):
        self.logger.debug("setup_main_content: START")
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)  # Very thin handle
        self.splitter.setStyleSheet(
            f"""
            QSplitter {{ background-color: {DARK_BACKGROUND}; border: none; }}
            QSplitter::handle {{ background-color: {DARK_BORDER}; }}
            QSplitter::handle:horizontal {{ width: 1px; }}
            QSplitter::handle:pressed {{ background-color: {DARK_TEXT_SECONDARY}; }}
        """
        )

        self.setup_horse_list_panel()  # Adds itself to splitter
        self.setup_horse_details_panel()  # Adds itself to splitter

        self.splitter.setSizes([300, 850])  # Initial sizes
        self.splitter.setStretchFactor(0, 0)  # Horse list panel - no stretch
        self.splitter.setStretchFactor(1, 1)  # Details panel - stretch
        self.splitter.setCollapsible(
            0, False
        )  # Prevent list from being fully collapsed
        self.splitter.setCollapsible(
            1, False
        )  # Prevent details from being fully collapsed

        parent_layout.addWidget(self.splitter, 1)  # Give splitter stretch factor
        self.logger.debug("setup_main_content: END")

    def setup_horse_list_panel(self):
        self.list_widget_container = (
            QWidget()
        )  # Container for potential future elements like a header for the list
        self.list_widget_container.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none; border-right: 1px solid {DARK_BORDER};"
        )
        list_layout = QVBoxLayout(self.list_widget_container)
        list_layout.setContentsMargins(
            0, 0, 0, 0
        )  # No margins, list widget will handle padding
        list_layout.setSpacing(0)

        self.horse_list = HorseListWidget()  # Custom styled list widget
        self.horse_list.setMinimumWidth(250)  # Ensure it doesn't get too small
        list_layout.addWidget(self.horse_list, 1)  # List takes all available space
        self.splitter.addWidget(self.list_widget_container)

    def setup_horse_details_panel(self):
        self.details_widget = QWidget()  # Main container for the right panel
        self.details_widget.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none;"
        )
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(
            15, 10, 15, 10
        )  # Padding around details area
        self.details_layout.setSpacing(15)

        # This widget will hold the actual horse details (header, tabs)
        self.horse_details_content_widget = QWidget()
        details_content_layout = QVBoxLayout(self.horse_details_content_widget)
        details_content_layout.setContentsMargins(
            0, 0, 0, 0
        )  # No internal margins, handled by elements
        details_content_layout.setSpacing(15)

        self.setup_horse_header_details(details_content_layout)
        self.setup_horse_tabs(details_content_layout)  # Tabs take most space

        self.setup_empty_state()  # For when no horse is selected

        self.details_layout.addWidget(self.empty_frame)  # Add empty state first
        self.details_layout.addWidget(
            self.horse_details_content_widget
        )  # Add actual content widget

        self.horse_details_content_widget.hide()  # Hide details until a horse is selected
        self.splitter.addWidget(self.details_widget)

    def setup_empty_state(self):
        self.empty_frame = QFrame()
        self.empty_frame.setObjectName("EmptyFrame")
        self.empty_frame.setStyleSheet(
            f"#EmptyFrame {{ background-color: transparent; border: none; }}"
        )
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(15)
        empty_label = QLabel("Select a horse from the list")
        empty_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 16px; background: transparent;"
        )
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        # Could add an icon or image here too

    def setup_horse_header_details(
        self, parent_layout
    ):  # Parent is details_content_layout
        header_widget = QWidget()  # Container for horse title and info line
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        self.horse_title = QLabel("Horse Name")  # Placeholder
        self.horse_title.setFont(QFont(DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold))
        self.horse_title.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )

        self.horse_info_line = QLabel(
            "Account: N/A | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A | 📍 N/A"
        )
        self.horse_info_line.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        self.horse_info_line.setWordWrap(True)

        header_layout.addWidget(self.horse_title)
        header_layout.addWidget(self.horse_info_line)
        parent_layout.addWidget(header_widget)

    def setup_horse_tabs(
        self, parent_layout_for_tabs
    ):  # Parent is details_content_layout
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DetailsTabWidget")  # For specific styling
        self.tab_widget.setStyleSheet(
            f"""
            QTabWidget#DetailsTabWidget::pane {{ 
                border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND}; 
                border-radius: 6px; /* Rounded corners for the pane */
                margin-top: -1px; /* Overlap with tab bar slightly for connected look */
            }}
            QTabBar::tab {{ 
                padding: 8px 15px; margin-right: 2px;
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY}; 
                border: 1px solid {DARK_BORDER}; border-bottom: none;
                border-top-left-radius: 5px; border-top-right-radius: 5px;
                min-width: 90px; font-size: 13px; font-weight: 500;
            }}
            QTabBar::tab:selected {{ 
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border-color: {DARK_BORDER}; 
                border-bottom-color: {DARK_WIDGET_BACKGROUND}; /* Make bottom border match pane */
            }}
            QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; color: {DARK_TEXT_PRIMARY}; }}
            QTabBar {{ border: none; background-color: transparent; margin-bottom: 0px; /* Align with pane top */ }}
        """
        )

        self.basic_info_tab = BasicInfoTab(
            self, self.horse_controller
        )  # Pass self as parent_view
        self.basic_info_tab.data_modified.connect(self._on_tab_data_modified)
        self.basic_info_tab.save_requested.connect(self.save_changes)
        self.basic_info_tab.discard_requested.connect(self.discard_changes)
        self.basic_info_tab.toggle_active_requested.connect(
            self.handle_toggle_active_status_from_tab
        )
        self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")

        self.owners_tab = OwnersTab(
            self, self.horse_controller, self.owner_controller
        )  # Pass self as parent_view
        self.owners_tab.owner_association_changed.connect(
            self._on_owner_association_changed
        )
        self.tab_widget.addTab(self.owners_tab, "👥 Owners")

        self.location_tab = LocationTab(
            self, self.horse_controller, self.location_controller
        )
        self.location_tab.location_assignment_changed.connect(
            self._handle_location_assignment_change
        )
        self.tab_widget.addTab(self.location_tab, "📍 Location")

        # Placeholder tabs for future expansion
        placeholder_tab_names = ["💰 Billing", "📊 History"]
        for name in placeholder_tab_names:
            placeholder_widget = QWidget()
            placeholder_widget.setStyleSheet(
                f"background-color: {DARK_WIDGET_BACKGROUND};"
            )  # Ensure consistent bg
            placeholder_layout = QVBoxLayout(placeholder_widget)
            placeholder_label = QLabel(f"Content for {name} tab.")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet(
                f"color: {DARK_TEXT_SECONDARY}; background: transparent;"
            )
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(placeholder_widget, name)

        parent_layout_for_tabs.addWidget(
            self.tab_widget, 1
        )  # Tabs take up remaining vertical space

    def _handle_location_assignment_change(self, location_data: Dict):
        self.logger.info(
            f"HorseUnifiedManagement received location_assignment_changed: {location_data}"
        )
        new_location_id = location_data.get("id")
        new_location_name = location_data.get("name", "N/A")

        # Update BasicInfoTab's display immediately
        if hasattr(self, "basic_info_tab") and self.basic_info_tab:
            self.basic_info_tab.update_displayed_location(
                new_location_id, new_location_name
            )
            self.logger.debug(
                f"Called basic_info_tab.update_displayed_location with ID={new_location_id}, Name='{new_location_name}'"
            )

        # Update current_horse object in HorseUnifiedManagement
        if self.current_horse:
            self.current_horse.current_location_id = new_location_id
            if new_location_id is not None:
                # Fetch Location object if needed, or assume LocationTab provides enough info
                loc_obj = self.location_controller.get_location_by_id(new_location_id)
                self.current_horse.location = loc_obj  # Assign full object if available
            else:
                self.current_horse.location = None

            # Update the horse header info line
            age_str = (
                self.horse_list._calculate_age(self.current_horse.date_of_birth)
                if self.horse_list and hasattr(self.horse_list, "_calculate_age")
                else "Age N/A"
            )
            self.horse_info_line.setText(
                f"Acct: {self.current_horse.account_number or 'N/A'} | Breed: {self.current_horse.breed or 'N/A'} | "
                f"Color: {self.current_horse.color or 'N/A'} | Sex: {self.current_horse.sex or 'N/A'} | Age: {age_str} | "
                f"📍 {new_location_name}"
            )
            self.logger.debug(
                f"Horse header updated with new location: {new_location_name}"
            )

        # BasicInfoTab's update_displayed_location should emit data_modified if the ID changed
        # and the form is editable. This will trigger _on_tab_data_modified.

    def _on_tab_data_modified(self):
        if (
            not self._has_changes_in_active_tab
        ):  # Prevent multiple signals if already true
            self.logger.debug(
                "Change detected in active tab's form (e.g., BasicInfoTab)."
            )
            self._has_changes_in_active_tab = True
            self.update_main_action_buttons_state()  # Update buttons like Save/Discard

    def _on_owner_association_changed(self, message: str):
        self.update_status(message)
        self._has_changes_in_active_tab = True  # Owner changes are also "changes"
        self.update_main_action_buttons_state()
        # Potentially refresh horse list item if owner info is part of it (not currently)

    def handle_toggle_active_status_from_tab(self, current_status: bool):
        if self.current_horse:
            self.handle_toggle_active_status()  # Call the main screen's handler
        else:
            self.logger.warning(
                "Toggle active requested from tab, but no current horse selected."
            )

    def setup_footer(self, parent_layout):
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(
            f"""
            QStatusBar {{ 
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_SECONDARY}; 
                border: none; border-top: 1px solid {DARK_BORDER}; padding: 0 15px; font-size: 11px;
            }}
            QStatusBar::item {{ border: none; }} /* Remove borders around widgets in status bar */
            QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; font-size: 11px; }}
        """
        )
        parent_layout.addWidget(self.status_bar)

        self.status_label = QLabel("Ready")  # Main status message area
        self.footer_horse_count_label = QLabel("Showing 0 of 0 horses")
        self.shortcut_label = QLabel("F5=Refresh")

        self.status_bar.addWidget(
            self.status_label, 1
        )  # Stretch factor 1 for status_label
        self.status_bar.addPermanentWidget(self.footer_horse_count_label)
        separator_label = QLabel(" | ")  # Visual separator
        separator_label.setStyleSheet(
            f"color: {DARK_BORDER}; background: transparent; margin: 0 5px;"
        )
        self.status_bar.addPermanentWidget(separator_label)
        self.status_bar.addPermanentWidget(self.shortcut_label)

    def save_changes(self):
        if not self.basic_info_tab:
            self.logger.error("BasicInfoTab is not initialized. Cannot save.")
            self.show_error("Save Error", "Cannot retrieve horse data to save.")
            return

        if not self._has_changes_in_active_tab:
            self.update_status("No changes to save.")
            return

        horse_data_to_save = self.basic_info_tab.get_data()
        if (
            horse_data_to_save is None
        ):  # Should not happen if _has_changes_in_active_tab is true
            self.logger.warning(
                "No data retrieved from BasicInfoTab to save, though changes were flagged."
            )
            return

        # Log the location ID being sent to the controller
        location_id_being_saved = horse_data_to_save.get("current_location_id")
        self.logger.info(
            f"Attempting to save horse data. current_location_id in data: {location_id_being_saved}"
        )

        # Owner associations are managed directly by OwnersTab and HorseController methods,
        # not typically through the main save_changes of BasicInfoTab.
        # However, if there was a direct list of owner IDs to associate from BasicInfo, it would be here.
        # owner_ids_to_associate = None # Example

        is_new_horse = self.current_horse is None or self.current_horse.horse_id is None
        self.logger.info(
            f"Attempting to save. New horse: {is_new_horse}. Data: {horse_data_to_save}"
        )

        is_valid, errors = self.horse_controller.validate_horse_data(
            horse_data_to_save,
            is_new=is_new_horse,
            horse_id_to_check_for_unique=(
                self.current_horse.horse_id
                if not is_new_horse and self.current_horse
                else None
            ),
        )
        if not is_valid:
            error_message = "Please correct the following errors:\n\n- " + "\n- ".join(
                errors
            )
            self.show_warning("Validation Error", error_message)
            return

        try:
            saved_horse_id = None
            success = False
            message = ""
            if not is_new_horse and self.current_horse:
                # Pass current_user (which is login_id) to controller
                op_success, op_message = self.horse_controller.update_horse(
                    self.current_horse.horse_id, horse_data_to_save, self.current_user
                )
                success = op_success
                message = op_message
                if success:
                    saved_horse_id = self.current_horse.horse_id
            else:  # New horse
                op_success, op_message, new_horse_obj = (
                    self.horse_controller.create_horse(
                        horse_data_to_save, self.current_user
                    )
                )
                success = op_success
                message = op_message
                if success and new_horse_obj:
                    saved_horse_id = new_horse_obj.horse_id

            if success:
                self.show_info("Success", message)
                self._has_changes_in_active_tab = False
                self.load_horses()  # Refresh list
                if saved_horse_id:  # Reselect the saved/created horse
                    for i in range(self.horse_list.count()):
                        item = self.horse_list.item(i)
                        if (
                            item
                            and item.data(Qt.ItemDataRole.UserRole) == saved_horse_id
                        ):
                            self.horse_list.setCurrentRow(
                                i
                            )  # This will trigger on_selection_changed
                            break
                self.update_main_action_buttons_state()
                # Explicitly update BasicInfoTab's buttons state after save
                if self.basic_info_tab:
                    self.basic_info_tab.update_buttons_state(
                        False, True if self.current_horse else False
                    )

                self.update_status(
                    f"Saved: {horse_data_to_save.get('horse_name', 'Unknown Horse')}"
                )
            else:
                self.show_error(
                    "Save Failed", message if message else "Unknown error during save."
                )
        except Exception as e:
            self.logger.error(f"Exception during save operation: {e}", exc_info=True)
            self.show_error("Save Error", f"An unexpected error occurred: {e}")

    def populate_horse_list(self):
        # ... (rest of the methods like populate_horse_list, load_initial_data, etc., remain unchanged from v1.7.1) ...
        self.horse_list.clear()
        for horse in self.horses_list:
            item = QListWidgetItem()  # Create QListWidgetItem
            item_widget = self.horse_list.create_horse_list_item_widget(
                horse
            )  # Create custom widget
            item.setSizeHint(item_widget.sizeHint())  # Set size hint for the item
            item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)  # Store horse_id
            self.horse_list.addItem(item)  # Add item to list
            self.horse_list.setItemWidget(
                item, item_widget
            )  # Set custom widget for item

        total_horses_count = len(self.horse_controller.search_horses(status="all"))
        self.footer_horse_count_label.setText(
            f"Showing {self.horse_list.count()} of {total_horses_count} total horses"
        )

    def load_initial_data(self):
        self.logger.info("load_initial_data called.")
        self.load_horses()
        self.update_status("Initialization complete. Ready.")
        # Any other initial setup like loading combo box data for tabs can go here

    def load_horses(self):
        try:
            if not hasattr(self, "search_input") or not hasattr(self, "status_label"):
                self.logger.error(
                    "load_horses called before UI elements (search_input/status_label) are initialized."
                )
                return

            search_term = self.search_input.text()
            status_filter = "active"  # Default
            if self.all_horses_radio.isChecked():
                status_filter = "all"
            elif self.deactivated_radio.isChecked():
                status_filter = "inactive"

            self.logger.info(
                f"Loading horses (Status: {status_filter}, Search: '{search_term}')"
            )
            selected_id_before_load = (
                self.current_horse.horse_id if self.current_horse else None
            )

            self.horses_list = self.horse_controller.search_horses(
                search_term, status=status_filter
            )
            self.populate_horse_list()  # This now uses the custom widget

            reselected_item = False
            if selected_id_before_load is not None:
                for i in range(self.horse_list.count()):
                    item = self.horse_list.item(i)
                    if (
                        item
                        and item.data(Qt.ItemDataRole.UserRole)
                        == selected_id_before_load
                    ):
                        self.horse_list.setCurrentItem(
                            item
                        )  # Triggers on_selection_changed
                        reselected_item = True
                        break

            if not reselected_item and self.horse_list.count() > 0:
                self.horse_list.setCurrentRow(
                    0
                )  # Select first item if nothing was reselected
            elif not self.horses_list:  # No horses match filter/search
                self.display_empty_state()

            self.update_status(f"Loaded {len(self.horses_list)} horses.")
        except AttributeError as ae:  # Catch if UI elements not ready
            self.logger.error(f"AttributeError during load_horses: {ae}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error loading horses: {e}", exc_info=True)
            self.show_error("Load Error", f"Failed to load horse list: {e}")
            self.horses_list = []  # Ensure list is empty on error
            self.populate_horse_list()  # Clear visual list
            self.display_empty_state()

    def on_search_text_changed(self):
        self.search_timer.stop()  # Reset timer on each text change
        self.search_timer.start(350)  # Wait 350ms before searching

    def perform_search(self):
        self.load_horses()  # This will use the current search_input text

    def on_filter_changed(self):
        sender = self.sender()
        if isinstance(sender, QRadioButton) and sender.isChecked():
            self.load_horses()  # Reload with new filter

    def on_selection_changed(self):
        selected_items = self.horse_list.selectedItems()
        new_selected_id = None
        if selected_items:
            new_selected_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        current_selected_id = (
            self.current_horse.horse_id if self.current_horse else None
        )

        # Avoid reloading if selection hasn't effectively changed and details are visible
        if (
            new_selected_id == current_selected_id
            and self.horse_details_content_widget.isVisible()
        ):
            return

        if self._has_changes_in_active_tab:
            reply = self.show_question(
                "Unsaved Changes",
                "You have unsaved changes.\nDiscard and load selected horse?",
            )
            if not reply:
                # Revert selection in the list widget if user cancels
                self.horse_list.blockSignals(True)  # Prevent re-triggering this slot
                if current_selected_id is not None:
                    for i in range(self.horse_list.count()):
                        item = self.horse_list.item(i)
                        if (
                            item
                            and item.data(Qt.ItemDataRole.UserRole)
                            == current_selected_id
                        ):
                            self.horse_list.setCurrentRow(
                                i
                            )  # Visually re-select old item
                            break
                else:  # No previous selection, just clear current attempt
                    self.horse_list.clearSelection()
                self.horse_list.blockSignals(False)
                return  # User chose not to discard changes

        # Proceed with loading new selection or clearing details
        self._has_changes_in_active_tab = (
            False  # Discarded changes or no changes to begin with
        )
        if new_selected_id is not None:
            self.load_horse_details(new_selected_id)
        else:
            self.display_empty_state()  # No selection or list is empty

        self.update_main_action_buttons_state()  # Update main Add/Edit buttons

    def add_new_horse(self):
        if self._has_changes_in_active_tab:
            if not self.show_question(
                "Unsaved Changes", "Discard and start new horse?"
            ):
                return

        self.current_horse = None  # Clear current horse object
        self.horse_list.clearSelection()  # Deselect any item in the list

        # Reset tabs
        if self.basic_info_tab:
            self.basic_info_tab.set_new_mode()
        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(None)
        if self.location_tab:
            self.location_tab.load_location_for_horse(None)
        # Add other tabs if they need resetting

        self.horse_title.setText("New Horse Record")
        self.horse_info_line.setText(
            "Account: N/A | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A | 📍 N/A"
        )

        self.display_details_state()  # Show the details panel
        self.tab_widget.setCurrentWidget(self.basic_info_tab)  # Focus on basic info

        self._has_changes_in_active_tab = (
            True  # New form is inherently "changed" for save/discard logic
        )
        self.update_main_action_buttons_state()

        # Update button states for tabs, especially BasicInfoTab which handles Save/Discard
        if self.basic_info_tab:
            self.basic_info_tab.update_buttons_state(
                True, False
            )  # has_modifications=True, is_existing=False
        if self.owners_tab:
            self.owners_tab.update_buttons_state()
        if self.location_tab:
            self.location_tab.update_buttons_state()

        self.update_status("Enter details for new horse.")

    def edit_selected_horse(self):
        if self.current_horse:
            current_tab_widget = self.tab_widget.currentWidget()
            if current_tab_widget == self.basic_info_tab:
                self.basic_info_tab.set_form_read_only(
                    False
                )  # Make basic info editable
            # Other tabs might have their own edit modes or are always editable once a horse is loaded

            self.update_main_action_buttons_state()  # Reflect that we are in edit mode (e.g. disable Add Horse)
            if hasattr(current_tab_widget, "update_buttons_state"):
                current_tab_widget.update_buttons_state(
                    self._has_changes_in_active_tab, True
                )

            self.update_status(f"Editing: {self.current_horse.horse_name}")
        else:
            self.show_info("Edit Horse", "Please select a horse to edit.")

    def discard_changes(self):
        if not self._has_changes_in_active_tab:
            return

        if self.show_question("Confirm Discard", "Discard unsaved changes?"):
            if self.current_horse:  # If editing an existing horse, reload its details
                self.load_horse_details(self.current_horse.horse_id)
            else:  # If it was a new horse form, clear everything
                if self.basic_info_tab:
                    self.basic_info_tab.clear_fields()
                if self.owners_tab:
                    self.owners_tab.load_owners_for_horse(None)
                if self.location_tab:
                    self.location_tab.load_location_for_horse(None)
                self.display_empty_state()  # Or go to new horse state if preferred

            self._has_changes_in_active_tab = False
            self.update_main_action_buttons_state()
            self.update_status("Changes discarded.")

    def refresh_data(self):
        if self._has_changes_in_active_tab:
            if not self.show_question("Unsaved Changes", "Discard and refresh?"):
                return

        self._has_changes_in_active_tab = False
        current_selected_id = (
            self.current_horse.horse_id if self.current_horse else None
        )

        self.load_horses()  # Reloads the list

        # Try to re-select and reload details if a horse was selected
        if (
            self.current_horse and self.current_horse.horse_id == current_selected_id
        ):  # If selection didn't change due to list refresh
            self.load_horse_details(
                self.current_horse.horse_id
            )  # Reload details for currently selected
        elif (
            not self.current_horse and current_selected_id is not None
        ):  # If previously selected horse is no longer in list (e.g. filtered out)
            self.display_empty_state()

        self.update_main_action_buttons_state()
        self.update_status("Data refreshed.")

    def show_help(self):
        QMessageBox.information(self, "Help", "Help content will be displayed here.")

    def load_horse_details(self, horse_id: int):
        self.logger.info(f"Loading details for horse ID: {horse_id}")
        horse = self.horse_controller.get_horse_by_id(
            horse_id
        )  # Fetches with eager loaded location/species
        if not horse:
            self.show_error("Error", f"Could not load details for horse ID {horse_id}.")
            self.display_empty_state()
            return

        self.current_horse = horse
        self._has_changes_in_active_tab = False  # Reset change flag

        self.horse_title.setText(horse.horse_name or "Unnamed Horse")
        age_str = (
            self.horse_list._calculate_age(horse.date_of_birth)
            if self.horse_list and hasattr(self.horse_list, "_calculate_age")
            else "Age N/A"
        )
        location_name = horse.location.location_name if horse.location else "N/A"
        self.horse_info_line.setText(
            f"Acct: {horse.account_number or 'N/A'} | Breed: {horse.breed or 'N/A'} | "
            f"Color: {horse.color or 'N/A'} | Sex: {horse.sex or 'N/A'} | Age: {age_str} | "
            f"📍 {location_name}"
        )

        # Populate tabs
        if self.basic_info_tab:
            self.basic_info_tab.populate_fields(horse)
        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(horse)
        if self.location_tab:
            self.location_tab.load_location_for_horse(horse)
        # Add other tabs if they need population

        self.display_details_state()  # Ensure details panel is visible
        self.update_main_action_buttons_state()
        self.update_status(f"Viewing: {horse.horse_name or 'Unnamed Horse'}")

    def display_empty_state(self):
        self.empty_frame.show()
        self.horse_details_content_widget.hide()
        self.current_horse = None
        self._has_changes_in_active_tab = False
        if self.basic_info_tab:
            self.basic_info_tab.clear_fields()
        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(None)
        if self.location_tab:
            self.location_tab.load_location_for_horse(None)
        self.update_main_action_buttons_state()

    def display_details_state(self):
        self.empty_frame.hide()
        self.horse_details_content_widget.show()

    def update_status(self, message, timeout=4000):
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.setText(message)
            if timeout > 0:
                QTimer.singleShot(
                    timeout, lambda: self.clear_status_if_matches(message)
                )

    def clear_status_if_matches(self, original_message):
        if (
            hasattr(self, "status_label")
            and self.status_label
            and self.status_label.text() == original_message
        ):
            self.status_label.setText("Ready")  # Reset to default

    def update_main_action_buttons_state(self):
        can_edit = (
            self.current_horse is not None and not self._has_changes_in_active_tab
        )
        self.edit_horse_btn.setEnabled(can_edit)
        self.add_horse_btn.setEnabled(
            not self._has_changes_in_active_tab
        )  # Can add if not editing/new

        current_tab = self.tab_widget.currentWidget() if self.tab_widget else None
        if hasattr(current_tab, "update_buttons_state"):
            if current_tab == self.basic_info_tab and self.basic_info_tab:
                self.basic_info_tab.update_buttons_state(
                    self._has_changes_in_active_tab, self.current_horse is not None
                )
            elif current_tab == self.owners_tab and self.owners_tab:
                self.owners_tab.update_buttons_state()
            elif current_tab == self.location_tab and self.location_tab:
                self.location_tab.update_buttons_state()
            # Add other tabs if they have their own button states

    def handle_toggle_active_status(self):
        if not self.current_horse:
            return

        action_text = "activate" if not self.current_horse.is_active else "deactivate"
        confirm_msg = f"Sure to {action_text} '{self.current_horse.horse_name or f'ID {self.current_horse.horse_id}'}'?"

        if self.show_question(f"Confirm {action_text.capitalize()}", confirm_msg):
            controller_method = (
                self.horse_controller.activate_horse
                if not self.current_horse.is_active
                else self.horse_controller.deactivate_horse
            )
            success, message = controller_method(
                self.current_horse.horse_id, self.current_user
            )

            if success:
                self.show_info("Status Changed", message)
                self.load_horse_details(
                    self.current_horse.horse_id
                )  # Reload to reflect changes
                self.load_horses()  # Refresh list as active status changed filtering
            else:
                self.show_error(f"{action_text.capitalize()} Failed", message)

    def handle_logout_request_from_menu(self):
        self.logger.info(f"User '{self.current_user}' requested logout from menu.")
        self.exit_requested.emit()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            if self.add_horse_btn.isEnabled():
                self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            # Check if BasicInfoTab is active and its save button is enabled
            current_tab_widget = (
                self.tab_widget.currentWidget() if self.tab_widget else None
            )
            if (
                current_tab_widget == self.basic_info_tab
                and hasattr(self.basic_info_tab, "save_btn")
                and self.basic_info_tab.save_btn.isEnabled()
            ):
                self.basic_info_tab.save_requested.emit()  # Trigger save via signal
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            active_modal = QApplication.activeModalWidget()
            if active_modal and isinstance(
                active_modal, QDialog
            ):  # Close open dialogs first
                active_modal.reject()
            elif (
                self._has_changes_in_active_tab
            ):  # If form has changes, prompt to discard
                self.discard_changes()
            else:  # No changes, request exit/logout
                self.exit_requested.emit()
        else:
            super().keyPressEvent(event)

    def setup_connections(self):
        if hasattr(self, "add_horse_btn"):
            self.add_horse_btn.clicked.connect(self.add_new_horse)
        if hasattr(self, "edit_horse_btn"):
            self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        if hasattr(self, "refresh_btn"):
            self.refresh_btn.clicked.connect(self.refresh_data)
        if hasattr(self, "help_btn"):
            self.help_btn.clicked.connect(self.show_help)
        if hasattr(self, "setup_icon_btn"):
            self.setup_icon_btn.clicked.connect(
                self.setup_requested.emit
            )  # Emit signal

        if hasattr(self, "active_only_radio"):
            self.active_only_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "all_horses_radio"):
            self.all_horses_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "deactivated_radio"):
            self.deactivated_radio.toggled.connect(self.on_filter_changed)

        if hasattr(self, "search_input"):
            self.search_input.textChanged.connect(self.on_search_text_changed)
        if hasattr(self, "horse_list"):
            self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)

        # Connect signals from tabs to appropriate handlers or slots
        if self.basic_info_tab:
            self.basic_info_tab.data_modified.connect(self._on_tab_data_modified)
            self.basic_info_tab.save_requested.connect(self.save_changes)
            self.basic_info_tab.discard_requested.connect(self.discard_changes)
            self.basic_info_tab.toggle_active_requested.connect(
                self.handle_toggle_active_status_from_tab
            )

        if self.owners_tab:
            self.owners_tab.owner_association_changed.connect(
                self._on_owner_association_changed
            )

        if self.location_tab and self.basic_info_tab:  # Ensure both exist
            self.location_tab.location_assignment_changed.connect(
                self._handle_location_assignment_change
            )
