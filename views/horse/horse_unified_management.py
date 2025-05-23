# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen (Dark Theme)
Version: 1.7.17
Purpose: Unified interface for horse management.
         - Removed incorrect re-assignment of tab variables in __init__.
         - display_empty_state now calls clear_fields with suppress_signal=True.
         - Retained diagnostic prints.
Last Updated: May 22, 2025
Author: Gemini

Changelog:
- v1.7.17 (2025-05-22):
    - Removed re-assignment of self.basic_info_tab, self.owners_tab, self.location_tab
      to None in __init__ AFTER super().__init__() call.
    - Modified display_empty_state to call self.basic_info_tab.clear_fields(suppress_signal=True).
    - Added reminder about finding and removing the rogue call to add_new_horse() during setup_ui.
- v1.7.16 (conceptual - user applied snippet):
    - Added print in display_empty_state to check self.basic_info_tab type.
- v1.7.15 (conceptual - user applied snippet or full rewrite):
    - Added print in add_new_horse to check self.basic_info_tab type.
- v1.7.14 (conceptual - user applied snippet or full rewrite):
    - Added print in update_main_action_buttons_state for add_horse_btn state.
- v1.7.13 (Original User Upload / 2025-05-21):
    - Added granular unconditional `print()` statements within `display_empty_state`
      to pinpoint where `self.tab_widget` becomes `None`.
# ... (rest of previous changelog entries are omitted for brevity but assumed present)
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
from .tabs.location_tab import LocationTab
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

        # Initialize tab attributes BEFORE super().__init__ if they are to hold instances
        # created by setup_ui (called by super().__init__()).
        # These are declared here for clarity and type hinting.
        self.tab_widget: Optional[QTabWidget] = None
        self.basic_info_tab: Optional[BasicInfoTab] = None
        self.owners_tab: Optional[OwnersTab] = None
        self.location_tab: Optional[LocationTab] = None

        super().__init__()  # This calls self.setup_ui(), which will create the tab instances

        # These attributes are correctly initialized after setup_ui
        self.horses_list: List[Horse] = []
        self.current_horse: Optional[Horse] = None
        self._has_changes_in_active_tab: bool = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # DO NOT re-assign tab instance variables to None here, as setup_ui has already created them.
        # Example of incorrect lines that were removed:
        # self.basic_info_tab: Optional[BasicInfoTab] = None # ERRONEOUS if after super().__init__()
        # self.owners_tab: Optional[OwnersTab] = None       # ERRONEOUS if after super().__init__()
        # self.location_tab: Optional[LocationTab] = None   # ERRONEOUS if after super().__init__()

        QTimer.singleShot(100, self.load_initial_data)

        self.logger.info(
            "HorseUnifiedManagement screen __init__ finished (initial data load deferred)."
        )
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.__INIT__ END: self.tab_widget is {type(self.tab_widget)}, self.basic_info_tab is {type(self.basic_info_tab)} ---"
        )

    def showEvent(self, event: QShowEvent):
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.SHOWEVENT START: self.tab_widget is {type(self.tab_widget)} ---"
        )
        self.logger.info("HorseUnifiedManagement showEvent triggered.")
        super().showEvent(event)
        if self.current_horse:
            self.display_details_state()
        else:
            self.display_empty_state()
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
            QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY}; }}
            QDateEdit::up-button, QDateEdit::down-button {{ width: 18px; }}
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
        # ... (style methods unchanged) ...
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

    def setup_ui(self):
        print("--- HORSEUNIFIEDMANAGEMENT.SETUP_UI CALLED (UNCONDITIONAL PRINT) ---")
        self.logger.debug("HorseUnifiedManagement.setup_ui: START")
        self.set_title("Horse Management")
        self.resize(1200, 800)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_header(main_layout)
        self.setup_action_bar(main_layout)
        self.setup_main_content(main_layout)
        self.setup_footer(main_layout)
        self.setup_connections()

        # !!! USER ACTION REQUIRED !!!
        # The log indicates add_new_horse() is being called during setup_ui.
        # This is incorrect and causes the "Add Horse" button to be disabled.
        # Please search your setup_ui method and its called sub-methods
        # (setup_main_content, setup_horse_details_panel, etc.)
        # for any direct call to self.add_new_horse() or add_new_horse()
        # and REMOVE IT. It should only be called by button clicks or shortcuts.
        # For example, if you see a line like `self.add_new_horse()` here, delete it.

        self.logger.debug("HorseUnifiedManagement.setup_ui: END")
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.SETUP_UI END: self.tab_widget is {type(self.tab_widget)}, self.basic_info_tab is {type(self.basic_info_tab)} ---"
        )

    def setup_header(self, parent_layout):
        # ... (unchanged) ...
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
        # ... (unchanged) ...
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
        self.edit_horse_btn = QPushButton("✓ Edit Selected")  # Changed text for clarity
        action_button_style = self.get_generic_button_style()
        add_btn_bg_color = DARK_PRIMARY_ACTION  # Use a primary action color
        if len(add_btn_bg_color) == 4:  # Expand 3-digit hex
            add_btn_bg_color = f"#{add_btn_bg_color[1]*2}{add_btn_bg_color[2]*2}{add_btn_bg_color[3]*2}"

        self.add_horse_btn.setStyleSheet(
            action_button_style.replace(
                DARK_BUTTON_BG, add_btn_bg_color + "B3"
            ).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white;"
            )  # Primary with alpha
        )
        self.edit_horse_btn.setStyleSheet(
            action_button_style
        )  # Standard button for edit

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
        # ... (unchanged, except for the NOTE about the rogue call if it's in here) ...
        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_MAIN_CONTENT CALLED (UNCONDITIONAL PRINT) ---"
        )
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
        # ... (unchanged) ...
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
        # ... (unchanged, except for the NOTE about the rogue call if it's in here) ...
        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_DETAILS_PANEL CALLED (UNCONDITIONAL PRINT) ---"
        )
        self.logger.debug("setup_horse_details_panel: START")
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

        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_DETAILS_PANEL: BEFORE setup_horse_header_details (UNCONDITIONAL PRINT) ---"
        )
        self.setup_horse_header_details(details_content_layout)  # CALL 1
        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_DETAILS_PANEL: AFTER setup_horse_header_details, BEFORE setup_horse_tabs (UNCONDITIONAL PRINT) ---"
        )
        self.setup_horse_tabs(
            details_content_layout
        )  # CALL 2 - THIS IS WHERE self.tab_widget IS SET
        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_DETAILS_PANEL: AFTER setup_horse_tabs (UNCONDITIONAL PRINT) ---"
        )

        self.setup_empty_state()  # For when no horse is selected

        self.details_layout.addWidget(self.empty_frame)  # Add empty state first
        self.details_layout.addWidget(
            self.horse_details_content_widget
        )  # Add actual content widget

        self.horse_details_content_widget.hide()  # Hide details until a horse is selected
        self.splitter.addWidget(self.details_widget)
        self.logger.debug("setup_horse_details_panel: END")

    def setup_empty_state(self):
        # ... (unchanged) ...
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

    def setup_horse_header_details(self, parent_layout):
        # ... (unchanged) ...
        print(
            "--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_HEADER_DETAILS CALLED (UNCONDITIONAL PRINT) ---"
        )
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

    def setup_horse_tabs(self, parent_layout_for_tabs):
        # ... (unchanged) ...
        try:
            print("--- SETUP_HORSE_TABS: START (UNCONDITIONAL PRINT) ---")
            self.logger.debug("setup_horse_tabs: START")
            self.tab_widget = QTabWidget()
            print(
                f"--- SETUP_HORSE_TABS: self.tab_widget INITIALIZED TO TYPE: {type(self.tab_widget)} (UNCONDITIONAL PRINT) ---"
            )
            self.logger.debug(
                f"setup_horse_tabs: self.tab_widget initialized to: {type(self.tab_widget)}"
            )

            self.tab_widget.setObjectName("DetailsTabWidget")
            self.tab_widget.setStyleSheet(
                f"""
                QTabWidget#DetailsTabWidget::pane {{
                    border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND};
                    border-radius: 6px;
                    margin-top: -1px;
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
                    border-bottom-color: {DARK_WIDGET_BACKGROUND};
                }}
                QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; color: {DARK_TEXT_PRIMARY}; }}
                QTabBar {{ border: none; background-color: transparent; margin-bottom: 0px; }}
            """
            )

            self.basic_info_tab = BasicInfoTab(self, self.horse_controller)
            # Connections for basic_info_tab are in setup_connections()

            self.owners_tab = OwnersTab(
                self, self.horse_controller, self.owner_controller
            )
            # Connections for owners_tab are in setup_connections()

            self.location_tab = LocationTab(
                self, self.horse_controller, self.location_controller
            )
            # Connections for location_tab are in setup_connections()

            self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")
            self.tab_widget.addTab(self.owners_tab, "👥 Owners")
            self.tab_widget.addTab(self.location_tab, "📍 Location")

            placeholder_tab_names = ["💰 Billing", "📊 History"]
            for name in placeholder_tab_names:
                placeholder_widget = QWidget()
                placeholder_widget.setStyleSheet(
                    f"background-color: {DARK_WIDGET_BACKGROUND};"
                )
                placeholder_layout = QVBoxLayout(placeholder_widget)
                placeholder_label = QLabel(f"Content for {name} tab.")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_label.setStyleSheet(
                    f"color: {DARK_TEXT_SECONDARY}; background: transparent;"
                )
                placeholder_layout.addWidget(placeholder_label)
                self.tab_widget.addTab(placeholder_widget, name)

            parent_layout_for_tabs.addWidget(self.tab_widget, 1)
            print(
                f"--- SETUP_HORSE_TABS: END. self.tab_widget TYPE IS: {type(self.tab_widget)}, VISIBLE: {self.tab_widget.isVisible() if self.tab_widget else 'N/A'} (UNCONDITIONAL PRINT) ---"
            )
            self.logger.debug(
                f"setup_horse_tabs: END, self.tab_widget is now: {type(self.tab_widget)}, visible: {self.tab_widget.isVisible() if self.tab_widget else 'N/A'}"
            )
        except Exception as e:
            print(f"--- EXCEPTION IN setup_horse_tabs: {e} ---")
            self.logger.error(f"CRITICAL ERROR in setup_horse_tabs: {e}", exc_info=True)
            self.tab_widget = None
            self.basic_info_tab = None  # Explicitly set to None on error
            self.owners_tab = None
            self.location_tab = None

    def _handle_location_assignment_change(self, location_data: Dict):
        # ... (unchanged) ...
        self.logger.info(
            f"HorseUnifiedManagement received location_assignment_changed: {location_data}"
        )
        new_location_id = location_data.get("id")
        new_location_name = location_data.get("name", "N/A")

        if hasattr(self, "basic_info_tab") and self.basic_info_tab:
            self.basic_info_tab.update_displayed_location(
                new_location_id, new_location_name
            )
            self.logger.debug(
                f"Called basic_info_tab.update_displayed_location with ID={new_location_id}, Name='{new_location_name}'"
            )

        if self.current_horse:
            self.current_horse.current_location_id = new_location_id
            if new_location_id is not None:
                loc_obj = self.location_controller.get_location_by_id(new_location_id)
                self.current_horse.location = loc_obj
            else:
                self.current_horse.location = None

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

    def _on_tab_data_modified(self):
        # ... (unchanged) ...
        if not self._has_changes_in_active_tab:
            self.logger.debug(
                "Change detected in active tab's form (e.g., BasicInfoTab)."
            )
            self._has_changes_in_active_tab = True
            self.update_main_action_buttons_state()

    def _on_owner_association_changed(self, message: str):
        # ... (unchanged) ...
        self.update_status(message)
        self._has_changes_in_active_tab = True
        self.update_main_action_buttons_state()

    def handle_toggle_active_status_from_tab(self, current_status: bool):
        # ... (unchanged) ...
        if self.current_horse:
            self.handle_toggle_active_status()
        else:
            self.logger.warning(
                "Toggle active requested from tab, but no current horse selected."
            )

    def setup_footer(self, parent_layout):
        # ... (unchanged) ...
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_SECONDARY};
                border: none; border-top: 1px solid {DARK_BORDER}; padding: 0 15px; font-size: 11px;
            }}
            QStatusBar::item {{ border: none; }}
            QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; font-size: 11px; }}
        """
        )
        parent_layout.addWidget(self.status_bar)

        self.status_label = QLabel("Ready")
        self.footer_horse_count_label = QLabel("Showing 0 of 0 horses")
        self.shortcut_label = QLabel("F5=Refresh")

        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.footer_horse_count_label)
        separator_label = QLabel(" | ")
        separator_label.setStyleSheet(
            f"color: {DARK_BORDER}; background: transparent; margin: 0 5px;"
        )
        self.status_bar.addPermanentWidget(separator_label)
        self.status_bar.addPermanentWidget(self.shortcut_label)

    def save_changes(self):
        # ... (unchanged) ...
        if not self.basic_info_tab:
            self.logger.error("BasicInfoTab is not initialized. Cannot save.")
            self.show_error("Save Error", "Cannot retrieve horse data to save.")
            return

        if not self._has_changes_in_active_tab:
            self.update_status("No changes to save.")
            return

        horse_data_to_save = self.basic_info_tab.get_data()
        if horse_data_to_save is None:
            self.logger.warning(
                "No data retrieved from BasicInfoTab to save, though changes were flagged."
            )
            return

        location_id_being_saved = horse_data_to_save.get("current_location_id")
        self.logger.info(
            f"Attempting to save horse data. current_location_id in data: {location_id_being_saved}"
        )

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
                op_success, op_message = self.horse_controller.update_horse(
                    self.current_horse.horse_id, horse_data_to_save, self.current_user
                )
                success = op_success
                message = op_message
                if success:
                    saved_horse_id = self.current_horse.horse_id
            else:
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
                self.load_horses()
                if saved_horse_id:
                    for i in range(self.horse_list.count()):
                        item = self.horse_list.item(i)
                        if (
                            item
                            and item.data(Qt.ItemDataRole.UserRole) == saved_horse_id
                        ):
                            self.horse_list.setCurrentRow(i)
                            break
                self.update_main_action_buttons_state()
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
        # ... (unchanged) ...
        self.horse_list.clear()
        for horse in self.horses_list:
            item = QListWidgetItem()
            item_widget = self.horse_list.create_horse_list_item_widget(horse)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)
            self.horse_list.addItem(item)
            self.horse_list.setItemWidget(item, item_widget)

        total_horses_count = len(self.horse_controller.search_horses(status="all"))
        self.footer_horse_count_label.setText(
            f"Showing {self.horse_list.count()} of {total_horses_count} total horses"
        )

    def load_initial_data(self):
        # ... (unchanged) ...
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.LOAD_INITIAL_DATA START: self.tab_widget is {type(self.tab_widget)} ---"
        )
        self.logger.info("load_initial_data called.")
        self.load_horses()
        self.update_status("Initialization complete. Ready.")

    def load_horses(self):
        # ... (unchanged) ...
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.LOAD_HORSES START: self.tab_widget is {type(self.tab_widget)} ---"
        )
        try:
            if not hasattr(self, "search_input") or not hasattr(self, "status_label"):
                self.logger.error(
                    "load_horses called before UI elements are initialized."
                )
                return

            search_term = self.search_input.text()
            status_filter = "active"
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
            self.populate_horse_list()

            reselected_item = False
            if selected_id_before_load is not None:
                for i in range(self.horse_list.count()):
                    item = self.horse_list.item(i)
                    if (
                        item
                        and item.data(Qt.ItemDataRole.UserRole)
                        == selected_id_before_load
                    ):
                        self.horse_list.setCurrentItem(item)
                        reselected_item = True
                        break

            if not reselected_item and self.horse_list.count() > 0:
                self.horse_list.setCurrentRow(0)
            elif not self.horses_list:
                self.display_empty_state()

            self.update_status(f"Loaded {len(self.horses_list)} horses.")
        except AttributeError as ae:
            self.logger.error(f"AttributeError during load_horses: {ae}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error loading horses: {e}", exc_info=True)
            self.show_error("Load Error", f"Failed to load horse list: {e}")
            self.horses_list = []
            self.populate_horse_list()
            self.display_empty_state()

    def on_search_text_changed(self):
        # ... (unchanged) ...
        self.search_timer.stop()
        self.search_timer.start(350)

    def perform_search(self):
        # ... (unchanged) ...
        self.load_horses()

    def on_filter_changed(self):
        # ... (unchanged) ...
        sender = self.sender()
        if isinstance(sender, QRadioButton) and sender.isChecked():
            self.load_horses()

    def on_selection_changed(self):
        # ... (unchanged) ...
        self.logger.debug(
            f"on_selection_changed: START. self.tab_widget is: {type(self.tab_widget)}"
        )
        selected_items = self.horse_list.selectedItems()
        new_selected_id = None
        if selected_items:
            new_selected_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        current_selected_id = (
            self.current_horse.horse_id if self.current_horse else None
        )

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
                self.horse_list.blockSignals(True)
                if current_selected_id is not None:
                    for i in range(self.horse_list.count()):
                        item = self.horse_list.item(i)
                        if (
                            item
                            and item.data(Qt.ItemDataRole.UserRole)
                            == current_selected_id
                        ):
                            self.horse_list.setCurrentRow(i)
                            break
                else:
                    self.horse_list.clearSelection()
                self.horse_list.blockSignals(False)
                return

        self._has_changes_in_active_tab = False
        if new_selected_id is not None:
            self.load_horse_details(new_selected_id)
        else:
            self.display_empty_state()
        self.update_main_action_buttons_state()

    def add_new_horse(self):
        print(
            "--- HORSEUNIFIEDMANAGEMENT.ADD_NEW_HORSE CALLED (UNCONDITIONAL PRINT) ---"
        )
        self.logger.info("Add New Horse button clicked / action triggered.")

        if (
            self._has_changes_in_active_tab
        ):  # Should be false if Add Horse button is enabled
            if not self.show_question(
                "Unsaved Changes", "Discard and start new horse?"
            ):
                return

        self.current_horse = None
        self.horse_list.clearSelection()

        print(
            f"--- ADD_NEW_HORSE: About to call set_new_mode. self.basic_info_tab is: {type(self.basic_info_tab)} ---"
        )
        if self.basic_info_tab:
            self.basic_info_tab.set_new_mode()  # This should now work and print its own message
        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(None)
        if self.location_tab:
            self.location_tab.load_location_for_horse(None)

        self.horse_title.setText("New Horse Record")
        self.horse_info_line.setText(
            "Account: N/A | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A | 📍 N/A"
        )

        self.display_details_state()
        if self.tab_widget and self.basic_info_tab:
            self.tab_widget.setCurrentWidget(self.basic_info_tab)

        self._has_changes_in_active_tab = True
        self.update_main_action_buttons_state()

        if self.basic_info_tab:
            self.basic_info_tab.update_buttons_state(True, False)
        if self.owners_tab:
            self.owners_tab.update_buttons_state()
        if self.location_tab:
            self.location_tab.update_buttons_state()

        self.update_status("Enter details for new horse.")

    def edit_selected_horse(self):
        # ... (unchanged) ...
        self.logger.debug(
            f"edit_selected_horse TOP: self.current_horse is {'set' if self.current_horse else 'None'}. self.tab_widget is: {self.tab_widget}"
        )
        if self.current_horse:
            if self.tab_widget is None:
                self.logger.error(
                    "CRITICAL: self.tab_widget is None in edit_selected_horse"
                )
                self.show_error("Critical UI Error", "Tab widget is not available.")
                return
            current_tab_widget = self.tab_widget.currentWidget()
            if current_tab_widget == self.basic_info_tab and self.basic_info_tab:
                self.basic_info_tab.set_form_read_only(False)

            self.update_main_action_buttons_state()
            if hasattr(current_tab_widget, "update_buttons_state"):
                if current_tab_widget == self.basic_info_tab and self.basic_info_tab:
                    self.basic_info_tab.update_buttons_state(True, True)
                elif hasattr(current_tab_widget, "update_buttons_state"):
                    current_tab_widget.update_buttons_state()
            self.update_status(f"Editing: {self.current_horse.horse_name}")
        else:
            self.show_info("Edit Horse", "Please select a horse to edit.")

    def discard_changes(self):
        # ... (unchanged) ...
        if not self._has_changes_in_active_tab:
            return

        if self.show_question("Confirm Discard", "Discard unsaved changes?"):
            if self.current_horse:
                self.load_horse_details(self.current_horse.horse_id)
            else:
                if self.basic_info_tab:
                    self.basic_info_tab.clear_fields(
                        suppress_signal=True
                    )  # Suppress here too
                if self.owners_tab:
                    self.owners_tab.load_owners_for_horse(None)
                if self.location_tab:
                    self.location_tab.load_location_for_horse(None)
                self.display_empty_state()

            self._has_changes_in_active_tab = False
            self.update_main_action_buttons_state()
            self.update_status("Changes discarded.")

    def refresh_data(self):
        # ... (unchanged) ...
        if self._has_changes_in_active_tab:
            if not self.show_question("Unsaved Changes", "Discard and refresh?"):
                return

        self._has_changes_in_active_tab = False
        current_selected_id = (
            self.current_horse.horse_id if self.current_horse else None
        )
        self.load_horses()
        if self.current_horse and self.current_horse.horse_id == current_selected_id:
            self.load_horse_details(self.current_horse.horse_id)
        elif not self.current_horse and current_selected_id is not None:
            self.display_empty_state()
        self.update_main_action_buttons_state()
        self.update_status("Data refreshed.")

    def show_help(self):
        # ... (unchanged) ...
        QMessageBox.information(self, "Help", "Help content will be displayed here.")

    def load_horse_details(self, horse_id: int):
        # ... (unchanged) ...
        print(
            f"--- HORSEUNIFIEDMANAGEMENT.LOAD_HORSE_DETAILS START: self.tab_widget is {type(self.tab_widget)} ---"
        )
        self.logger.info(f"Loading details for horse ID: {horse_id}")
        horse = self.horse_controller.get_horse_by_id(horse_id)
        if not horse:
            self.show_error("Error", f"Could not load details for horse ID {horse_id}.")
            self.display_empty_state()
            return

        self.current_horse = horse
        self._has_changes_in_active_tab = False

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

        if self.basic_info_tab:
            self.basic_info_tab.populate_fields(horse)
        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(horse)
        if self.location_tab:
            self.location_tab.load_location_for_horse(horse)

        self.display_details_state()
        self.update_main_action_buttons_state()
        self.update_status(f"Viewing: {horse.horse_name or 'Unnamed Horse'}")

    def display_empty_state(self):
        print(
            f"--- DISPLAY_EMPTY_STATE: START. self.tab_widget is {type(self.tab_widget)} ---"
        )
        self.logger.debug(
            f"display_empty_state called. self.tab_widget BEFORE HIDE: {type(self.tab_widget)}"
        )

        print(
            f"--- DISPLAY_EMPTY_STATE: Before hide/show. self.tab_widget is {type(self.tab_widget)} ---"
        )
        if hasattr(self, "empty_frame") and self.empty_frame:
            self.empty_frame.show()
        if (
            hasattr(self, "horse_details_content_widget")
            and self.horse_details_content_widget
        ):
            self.horse_details_content_widget.hide()
        print(
            f"--- DISPLAY_EMPTY_STATE: After hide/show. self.tab_widget is {type(self.tab_widget)} ---"
        )

        self.current_horse = None
        self._has_changes_in_active_tab = False  # Reset before clearing fields

        print(
            f"--- DISPLAY_EMPTY_STATE: Check BEFORE basic_info_tab.clear_fields(). self.basic_info_tab is: {type(self.basic_info_tab)} ---"
        )
        if self.basic_info_tab:
            self.basic_info_tab.clear_fields(
                suppress_signal=True
            )  # MODIFIED: Suppress signal
        print(
            f"--- DISPLAY_EMPTY_STATE: After basic_info_tab.clear_fields(). self.tab_widget is {type(self.tab_widget)}, self.basic_info_tab is {type(self.basic_info_tab)} ---"
        )

        if self.owners_tab:
            self.owners_tab.load_owners_for_horse(None)
        print(
            f"--- DISPLAY_EMPTY_STATE: After owners_tab.load_owners_for_horse(None). self.tab_widget is {type(self.tab_widget)} ---"
        )

        if self.location_tab:
            self.location_tab.load_location_for_horse(None)
        print(
            f"--- DISPLAY_EMPTY_STATE: After location_tab.load_location_for_horse(None). self.tab_widget is {type(self.tab_widget)} ---"
        )

        self.update_main_action_buttons_state()  # This will now use the corrected _has_changes_in_active_tab
        self.logger.debug(
            f"display_empty_state finished. self.tab_widget AFTER HIDE: {type(self.tab_widget)}"
        )
        print(
            f"--- DISPLAY_EMPTY_STATE: END. self.tab_widget is {type(self.tab_widget)} ---"
        )

    def display_details_state(self):
        # ... (unchanged) ...
        self.logger.debug(
            f"display_details_state called. self.tab_widget BEFORE SHOW: {type(self.tab_widget)}"
        )
        if hasattr(self, "empty_frame") and self.empty_frame:
            self.empty_frame.hide()
        if (
            hasattr(self, "horse_details_content_widget")
            and self.horse_details_content_widget
        ):
            self.horse_details_content_widget.show()
        self.logger.debug(
            f"display_details_state finished. self.tab_widget AFTER SHOW: {type(self.tab_widget)}"
        )

    def update_status(self, message, timeout=4000):
        # ... (unchanged) ...
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.setText(message)
            if timeout > 0:
                QTimer.singleShot(
                    timeout, lambda: self.clear_status_if_matches(message)
                )

    def clear_status_if_matches(self, original_message):
        # ... (unchanged) ...
        if (
            hasattr(self, "status_label")
            and self.status_label
            and self.status_label.text() == original_message
        ):
            self.status_label.setText("Ready")

    def update_main_action_buttons_state(self):
        # ... (Diagnostic print retained) ...
        can_edit = (
            self.current_horse is not None and not self._has_changes_in_active_tab
        )
        if hasattr(self, "edit_horse_btn") and self.edit_horse_btn:
            self.edit_horse_btn.setEnabled(can_edit)
        if hasattr(self, "add_horse_btn") and self.add_horse_btn:
            self.add_horse_btn.setEnabled(not self._has_changes_in_active_tab)
            print(
                f"--- UPDATE_MAIN_ACTION_BUTTONS_STATE: Add Horse Button Enabled: {self.add_horse_btn.isEnabled()} (_has_changes_in_active_tab: {self._has_changes_in_active_tab}) ---"
            )

        if self.tab_widget:
            current_tab = self.tab_widget.currentWidget()
            if hasattr(current_tab, "update_buttons_state"):
                if current_tab == self.basic_info_tab and self.basic_info_tab:
                    self.basic_info_tab.update_buttons_state(
                        self._has_changes_in_active_tab, self.current_horse is not None
                    )
                elif current_tab == self.owners_tab and self.owners_tab:
                    self.owners_tab.update_buttons_state()
                elif current_tab == self.location_tab and self.location_tab:
                    self.location_tab.update_buttons_state()
        else:
            self.logger.warning(
                "update_main_action_buttons_state: self.tab_widget is None."
            )

    def handle_toggle_active_status(self):
        # ... (unchanged) ...
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
                self.load_horse_details(self.current_horse.horse_id)
                self.load_horses()
            else:
                self.show_error(f"{action_text.capitalize()} Failed", message)

    def handle_logout_request_from_menu(self):
        # ... (unchanged) ...
        self.logger.info(f"User '{self.current_user}' requested logout from menu.")
        self.exit_requested.emit()

    def keyPressEvent(self, event: QKeyEvent):
        # ... (unchanged) ...
        key = event.key()
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            if (
                hasattr(self, "add_horse_btn")
                and self.add_horse_btn
                and self.add_horse_btn.isEnabled()
            ):
                self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            current_tab_widget = (
                self.tab_widget.currentWidget() if self.tab_widget else None
            )
            if (
                current_tab_widget == self.basic_info_tab
                and self.basic_info_tab  # Ensure tab exists
                and hasattr(self.basic_info_tab, "save_btn")
                and self.basic_info_tab.save_btn.isEnabled()
            ):
                self.basic_info_tab.save_requested.emit()
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            active_modal = QApplication.activeModalWidget()
            if active_modal and isinstance(active_modal, QDialog):
                active_modal.reject()
            elif self._has_changes_in_active_tab:
                self.discard_changes()
            else:
                self.exit_requested.emit()
        else:
            super().keyPressEvent(event)

    def setup_connections(self):
        # ... (Refined checks for attributes before connecting) ...
        if hasattr(self, "add_horse_btn") and self.add_horse_btn:
            self.add_horse_btn.clicked.connect(self.add_new_horse)
        if hasattr(self, "edit_horse_btn") and self.edit_horse_btn:
            self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        if hasattr(self, "refresh_btn") and self.refresh_btn:
            self.refresh_btn.clicked.connect(self.refresh_data)
        if hasattr(self, "help_btn") and self.help_btn:
            self.help_btn.clicked.connect(self.show_help)
        if hasattr(self, "setup_icon_btn") and self.setup_icon_btn:
            self.setup_icon_btn.clicked.connect(self.setup_requested.emit)

        if hasattr(self, "active_only_radio") and self.active_only_radio:
            self.active_only_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "all_horses_radio") and self.all_horses_radio:
            self.all_horses_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "deactivated_radio") and self.deactivated_radio:
            self.deactivated_radio.toggled.connect(self.on_filter_changed)

        if hasattr(self, "search_input") and self.search_input:
            self.search_input.textChanged.connect(self.on_search_text_changed)
        if hasattr(self, "horse_list") and self.horse_list:
            self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)

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
        if (
            self.location_tab and self.basic_info_tab
        ):  # Ensure both exist for this connection
            self.location_tab.location_assignment_changed.connect(
                self._handle_location_assignment_change
            )
