# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management and System Setup Screen
Version: 1.10.11 (Based on GitHub v1.10.7, incorporating v1.10.8-10 changes)
Purpose: Manages users, system settings, reference data.
         Temporarily simplified _setup_ui to only display a test label,
         to diagnose the "blank unresponsive screen" issue.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.10.11 (2025-05-20):
    - (Based on GitHub v1.10.7, incorporating v1.10.8-10 changes)
    - Drastically simplified `_setup_ui` to only create a basic QVBoxLayout
      on self.central_widget and add a single QLabel to it. All tab setup
      and complex UI elements are temporarily bypassed.
    - `_load_initial_data` is deferred and its internal calls to data loading
      methods are commented out for this test to focus on UI rendering.
- v1.10.10 (2025-05-20):
    - Added helper methods `get_toolbar_button_style` and `get_generic_button_style`.
- v1.10.9 (2025-05-20):
    - Corrected `_load_users_data` for User model attributes & role display.
- v1.10.8 (2025-05-20):
    - Modified `__init__` for `current_user_identifier`. Added debug logs.
- v1.10.7 (2025-05-20):
    - Corrected import for AddEditChargeCodeDialog.
"""

import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QDialog,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer  # Added QTimer for deferred load
from PySide6.QtGui import QColor

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
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_ITEM_HOVER,
)

from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.charge_code_controller import ChargeCodeController
from models import User, Location as LocationModel, ChargeCode as ChargeCodeModel

# Dialogs are not used in this simplified UI test version
# from .dialogs.add_edit_user_dialog import AddEditUserDialog
# from .dialogs.add_edit_location_dialog import AddEditLocationDialog
# from .dialogs.add_edit_change_code_dialog import AddEditChargeCodeDialog


class UserManagementScreen(BaseView):
    exit_requested = Signal()
    horse_management_requested = Signal()

    def __init__(self, current_user_identifier: str):
        super().__init__()
        self.logger = logging.getLogger(__class__.__name__)
        self.current_user_identifier = current_user_identifier

        # Controllers might not be needed if data loading is stubbed
        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.charge_code_controller = ChargeCodeController()

        self._setup_ui()  # This will now be simplified
        QTimer.singleShot(
            100, self._load_initial_data
        )  # Defer even stubbed data loading
        self.logger.info(
            f"UserManagementScreen initialized for user: {self.current_user_identifier}."
        )

    def get_toolbar_button_style(self, bg_color_hex, text_color_hex="#ffffff"):
        # Method kept for completeness if UI is restored, not used by simplified UI
        if len(bg_color_hex) == 4 and bg_color_hex.startswith("#"):
            bg_color_hex = f"#{bg_color_hex[1]*2}{bg_color_hex[2]*2}{bg_color_hex[3]*2}"
        try:
            r_val = int(bg_color_hex[1:3], 16)
            g_val = int(bg_color_hex[3:5], 16)
            b_val = int(bg_color_hex[5:7], 16)
            hover_bg = (
                f"#{max(0,r_val-20):02x}{max(0,g_val-20):02x}{max(0,b_val-20):02x}"
            )
            pressed_bg = (
                f"#{max(0,r_val-40):02x}{max(0,g_val-40):02x}{max(0,b_val-40):02x}"
            )
        except ValueError:
            self.logger.warning(f"Could not parse color: {bg_color_hex}")
            hover_bg = DARK_BUTTON_HOVER
            pressed_bg = DARK_BUTTON_BG
        return f"QPushButton{{background-color:{bg_color_hex};color:{text_color_hex};border:none;border-radius:4px;padding:8px 12px;font-size:12px;font-weight:500;min-height:28px;}} QPushButton:hover{{background-color:{hover_bg};}} QPushButton:pressed{{background-color:{pressed_bg};}} QPushButton:disabled{{background-color:{DARK_HEADER_FOOTER};color:{DARK_TEXT_TERTIARY};}}"

    def get_generic_button_style(self):
        # Method kept for completeness, not used by simplified UI
        return f"QPushButton{{background-color:{DARK_BUTTON_BG};color:{DARK_TEXT_PRIMARY};border:1px solid {DARK_BORDER};border-radius:4px;padding:8px 12px;font-size:12px;font-weight:500;min-height:28px;}} QPushButton:hover{{background-color:{DARK_BUTTON_HOVER};}} QPushButton:disabled{{background-color:{DARK_HEADER_FOOTER};color:{DARK_TEXT_TERTIARY};}}"

    def _setup_ui(self):
        self.set_title("User Management & System Setup (Simplified UI Test)")
        self.resize(1000, 700)

        # Ensure central_widget has a distinct background to confirm visibility
        self.central_widget.setStyleSheet(f"background-color: {DARK_BACKGROUND};")

        # Create a main layout for the central_widget
        # This is the ONLY place self.central_widget should get its layout set.
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Add a very simple test label
        test_label = QLabel("Simplified User Management Screen - UI Test")
        test_label.setStyleSheet(
            f"color: #FFFFFF; font-size: 24px; qproperty-alignment: 'AlignCenter'; background-color: #555555; padding: 20px;"
        )
        test_label.setWordWrap(True)
        main_layout.addWidget(test_label)
        main_layout.addStretch()  # Pushes label to the top

        # --- Footer for Exit button ---
        # Even in simplified UI, we need a way to trigger the exit path.
        footer_frame = QFrame()
        footer_frame.setObjectName("FooterFrameAdminSimplified")
        footer_frame.setFixedHeight(60)
        footer_frame.setStyleSheet(
            f"#FooterFrameAdminSimplified{{background-color:{DARK_HEADER_FOOTER};border-top:1px solid {DARK_BORDER};padding:10px 15px;}}"
        )

        footer_layout = QHBoxLayout(footer_frame)
        self.exit_button_simplified = QPushButton("🚪 Exit This Test Screen")
        self.exit_button_simplified.setStyleSheet(
            self.get_generic_button_style()
        )  # Uses the existing method
        self.exit_button_simplified.clicked.connect(self._confirm_exit_simplified_ui)

        footer_layout.addStretch()
        footer_layout.addWidget(self.exit_button_simplified)
        main_layout.addWidget(footer_frame)  # Add footer to main layout

        self.logger.info(
            "UserManagementScreen _setup_ui CALLED (SIMPLIFIED FOR DIAGNOSIS)."
        )

        # --- Original complex UI setup is TEMPORARILY BYPASSED ---
        # self._setup_header(main_layout) # Original header
        # self.tab_widget = QTabWidget()
        # self.tab_widget.setStyleSheet(self._get_tab_widget_style())
        # self._setup_users_tab()
        # self._setup_locations_tab()
        # self._setup_charge_codes_tab()
        # main_layout.addWidget(self.tab_widget, 1)
        # self._setup_footer_buttons(main_layout) # Original footer

    def _confirm_exit_simplified_ui(self):
        self.logger.info("Exit button clicked on simplified UserManagementScreen.")
        self.exit_requested.emit()  # This should trigger main.py to go back to Horse screen

    # --- Stubbed or unmodified methods from the full version below ---
    # --- They are mostly not called by the simplified _setup_ui ---

    def _load_initial_data(self):
        self.logger.info(
            "UserManagementScreen: _load_initial_data called (data loading bypassed for simplified UI test)."
        )
        # self._load_users_data()
        # self._load_locations_data()
        # self._load_charge_codes_data()

    # The _get_tab_widget_style and _get_table_widget_style are not called by simplified UI
    # but kept for when UI is restored.
    def _get_tab_widget_style(self):
        return f"QTabWidget::pane{{border:1px solid {DARK_BORDER};background-color:{DARK_WIDGET_BACKGROUND};border-radius:0px;margin-top:-1px;}} QTabBar::tab{{padding:10px 20px;margin-right:1px;background-color:{DARK_BUTTON_BG};color:{DARK_TEXT_SECONDARY};border:1px solid {DARK_BORDER};border-bottom:none;border-top-left-radius:5px;border-top-right-radius:5px;font-size:13px;font-weight:500;}} QTabBar::tab:selected{{background-color:{DARK_WIDGET_BACKGROUND};color:{DARK_TEXT_PRIMARY};border-bottom-color:{DARK_WIDGET_BACKGROUND};}} QTabBar::tab:!selected:hover{{background-color:{DARK_BUTTON_HOVER};}}"

    def _get_table_widget_style(self):
        return f"QTableWidget{{background-color:{DARK_WIDGET_BACKGROUND};color:{DARK_TEXT_PRIMARY};border:1px solid {DARK_BORDER};gridline-color:{DARK_BORDER};alternate-background-color:{DARK_INPUT_FIELD_BACKGROUND};selection-background-color:{DARK_PRIMARY_ACTION}70;selection-color:{DARK_TEXT_PRIMARY};font-size:12px;}} QTableWidget::item{{padding:8px;border-bottom:1px solid {DARK_BORDER};}} QHeaderView::section{{background-color:{DARK_HEADER_FOOTER};color:{DARK_TEXT_PRIMARY};padding:8px;border:1px solid {DARK_BORDER};font-weight:bold;font-size:12px;}} QTableCornerButton::section{{background-color:{DARK_HEADER_FOOTER};border:1px solid {DARK_BORDER};}}"

    def _setup_header(self, parent_layout: QVBoxLayout):
        pass  # Stubbed

    def _setup_users_tab(self):
        pass  # Stubbed

    def _setup_locations_tab(self):
        pass  # Stubbed

    def _setup_charge_codes_tab(self):
        pass  # Stubbed

    def _configure_table_widget(self, table: QTableWidget):
        pass  # Stubbed

    def _setup_footer_buttons(self, parent_layout: QVBoxLayout):
        pass  # Stubbed

    def _load_users_data(self):
        self.logger.debug("Simplified: _load_users_data would run here.")

    def _load_locations_data(self):
        self.logger.debug("Simplified: _load_locations_data would run here.")

    def _load_charge_codes_data(self):
        self.logger.debug("Simplified: _load_charge_codes_data would run here.")

    def _add_user(self):
        self.logger.debug("Add User clicked (UI stubbed).")

    def _edit_user(self):
        self.logger.debug("Edit User clicked (UI stubbed).")

    def _update_user_action_buttons_state(self):
        pass

    def _add_location(self):
        self.logger.debug("Add Location clicked (UI stubbed).")

    def _edit_location(self):
        self.logger.debug("Edit Location clicked (UI stubbed).")

    def _update_location_action_buttons_state(self):
        pass

    def _add_charge_code(self):
        self.logger.debug("Add Charge Code clicked (UI stubbed).")

    def _edit_charge_code(self):
        self.logger.debug("Edit Charge Code clicked (UI stubbed).")

    def _update_charge_code_action_buttons_state(self):
        pass

    def get_selected_user_login_id(self) -> Optional[str]:
        return None

    def get_selected_location_object(self) -> Optional[LocationModel]:
        return None

    def get_selected_charge_code_object(self) -> Optional[ChargeCodeModel]:
        return None

    def _confirm_exit(
        self,
    ):  # Original exit method, now distinct from simplified UI's exit
        self.logger.info(
            "Original _confirm_exit called (should not happen with simplified UI footer)."
        )
        self.exit_requested.emit()
