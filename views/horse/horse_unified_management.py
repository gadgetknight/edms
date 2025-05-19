# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen (Dark Theme)
Version: 1.6.3
Purpose: Unified interface for horse management. Removes syntax error.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.6.3 (2025-05-18):
    - Removed stray Markdown backticks that were causing a SyntaxError.
- v1.6.2 (2025-05-18):
    - Corrected how AppConfig color constants are imported and used (directly from
      the module, not as class attributes of AppConfig).
- v1.6.1 (2025-05-17):
    - Extracted OwnersTab into views.horse.tabs.owners_tab.
- v1.6.0 (2025-05-17): Extracted BasicInfoTab.
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
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
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QMessageBox,
    QStatusBar,
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QKeyEvent

from views.base_view import BaseView
from config.app_config import (
    AppConfig,
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
from models import Horse

from .tabs.basic_info_tab import BasicInfoTab
from .tabs.owners_tab import OwnersTab
from .widgets.horse_list_widget import HorseListWidget


class HorseUnifiedManagement(BaseView):
    horse_selection_changed = Signal(int)
    exit_requested = Signal()
    setup_requested = Signal()

    def __init__(self, current_user=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"HorseUnifiedManagement __init__ started for user: {current_user}"
        )
        self.current_user = current_user or "ADMIN"
        self.horse_controller = HorseController()
        self.owner_controller = OwnerController()
        super().__init__()
        self.horses_list: List[Horse] = []
        self.current_horse: Optional[Horse] = None
        self._has_changes_in_active_tab: bool = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(DARK_WIDGET_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK_ITEM_HOVER))
        dark_palette.setColor(
            QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND)
        )
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_HIGHLIGHT_BG))
        dark_palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(DARK_HIGHLIGHT_TEXT)
        )
        dark_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY)
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(DARK_TEXT_TERTIARY),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(DARK_TEXT_TERTIARY),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Base,
            QColor(DARK_HEADER_FOOTER),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Button,
            QColor(DARK_HEADER_FOOTER),
        )
        self.setPalette(dark_palette)
        self.setAutoFillBackground(True)

        self.load_initial_data()
        self.logger.info("HorseUnifiedManagement screen __init__ finished.")

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
        if len(bg_color_hex) == 4 and bg_color_hex.startswith("#"):
            bg_color_hex = f"#{bg_color_hex[1]*2}{bg_color_hex[2]*2}{bg_color_hex[3]*2}"
        try:
            r = int(bg_color_hex[1:3], 16)
            g = int(bg_color_hex[3:5], 16)
            b = int(bg_color_hex[5:7], 16)
            hover_bg = f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
            pressed_bg = f"#{max(0,r-40):02x}{max(0,g-40):02x}{max(0,b-40):02x}"
        except ValueError:
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
        self.logger.debug("HorseUnifiedManagement setup_ui started.")
        self.set_title("Horse Management")
        self.resize(1200, 800)
        self.center_on_screen()
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setup_header(main_layout)
        self.setup_action_bar(main_layout)
        self.setup_main_content(main_layout)
        self.setup_footer(main_layout)
        self.setup_connections()
        self.logger.debug("Dark Theme UI setup complete.")

    def setup_header(self, parent_layout):
        self.logger.debug("setup_header started.")
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
            QPushButton#UserMenuButton::menu-indicator {{ image: none; }}
            QPushButton#UserMenuButton:hover {{
                color: {DARK_TEXT_PRIMARY};
                background-color: {QColor(DARK_ITEM_HOVER).lighter(110).name(QColor.NameFormat.HexRgb)}33;
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
        breadcrumb_label = QLabel("🏠 Horse Management")
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
        self.user_menu_button.setFlat(True)
        self.user_menu = QMenu(self)
        self.user_menu.setStyleSheet(
            f"""
            QMenu {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; padding: 5px;
            }}
            QMenu::item {{ padding: 5px 20px 5px 20px; min-width: 100px; }}
            QMenu::item:selected {{
                background-color: {DARK_HIGHLIGHT_BG}70; color: {DARK_HIGHLIGHT_TEXT};
            }}
            QMenu::separator {{
                height: 1px; background: {DARK_BORDER};
                margin-left: 5px; margin-right: 5px;
            }}
            """
        )
        logout_action = QAction("Log Out", self)
        logout_action.triggered.connect(self.handle_logout_request)
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
        self.logger.debug("setup_header finished.")

    def setup_action_bar(self, parent_layout):
        self.logger.debug("setup_action_bar started.")
        action_bar_frame = QFrame()
        action_bar_frame.setObjectName("ActionBarFrame")
        action_bar_frame.setFixedHeight(50)
        action_bar_frame.setStyleSheet(
            f"""
            #ActionBarFrame {{
                background-color: {DARK_BACKGROUND}; border: none;
                border-bottom: 1px solid {DARK_BORDER}; padding: 0 20px;
            }}
            QPushButton {{ min-height: 30px; }}
            QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; }}
            QRadioButton::indicator {{ width: 13px; height: 13px; }}
            QRadioButton {{ color: {DARK_TEXT_SECONDARY}; background: transparent; padding: 5px; }}
            """
        )
        action_bar_layout = QHBoxLayout(action_bar_frame)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
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
        )
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
        )
        action_bar_layout.addWidget(self.search_input)
        self.edit_horse_btn.setEnabled(False)
        parent_layout.addWidget(action_bar_frame)
        self.logger.debug("setup_action_bar finished.")

    def setup_main_content(self, parent_layout):
        self.logger.debug("setup_main_content started.")
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(
            f"""
            QSplitter {{ background-color: {DARK_BACKGROUND}; border: none; }}
            QSplitter::handle {{ background-color: {DARK_BORDER}; }}
            QSplitter::handle:horizontal {{ width: 1px; }}
            QSplitter::handle:pressed {{ background-color: {DARK_TEXT_SECONDARY}; }}
            """
        )
        self.setup_horse_list_panel()
        self.setup_horse_details_panel()
        self.splitter.setSizes([300, 850])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        parent_layout.addWidget(self.splitter, 1)
        self.logger.debug("setup_main_content finished.")

    def setup_horse_list_panel(self):
        self.logger.debug("setup_horse_list_panel started.")
        self.list_widget_container = QWidget()
        self.list_widget_container.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none; border-right: 1px solid {DARK_BORDER};"
        )
        list_layout = QVBoxLayout(self.list_widget_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        self.horse_list = HorseListWidget()
        self.horse_list.setMinimumWidth(250)
        list_layout.addWidget(self.horse_list, 1)
        self.splitter.addWidget(self.list_widget_container)
        self.logger.debug("setup_horse_list_panel finished.")

    def setup_horse_details_panel(self, parent_layout_for_tabs=None):
        self.logger.debug("setup_horse_details_panel started.")
        self.details_widget = QWidget()
        self.details_widget.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none;"
        )
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(15, 10, 15, 10)
        self.details_layout.setSpacing(15)
        self.horse_details_content_widget = QWidget()
        details_content_layout = QVBoxLayout(self.horse_details_content_widget)
        details_content_layout.setContentsMargins(0, 0, 0, 0)
        details_content_layout.setSpacing(15)
        self.setup_horse_header_details(details_content_layout)
        self.setup_horse_tabs(details_content_layout)
        self.setup_empty_state()
        self.details_layout.addWidget(self.empty_frame)
        self.details_layout.addWidget(self.horse_details_content_widget)
        self.horse_details_content_widget.hide()
        self.splitter.addWidget(self.details_widget)
        self.logger.debug("setup_horse_details_panel finished.")

    def setup_empty_state(self):
        self.logger.debug("setup_empty_state started.")
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
        self.logger.debug("setup_empty_state finished.")

    def setup_horse_header_details(self, parent_layout):
        self.logger.debug("setup_horse_header_details started.")
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        self.horse_title = QLabel("Horse Name")
        self.horse_title.setFont(QFont(DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold))
        self.horse_title.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )
        self.horse_info_line = QLabel(
            "Account: N/A | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A"
        )
        self.horse_info_line.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        self.horse_info_line.setWordWrap(True)
        header_layout.addWidget(self.horse_title)
        header_layout.addWidget(self.horse_info_line)
        parent_layout.addWidget(header_widget)
        self.logger.debug("setup_horse_header_details finished.")

    def setup_horse_tabs(self, parent_layout_for_tabs):
        self.logger.debug("setup_horse_tabs started.")
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DetailsTabWidget")
        self.tab_widget.setStyleSheet(
            f"""
            QTabWidget#DetailsTabWidget::pane {{
                border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND};
                border-radius: 6px; margin-top: -1px;
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
                border-color: {DARK_BORDER}; border-bottom-color: {DARK_WIDGET_BACKGROUND};
            }}
            QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; color: {DARK_TEXT_PRIMARY}; }}
            QTabBar {{ border: none; background-color: transparent; margin-bottom: 0px; }}
            """
        )
        self.basic_info_tab = BasicInfoTab(self, self.horse_controller)
        self.basic_info_tab.data_modified.connect(self._on_tab_data_modified)
        self.basic_info_tab.save_requested.connect(self.save_changes)
        self.basic_info_tab.discard_requested.connect(self.discard_changes)
        self.basic_info_tab.toggle_active_requested.connect(
            self.handle_toggle_active_status_from_tab
        )
        self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")
        self.load_locations_into_basic_info_tab()

        self.owners_tab = OwnersTab(self, self.horse_controller, self.owner_controller)
        self.owners_tab.owner_association_changed.connect(
            self._on_owner_association_changed
        )
        self.tab_widget.addTab(self.owners_tab, "👥 Owners")

        placeholder_tab_names = ["📍 Location", "💰 Billing", "📊 History"]
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
        self.logger.debug("setup_horse_tabs finished.")

    def load_locations_into_basic_info_tab(self):
        if hasattr(self, "basic_info_tab") and self.basic_info_tab:
            try:
                locations = self.horse_controller.get_locations_list()
                locations_data_for_combo = [
                    {"id": loc.location_id, "name": loc.location_name}
                    for loc in locations
                ]
                self.basic_info_tab.populate_locations_combo(locations_data_for_combo)
            except Exception as e:
                self.logger.error(
                    f"Error loading locations for BasicInfoTab: {e}", exc_info=True
                )
                self.show_error("Load Error", "Failed to load locations for form.")

    def _on_tab_data_modified(self):
        if not self._has_changes_in_active_tab:
            self.logger.debug("Change detected in active tab's form.")
            self._has_changes_in_active_tab = True
            self.update_main_action_buttons_state()

    def _on_owner_association_changed(self, message: str):
        self.update_status(message)

    def handle_toggle_active_status_from_tab(self, current_status: bool):
        if self.current_horse:
            self.handle_toggle_active_status()
        else:
            self.logger.warning(
                "Toggle active requested from tab, but no current horse selected."
            )

    def setup_footer(self, parent_layout):
        self.logger.debug("setup_footer started.")
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
        self.logger.debug("setup_footer finished.")

    def save_changes(self):
        if not self._has_changes_in_active_tab:
            self.update_status("No changes to save.")
            return

        current_tab_widget = self.tab_widget.currentWidget()
        if not hasattr(current_tab_widget, "get_data"):
            self.logger.warning("Current tab does not support get_data(). Cannot save.")
            self.show_error("Save Error", "Cannot save changes from the current tab.")
            return

        horse_data_from_tab = current_tab_widget.get_data()
        if horse_data_from_tab is None:
            self.logger.warning("No data retrieved from current tab to save.")
            return

        is_new_horse = self.current_horse is None
        self.logger.info(
            f"Attempting to save changes from tab. New horse: {is_new_horse}"
        )

        is_valid, errors = self.horse_controller.validate_horse_data(
            horse_data_from_tab
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
                self.logger.info(f"Updating horse ID: {self.current_horse.horse_id}")
                op_success, op_message = self.horse_controller.update_horse(
                    self.current_horse.horse_id, horse_data_from_tab, self.current_user
                )
                success = op_success
                message = op_message
                if success:
                    saved_horse_id = self.current_horse.horse_id
            else:
                self.logger.info("Creating new horse.")
                op_success, op_message, new_horse_obj = (
                    self.horse_controller.create_horse(
                        horse_data_from_tab, self.current_user
                    )
                )
                success = op_success
                message = op_message
                if success and new_horse_obj:
                    saved_horse_id = new_horse_obj.horse_id
                    self.logger.info(f"New horse created with ID: {saved_horse_id}")

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
                if hasattr(current_tab_widget, "update_buttons_state"):
                    current_tab_widget.update_buttons_state(
                        False, True if self.current_horse else False
                    )
                self.update_status(
                    f"Saved: {horse_data_from_tab.get('horse_name', 'Unknown Horse')}"
                )
            else:
                self.show_error(
                    "Save Failed", message if message else "Unknown error during save."
                )
        except Exception as e:
            self.logger.error(f"Exception during save operation: {e}", exc_info=True)
            self.show_error("Save Error", f"An unexpected error occurred: {e}")

    def populate_horse_list(self):
        self.horse_list.clear()
        self.logger.debug(f"Populating list with {len(self.horses_list)} horses.")
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
        self.logger.debug("Horse list population complete.")

    def load_initial_data(self):
        self.logger.debug("load_initial_data called")
        self.load_horses()
        self.update_status("Initialization complete. Ready.")

    def load_horses(self):
        try:
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
            self.show_error(
                "Load Error", f"A problem occurred: {ae}. Please check logs."
            )
        except Exception as e:
            self.logger.error(f"Error loading horses: {e}", exc_info=True)
            self.show_error("Load Error", f"Failed to load horse list: {e}")
            self.horses_list = []
            self.populate_horse_list()
            self.display_empty_state()

    def on_search_text_changed(self):
        self.search_timer.stop()
        self.search_timer.start(350)
        self.logger.debug("Search timer started/restarted.")

    def perform_search(self):
        self.logger.info("Performing search...")
        self.load_horses()

    def on_filter_changed(self):
        sender = self.sender()
        if isinstance(sender, QRadioButton) and sender.isChecked():
            self.logger.info(f"Filter changed to: {sender.text()}")
            self.load_horses()

    def on_selection_changed(self):
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
                self.horse_list.blockSignals(False)
                return

        self._has_changes_in_active_tab = False
        if new_selected_id is not None:
            self.logger.info(f"Horse selected: ID {new_selected_id}")
            self.load_horse_details(new_selected_id)
        else:
            self.logger.info("Horse selection cleared.")
            self.display_empty_state()
        self.update_main_action_buttons_state()

    def add_new_horse(self):
        if self._has_changes_in_active_tab:
            reply = self.show_question(
                "Unsaved Changes",
                "You have unsaved changes. Discard and start new horse?",
            )
            if not reply:
                return

        self.logger.info("Initiating add new horse.")
        self.current_horse = None
        self.horse_list.clearSelection()

        self.basic_info_tab.set_new_mode()
        if hasattr(self, "owners_tab"):
            self.owners_tab.load_owners_for_horse(None)

        self.horse_title.setText("New Horse Record")
        self.horse_info_line.setText("Enter details below")
        self.display_details_state()
        self.tab_widget.setCurrentWidget(self.basic_info_tab)

        self._has_changes_in_active_tab = True
        self.update_main_action_buttons_state()
        self.basic_info_tab.update_buttons_state(True, False)
        if hasattr(self, "owners_tab"):
            self.owners_tab.update_buttons_state()
        self.update_status("Enter details for new horse.")

    def edit_selected_horse(self):
        if self.current_horse:
            self.logger.info(
                f"Enabling edit for horse: {self.current_horse.horse_name}"
            )
            current_tab_widget = self.tab_widget.currentWidget()
            if current_tab_widget == self.basic_info_tab:
                self.basic_info_tab.set_form_read_only(False)
            self.update_main_action_buttons_state()
            if hasattr(current_tab_widget, "update_buttons_state"):
                current_tab_widget.update_buttons_state(
                    self._has_changes_in_active_tab, True
                )
            self.update_status(f"Editing: {self.current_horse.horse_name}")
        else:
            self.show_info("Edit Horse", "Please select a horse from the list to edit.")

    def discard_changes(self):
        if not self._has_changes_in_active_tab:
            return
        self.logger.info("Discarding changes...")
        if self.show_question(
            "Confirm Discard", "Are you sure you want to discard unsaved changes?"
        ):
            current_tab_widget = self.tab_widget.currentWidget()
            if self.current_horse:
                if current_tab_widget == self.basic_info_tab:
                    self.basic_info_tab.populate_fields(self.current_horse)
            else:
                if current_tab_widget == self.basic_info_tab:
                    self.basic_info_tab.clear_fields()
                self.display_empty_state()
            self._has_changes_in_active_tab = False
            self.update_main_action_buttons_state()
            if hasattr(current_tab_widget, "update_buttons_state"):
                current_tab_widget.update_buttons_state(
                    False, self.current_horse is not None
                )
            self.update_status("Changes discarded.")
        else:
            self.logger.info("User cancelled discard operation.")

    def refresh_data(self):
        if self._has_changes_in_active_tab:
            if not self.show_question(
                "Unsaved Changes", "You have unsaved changes. Discard and refresh?"
            ):
                return
        self.logger.info("Refreshing data...")
        self._has_changes_in_active_tab = False
        current_selected_id = (
            self.current_horse.horse_id if self.current_horse else None
        )
        self.load_horses()
        if self.current_horse:
            if self.current_horse.horse_id != current_selected_id:
                self.load_horse_details(self.current_horse.horse_id)
            else:
                if hasattr(self, "basic_info_tab"):
                    self.basic_info_tab.populate_fields(self.current_horse)
                if hasattr(self, "owners_tab"):
                    self.owners_tab.load_owners_for_horse(self.current_horse)
        elif current_selected_id is not None:
            self.display_empty_state()
        self.update_main_action_buttons_state()
        self.update_status("Data refreshed.")

    def show_help(self):
        self.logger.debug("Showing help information...")
        QMessageBox.information(self, "Help", "Help content will be displayed here.")

    def load_horse_details(self, horse_id: int):
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
        if hasattr(self, "basic_info_tab"):
            self.basic_info_tab.populate_fields(horse)
        if hasattr(self, "owners_tab"):
            self.owners_tab.load_owners_for_horse(horse)
        self.display_details_state()
        self.update_main_action_buttons_state()
        self.update_status(f"Viewing: {horse.horse_name or 'Unnamed Horse'}")

    def display_empty_state(self):
        self.logger.debug("Displaying empty state for horse details.")
        self.empty_frame.show()
        self.horse_details_content_widget.hide()
        self.current_horse = None
        self._has_changes_in_active_tab = False
        if hasattr(self, "basic_info_tab"):
            self.basic_info_tab.clear_fields()
        if hasattr(self, "owners_tab"):
            self.owners_tab.load_owners_for_horse(None)
        self.update_main_action_buttons_state()

    def display_details_state(self):
        self.logger.debug("Displaying horse details state.")
        self.empty_frame.hide()
        self.horse_details_content_widget.show()

    def update_status(self, message, timeout=4000):
        self.logger.debug(f"Status update: {message}")
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.clear_status_if_matches(message))

    def clear_status_if_matches(self, original_message):
        if self.status_label.text() == original_message:
            self.status_label.setText("Ready")

    def update_main_action_buttons_state(self):
        can_edit = (
            self.current_horse is not None and not self._has_changes_in_active_tab
        )
        self.edit_horse_btn.setEnabled(can_edit)
        self.add_horse_btn.setEnabled(not self._has_changes_in_active_tab)
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, "update_buttons_state"):
            current_tab.update_buttons_state(
                self._has_changes_in_active_tab, self.current_horse is not None
            )
        if hasattr(self, "owners_tab") and current_tab == self.owners_tab:
            self.owners_tab.update_buttons_state()

    def handle_toggle_active_status(self):
        if not self.current_horse:
            self.logger.warning("Toggle active status: No current horse selected.")
            return
        action_text = "activate" if not self.current_horse.is_active else "deactivate"
        confirm_message = f"Sure to {action_text} '{self.current_horse.horse_name or f'ID {self.current_horse.horse_id}'}'?"
        if self.show_question(f"Confirm {action_text.capitalize()}", confirm_message):
            self.logger.info(
                f"User confirmed to {action_text} horse ID: {self.current_horse.horse_id}"
            )
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
                self.update_status(message)
            else:
                self.show_error(f"{action_text.capitalize()} Failed", message)
        else:
            self.logger.info(f"User cancelled {action_text} operation.")

    def exit_application(self):
        self.logger.info("Exit requested from Horse Management screen.")
        if self._has_changes_in_active_tab:
            if not self.show_question(
                "Unsaved Changes", "You have unsaved changes. Discard and exit?"
            ):
                return
        self.logger.info("Emitting exit_requested signal to main application.")
        self.exit_requested.emit()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = QApplication.keyboardModifiers()
        self.logger.debug(f"KeyPressEvent: Key={key}, Modifiers={modifiers}")
        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            if self.add_horse_btn.isEnabled():
                self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            current_tab_widget = self.tab_widget.currentWidget()
            if (
                hasattr(current_tab_widget, "save_btn")
                and current_tab_widget.save_btn.isEnabled()
            ):
                current_tab_widget.save_requested.emit()
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            active_modal_widget = QApplication.activeModalWidget()
            if active_modal_widget and isinstance(active_modal_widget, QDialog):
                active_modal_widget.reject()
            elif self._has_changes_in_active_tab:
                super().keyPressEvent(event)
            else:
                self.exit_application()
        else:
            super().keyPressEvent(event)

    def setup_connections(self):
        self.logger.debug("setup_connections started.")
        self.add_horse_btn.clicked.connect(self.add_new_horse)
        self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.help_btn.clicked.connect(self.show_help)
        self.setup_icon_btn.clicked.connect(self.handle_setup_icon_click)
        self.active_only_radio.toggled.connect(self.on_filter_changed)
        self.all_horses_radio.toggled.connect(self.on_filter_changed)
        self.deactivated_radio.toggled.connect(self.on_filter_changed)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.logger.debug("Signal connections established.")

    def handle_setup_icon_click(self):
        self.logger.info("Setup icon clicked, emitting setup_requested signal.")
        self.setup_requested.emit()

    def handle_logout_request(self):
        self.logger.info("Log Out action triggered from user menu.")
        if self._has_changes_in_active_tab:
            reply = self.show_question(
                "Unsaved Changes",
                "You have unsaved changes. Discard changes and log out?",
            )
            if not reply:
                return
        self.exit_requested.emit()
