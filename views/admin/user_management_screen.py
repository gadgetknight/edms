# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.6.4
Purpose: Admin screen for managing users, locations, veterinarians, charge codes,
         categories, owners, and the company profile.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v1.6.4 (2025-06-10):
    - Fixed `DetachedInstanceError` in `_edit_selected_category_process` by
      checking if a category is Level 1 before accessing its `.parent`
      attribute, which would be None and cause a lazy-load failure.
- v1.6.3 (2025-06-09):
    - Providing the single, complete, and unabridged file containing the full
      implementations for all seven tabs.
- v1.6.2 (2025-06-09):
    - Bug Fix: Removed redundant message helper methods.
- v1.6.1 (2025-06-09):
    - Bug Fix: Restored the full implementations for all original tab methods.
    - Feature: Correctly integrated the new "Manage Veterinarians" and "Company Profile" tabs.
"""

import logging
from typing import Optional, List, Dict, Any, Union

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QAbstractItemView,
    QLabel,
    QFrame,
    QMessageBox,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QComboBox,
    QDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QColor, QFont

from views.base_view import BaseView
from config.app_config import AppConfig

from controllers import (
    UserController,
    LocationController,
    ChargeCodeController,
    OwnerController,
    CompanyProfileController,
    VeterinarianController,
)

from models import (
    User,
    Location,
    ChargeCode,
    Owner as OwnerModel,
    ChargeCodeCategory,
    Veterinarian,
)

from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .dialogs.add_edit_owner_dialog import AddEditOwnerDialog
from .dialogs.add_edit_charge_code_category_dialog import (
    AddEditChargeCodeCategoryDialog,
)
from .dialogs.add_edit_veterinarian_dialog import AddEditVeterinarianDialog
from .dialogs.company_profile_dialog import CompanyProfileDialog
from ..horse.widgets.custom_question_dialog import CustomQuestionDialog


class UserManagementScreen(BaseView):
    back_to_main_menu = Signal()
    entity_updated = Signal(str)

    USER_TAB_INDEX = 0
    LOCATION_TAB_INDEX = 1
    VETERINARIAN_TAB_INDEX = 2
    CATEGORY_PROCESS_TAB_INDEX = 3
    CHARGE_CODE_TAB_INDEX = 4
    OWNER_TAB_INDEX = 5
    PROFILE_TAB_INDEX = 6

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"UserManagementScreen __init__ called for user: {current_user_id}"
        )

        self.current_user_id = current_user_id
        if not self.current_user_id:
            self.logger.error(
                "UserManagementScreen initialized without a current_user_id!"
            )

        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.veterinarian_controller = VeterinarianController()
        self.charge_code_controller = ChargeCodeController()
        self.owner_controller = OwnerController()
        self.company_profile_controller = CompanyProfileController()

        # Widget Attributes
        self.users_table: Optional[QTableWidget] = None
        self.add_user_btn: Optional[QPushButton] = None
        self.edit_user_btn: Optional[QPushButton] = None
        self.toggle_user_active_btn: Optional[QPushButton] = None
        self.delete_user_btn: Optional[QPushButton] = None
        self.user_status_filter_combo: Optional[QComboBox] = None

        self.locations_table: Optional[QTableWidget] = None
        self.add_location_btn: Optional[QPushButton] = None
        self.edit_location_btn: Optional[QPushButton] = None
        self.toggle_location_active_btn: Optional[QPushButton] = None
        self.delete_location_btn: Optional[QPushButton] = None
        self.location_status_filter_combo: Optional[QComboBox] = None

        self.vets_table: Optional[QTableWidget] = None
        self.add_vet_btn: Optional[QPushButton] = None
        self.edit_vet_btn: Optional[QPushButton] = None
        self.toggle_vet_active_btn: Optional[QPushButton] = None
        self.vet_status_filter_combo: Optional[QComboBox] = None

        self.categories_tree: Optional[QTreeWidget] = None
        self.add_category_btn: Optional[QPushButton] = None
        self.add_process_btn: Optional[QPushButton] = None
        self.edit_category_process_btn: Optional[QPushButton] = None
        self.toggle_category_process_active_btn: Optional[QPushButton] = None
        self.delete_category_process_btn: Optional[QPushButton] = None
        self.category_filter_combo: Optional[QComboBox] = None

        self.charge_codes_table: Optional[QTableWidget] = None
        self.add_charge_code_btn: Optional[QPushButton] = None
        self.edit_charge_code_btn: Optional[QPushButton] = None
        self.toggle_charge_code_active_btn: Optional[QPushButton] = None
        self.delete_charge_code_btn: Optional[QPushButton] = None
        self.charge_code_status_filter_combo: Optional[QComboBox] = None

        self.owners_table: Optional[QTableWidget] = None
        self.add_owner_btn: Optional[QPushButton] = None
        self.edit_owner_btn: Optional[QPushButton] = None
        self.toggle_owner_active_btn: Optional[QPushButton] = None
        self.delete_owner_btn: Optional[QPushButton] = None
        self.owner_status_filter_combo: Optional[QComboBox] = None

        self.edit_profile_btn: Optional[QPushButton] = None
        self.tab_widget: Optional[QTabWidget] = None

        self._active_filters: Dict[int, str] = {
            self.USER_TAB_INDEX: "active",
            self.LOCATION_TAB_INDEX: "active",
            self.VETERINARIAN_TAB_INDEX: "active",
            self.CATEGORY_PROCESS_TAB_INDEX: "active",
            self.CHARGE_CODE_TAB_INDEX: "active",
            self.OWNER_TAB_INDEX: "active",
        }

        super().__init__(parent)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self._refresh_current_tab_data)

        self.setWindowTitle("User and System Management")
        self.resize(1200, 800)
        self.logger.info("UserManagementScreen __init__ completed.")

    def setup_ui(self):
        self.logger.info("Setting up UserManagementScreen UI...")

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_widget_style())

        users_tab_widget = self._create_users_tab()
        locations_tab_widget = self._create_locations_tab()
        veterinarians_tab_widget = self._create_veterinarians_tab()
        categories_processes_tab_widget = self._create_categories_processes_tab()
        charge_codes_tab_widget = self._create_charge_codes_tab()
        owners_tab_widget = self._create_owners_tab()
        company_profile_tab_widget = self._create_company_profile_tab()

        self.tab_widget.addTab(users_tab_widget, "👤 Manage Users")
        self.tab_widget.addTab(locations_tab_widget, "📍 Manage Locations")
        self.tab_widget.addTab(veterinarians_tab_widget, "🧑‍⚕️ Manage Veterinarians")
        self.tab_widget.addTab(
            categories_processes_tab_widget, "🗂️ Manage Categories/Processes"
        )
        self.tab_widget.addTab(charge_codes_tab_widget, "💲 Manage Charge Codes")
        self.tab_widget.addTab(owners_tab_widget, "🤝 Manage Master Owners")
        self.tab_widget.addTab(company_profile_tab_widget, "🏢 Company Profile")

        main_layout.addWidget(self.tab_widget)

        self._setup_connections()
        if self.tab_widget:
            self.tab_widget.setCurrentIndex(0)
            self._refresh_current_tab_data()

        self.logger.info("UserManagementScreen UI setup complete.")

    def _get_tab_widget_style(self) -> str:
        return f"""
            QTabWidget::pane {{
                border: 1px solid {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                border-radius: 6px;
                margin-top: -1px; 
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 2px;
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_SECONDARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-bottom: none; 
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 120px; 
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border-color: {AppConfig.DARK_BORDER};
                border-bottom-color: {AppConfig.DARK_WIDGET_BACKGROUND}; 
            }}
            QTabBar::tab:!selected:hover {{
                background-color: {AppConfig.DARK_BUTTON_HOVER};
                color: {AppConfig.DARK_TEXT_PRIMARY};
            }}
            QTabWidget::tab-bar {{
                alignment: left;
                border: none; 
                background-color: transparent; 
                margin-bottom: 0px; 
            }}
        """

    def _create_standard_button_layout(self) -> QHBoxLayout:
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        return button_layout

    def _apply_standard_button_style(
        self, button: QPushButton, button_type: str = "standard"
    ):
        base_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 12px;
                font-weight: 500;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.DARK_BUTTON_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_TERTIARY};
            }}
        """
        if button_type == "add":
            button.setStyleSheet(
                base_style.replace(
                    AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
                )
                + "color: white;"
            )
        elif button_type == "edit":
            button.setStyleSheet(
                base_style.replace(
                    AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
                )
                + "color: white;"
            )
        elif button_type == "delete" or button_type == "toggle_inactive":
            button.setStyleSheet(
                base_style.replace(
                    AppConfig.DARK_BUTTON_BG, AppConfig.DARK_DANGER_ACTION
                )
                + "color: white;"
            )
        else:
            button.setStyleSheet(base_style)

    def get_form_input_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: transparent;
            }}
            QComboBox QAbstractItemView {{
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                selection-background-color: {AppConfig.DARK_HIGHLIGHT_BG};
                selection-color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
        """

    def _setup_connections(self):
        self.logger.debug("Setting up connections for UserManagementScreen.")
        if self.tab_widget:
            self.tab_widget.currentChanged.connect(self._on_tab_changed)

        if self.add_user_btn:
            self.add_user_btn.clicked.connect(self._add_user)
        if self.edit_user_btn:
            self.edit_user_btn.clicked.connect(self._edit_selected_user)
        if self.toggle_user_active_btn:
            self.toggle_user_active_btn.clicked.connect(
                self._toggle_selected_user_active_status
            )
        if self.delete_user_btn:
            self.delete_user_btn.clicked.connect(self._delete_selected_user)
        if self.users_table:
            self.users_table.itemSelectionChanged.connect(
                self._update_user_action_buttons_state
            )
        if self.user_status_filter_combo:
            self.user_status_filter_combo.currentIndexChanged.connect(
                self._on_user_filter_changed
            )

        if self.add_location_btn:
            self.add_location_btn.clicked.connect(self._add_location)
        if self.edit_location_btn:
            self.edit_location_btn.clicked.connect(self._edit_selected_location)
        if self.toggle_location_active_btn:
            self.toggle_location_active_btn.clicked.connect(
                self._toggle_selected_location_active_status
            )
        if self.delete_location_btn:
            self.delete_location_btn.clicked.connect(self._delete_selected_location)
        if self.locations_table:
            self.locations_table.itemSelectionChanged.connect(
                self._update_location_action_buttons_state
            )
        if self.location_status_filter_combo:
            self.location_status_filter_combo.currentIndexChanged.connect(
                self._on_location_filter_changed
            )

        if self.add_vet_btn:
            self.add_vet_btn.clicked.connect(self._add_veterinarian)
        if self.edit_vet_btn:
            self.edit_vet_btn.clicked.connect(self._edit_selected_veterinarian)
        if self.toggle_vet_active_btn:
            self.toggle_vet_active_btn.clicked.connect(
                self._toggle_selected_veterinarian_status
            )
        if self.vets_table:
            self.vets_table.itemSelectionChanged.connect(
                self._update_veterinarian_action_buttons_state
            )
        if self.vet_status_filter_combo:
            self.vet_status_filter_combo.currentIndexChanged.connect(
                self._on_vet_filter_changed
            )

        if self.add_category_btn:
            self.add_category_btn.clicked.connect(self._add_category_or_process)
        if self.add_process_btn:
            self.add_process_btn.clicked.connect(
                lambda: self._add_category_or_process(is_process=True)
            )
        if self.edit_category_process_btn:
            self.edit_category_process_btn.clicked.connect(
                self._edit_selected_category_process
            )
        if self.toggle_category_process_active_btn:
            self.toggle_category_process_active_btn.clicked.connect(
                self._toggle_selected_category_process_active_status
            )
        if self.delete_category_process_btn:
            self.delete_category_process_btn.clicked.connect(
                self._delete_selected_category_process
            )
        if self.categories_tree:
            self.categories_tree.itemSelectionChanged.connect(
                self._update_category_action_buttons_state
            )
        if self.category_filter_combo:
            self.category_filter_combo.currentIndexChanged.connect(
                self._on_category_filter_changed
            )

        if self.add_charge_code_btn:
            self.add_charge_code_btn.clicked.connect(self._add_charge_code)
        if self.edit_charge_code_btn:
            self.edit_charge_code_btn.clicked.connect(self._edit_selected_charge_code)
        if self.toggle_charge_code_active_btn:
            self.toggle_charge_code_active_btn.clicked.connect(
                self._toggle_selected_charge_code_active_status
            )
        if self.delete_charge_code_btn:
            self.delete_charge_code_btn.clicked.connect(
                self._delete_selected_charge_code
            )
        if self.charge_codes_table:
            self.charge_codes_table.itemSelectionChanged.connect(
                self._update_charge_code_action_buttons_state
            )
        if self.charge_code_status_filter_combo:
            self.charge_code_status_filter_combo.currentIndexChanged.connect(
                self._on_charge_code_filter_changed
            )

        if self.add_owner_btn:
            self.add_owner_btn.clicked.connect(self._add_owner)
        if self.edit_owner_btn:
            self.edit_owner_btn.clicked.connect(self._edit_selected_owner)
        if self.toggle_owner_active_btn:
            self.toggle_owner_active_btn.clicked.connect(
                self._toggle_selected_owner_active_status
            )
        if self.delete_owner_btn:
            self.delete_owner_btn.clicked.connect(self._delete_selected_owner)
        if self.owners_table:
            self.owners_table.itemSelectionChanged.connect(
                self._update_owner_action_buttons_state
            )
        if self.owner_status_filter_combo:
            self.owner_status_filter_combo.currentIndexChanged.connect(
                self._on_owner_filter_changed
            )

        if self.edit_profile_btn:
            self.edit_profile_btn.clicked.connect(self._launch_company_profile_dialog)
        self.logger.debug("Connections setup complete.")

    def _on_tab_changed(self, index: int):
        self.logger.info(
            f"Tab changed to index: {index}, new tab title: {self.tab_widget.tabText(index) if self.tab_widget else 'N/A'}"
        )
        self._refresh_current_tab_data()

    def _refresh_current_tab_data(self, force_reload: bool = False):
        if not self.tab_widget:
            self.logger.warning("Tab widget not available for refresh.")
            return
        current_index = self.tab_widget.currentIndex()
        self.logger.debug(f"Refreshing data for tab index: {current_index}")

        if current_index == self.USER_TAB_INDEX:
            self.load_users_data()
        elif current_index == self.LOCATION_TAB_INDEX:
            self.load_locations_data()
        elif current_index == self.VETERINARIAN_TAB_INDEX:
            self.load_veterinarians_data()
        elif current_index == self.CATEGORY_PROCESS_TAB_INDEX:
            self.load_categories_processes_data()
        elif current_index == self.CHARGE_CODE_TAB_INDEX:
            self.load_charge_codes_data()
        elif current_index == self.OWNER_TAB_INDEX:
            self.load_owners_data()
        elif current_index == self.PROFILE_TAB_INDEX:
            pass
        else:
            self.logger.warning(
                f"No data loading action defined for tab index {current_index}"
            )

    def _create_table_widget(self, headers: List[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setStyleSheet(
            f"""
            QTableWidget {{
                gridline-color: {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                color: {AppConfig.DARK_TEXT_SECONDARY};
                padding: 5px;
                border: none; 
                border-bottom: 1px solid {AppConfig.DARK_BORDER};
                font-weight: 500;
            }}
            QTableWidget::item {{ padding: 5px; }}
            QTableWidget::item:selected {{ background-color: {AppConfig.DARK_HIGHLIGHT_BG}; color: {AppConfig.DARK_HIGHLIGHT_TEXT}; }}
            """
        )
        table.horizontalHeader().setStretchLastSection(True)
        for i in range(len(headers) - 1):
            table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        return table

    # --- Users Tab Methods ---
    def _create_users_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        button_layout = self._create_standard_button_layout()
        self.add_user_btn = QPushButton("➕ Add New User")
        self._apply_standard_button_style(self.add_user_btn, "add")
        self.edit_user_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_user_btn, "edit")
        self.toggle_user_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_user_active_btn)
        self.delete_user_btn = QPushButton("🗑️ Delete Selected")
        self._apply_standard_button_style(self.delete_user_btn, "delete")
        button_layout.addWidget(self.add_user_btn)
        button_layout.addWidget(self.edit_user_btn)
        button_layout.addWidget(self.toggle_user_active_btn)
        button_layout.addWidget(self.delete_user_btn)
        top_bar_layout.addLayout(button_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.user_status_filter_combo = QComboBox()
        self.user_status_filter_combo.addItems(["Active", "Inactive", "All"])
        self.user_status_filter_combo.setCurrentText(
            self._active_filters.get(self.USER_TAB_INDEX, "active")
        )
        self.user_status_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.user_status_filter_combo)
        layout.addLayout(top_bar_layout)
        self.users_table = self._create_table_widget(
            ["Login ID", "Full Name", "Email", "Roles", "Active", "Last Login"]
        )
        layout.addWidget(self.users_table)
        self._update_user_action_buttons_state()
        return tab

    def load_users_data(self):
        self.logger.info("Loading users data for tab...")
        if not self.users_table or not self.user_status_filter_combo:
            self.logger.error("Users table or filter combo not initialized.")
            return
        try:
            status_filter = self.user_status_filter_combo.currentText().lower()
            self._active_filters[self.USER_TAB_INDEX] = status_filter
            users = self.user_controller.get_all_users(status_filter=status_filter)
            self.users_table.setRowCount(0)
            for user_obj in users:
                row_position = self.users_table.rowCount()
                self.users_table.insertRow(row_position)
                self.users_table.setItem(
                    row_position, 0, QTableWidgetItem(user_obj.user_id)
                )
                self.users_table.setItem(
                    row_position, 1, QTableWidgetItem(user_obj.user_name or "")
                )
                self.users_table.setItem(
                    row_position, 2, QTableWidgetItem(user_obj.email or "")
                )
                roles_str = ", ".join([role.name for role in user_obj.roles])
                self.users_table.setItem(row_position, 3, QTableWidgetItem(roles_str))
                active_str = "Yes" if user_obj.is_active else "No"
                self.users_table.setItem(row_position, 4, QTableWidgetItem(active_str))
                last_login_str = (
                    user_obj.last_login.strftime("%Y-%m-%d %H:%M")
                    if user_obj.last_login
                    else "Never"
                )
                self.users_table.setItem(
                    row_position, 5, QTableWidgetItem(last_login_str)
                )
                self.users_table.item(row_position, 0).setData(
                    Qt.ItemDataRole.UserRole, user_obj.user_id
                )
            self.logger.info(f"Loaded {len(users)} users.")
        except Exception as e:
            self.logger.error(f"Error loading users: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load users: {e}")
        self._update_user_action_buttons_state()

    def _on_user_filter_changed(self, index: int):
        self.load_users_data()

    def _add_user(self):
        dialog = AddEditUserDialog(
            self,
            user_controller=self.user_controller,
            current_user_object=None,
            current_user_id=self.current_user_id,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users_data()
            self.entity_updated.emit("user")

    def _edit_selected_user(self):
        if not self.users_table or not self.users_table.currentItem():
            self.show_info("Edit User", "Please select a user to edit.")
            return
        selected_row = self.users_table.currentRow()
        user_id_item = self.users_table.item(selected_row, 0)
        if not user_id_item:
            self.show_error("Error", "Could not retrieve user ID for selected row.")
            return
        user_login_id = (
            user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
        )
        user_to_edit = self.user_controller.get_user_by_login_id(user_login_id)
        if user_to_edit:
            dialog = AddEditUserDialog(
                self,
                user_controller=self.user_controller,
                current_user_object=user_to_edit,
                current_user_id=self.current_user_id,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_users_data()
                self.entity_updated.emit("user")
        else:
            self.show_error("Error", f"User with Login ID '{user_login_id}' not found.")
            self.load_users_data()

    def _toggle_selected_user_active_status(self):
        if not self.users_table or not self.users_table.currentItem():
            self.show_info("Toggle Active Status", "Please select a user.")
            return
        selected_row = self.users_table.currentRow()
        user_id_item = self.users_table.item(selected_row, 0)
        user_login_id = (
            user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
        )
        user_obj = self.user_controller.get_user_by_login_id(user_login_id)
        if not user_obj:
            self.show_error("Error", f"User {user_login_id} not found.")
            return
        action = "deactivate" if user_obj.is_active else "activate"
        name_display = user_obj.user_name or user_obj.user_id
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} user '{name_display}'?",
        ):
            success, message = self.user_controller.toggle_user_active_status(
                user_login_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_users_data()
                self.entity_updated.emit("user")
            else:
                self.show_error("Error", message)

    def _delete_selected_user(self):
        if not self.users_table or not self.users_table.currentItem():
            self.show_info("Delete User", "Please select a user to delete.")
            return
        selected_row = self.users_table.currentRow()
        user_id_item = self.users_table.item(selected_row, 0)
        user_login_id = (
            user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
        )
        user_name_item = self.users_table.item(selected_row, 1)
        display_name = user_name_item.text() if user_name_item else user_login_id
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to permanently delete user '{display_name}'?\nThis action cannot be undone.",
        ):
            success, message = self.user_controller.delete_user_permanently(
                user_login_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_users_data()
                self.entity_updated.emit("user_deleted")
            else:
                self.show_error("Delete Failed", message)

    def _update_user_action_buttons_state(self):
        has_selection = (
            self.users_table is not None and self.users_table.currentItem() is not None
        )
        if self.edit_user_btn:
            self.edit_user_btn.setEnabled(has_selection)
        if self.toggle_user_active_btn:
            self.toggle_user_active_btn.setEnabled(has_selection)
        if self.delete_user_btn:
            self.delete_user_btn.setEnabled(has_selection)
        if has_selection and self.toggle_user_active_btn and self.users_table:
            selected_row = self.users_table.currentRow()
            user_id_item = self.users_table.item(selected_row, 0)
            if not user_id_item:
                return
            user_login_id = (
                user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
            )
            user_obj = self.user_controller.get_user_by_login_id(user_login_id)
            if user_obj:
                action_text = "Deactivate" if user_obj.is_active else "Activate"
                self.toggle_user_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_user_active_btn,
                    "toggle_inactive" if user_obj.is_active else "standard",
                )

    # --- Locations Tab Methods ---
    def _create_locations_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        button_layout = self._create_standard_button_layout()
        self.add_location_btn = QPushButton("➕ Add New Location")
        self._apply_standard_button_style(self.add_location_btn, "add")
        self.edit_location_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_location_btn, "edit")
        self.toggle_location_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_location_active_btn)
        self.delete_location_btn = QPushButton("🗑️ Delete Selected")
        self._apply_standard_button_style(self.delete_location_btn, "delete")
        button_layout.addWidget(self.add_location_btn)
        button_layout.addWidget(self.edit_location_btn)
        button_layout.addWidget(self.toggle_location_active_btn)
        button_layout.addWidget(self.delete_location_btn)
        top_bar_layout.addLayout(button_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.location_status_filter_combo = QComboBox()
        self.location_status_filter_combo.addItems(["Active", "Inactive", "All"])
        self.location_status_filter_combo.setCurrentText(
            self._active_filters.get(self.LOCATION_TAB_INDEX, "active")
        )
        self.location_status_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.location_status_filter_combo)
        layout.addLayout(top_bar_layout)
        self.locations_table = self._create_table_widget(
            ["Name", "Address", "City", "State", "Zip", "Contact", "Active"]
        )
        layout.addWidget(self.locations_table)
        self._update_location_action_buttons_state()
        return tab

    def load_locations_data(self):
        self.logger.info("Loading locations data for tab...")
        if not self.locations_table or not self.location_status_filter_combo:
            self.logger.error("Locations table or filter combo not initialized.")
            return
        try:
            status_filter = self.location_status_filter_combo.currentText().lower()
            self._active_filters[self.LOCATION_TAB_INDEX] = status_filter
            locations = self.location_controller.get_all_locations(
                status_filter=status_filter
            )
            self.locations_table.setRowCount(0)
            for loc_obj in locations:
                row_position = self.locations_table.rowCount()
                self.locations_table.insertRow(row_position)
                self.locations_table.setItem(
                    row_position, 0, QTableWidgetItem(loc_obj.location_name)
                )
                address_parts = [loc_obj.address_line1, loc_obj.address_line2]
                self.locations_table.setItem(
                    row_position,
                    1,
                    QTableWidgetItem(" ".join(filter(None, address_parts))),
                )
                self.locations_table.setItem(
                    row_position, 2, QTableWidgetItem(loc_obj.city or "")
                )
                state_display = loc_obj.state_code or ""
                if (
                    hasattr(loc_obj, "state")
                    and loc_obj.state
                    and hasattr(loc_obj.state, "state_code")
                ):
                    state_display = loc_obj.state.state_code
                self.locations_table.setItem(
                    row_position, 3, QTableWidgetItem(state_display)
                )
                self.locations_table.setItem(
                    row_position, 4, QTableWidgetItem(loc_obj.zip_code or "")
                )
                self.locations_table.setItem(
                    row_position, 5, QTableWidgetItem(loc_obj.contact_person or "")
                )
                self.locations_table.setItem(
                    row_position,
                    6,
                    QTableWidgetItem("Yes" if loc_obj.is_active else "No"),
                )
                self.locations_table.item(row_position, 0).setData(
                    Qt.ItemDataRole.UserRole, loc_obj.location_id
                )
            self.logger.info(f"Loaded {len(locations)} locations.")
        except Exception as e:
            self.logger.error(f"Error loading locations: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load locations: {e}")
        self._update_location_action_buttons_state()

    def _on_location_filter_changed(self, index: int):
        self.load_locations_data()

    def _add_location(self):
        dialog = AddEditLocationDialog(
            self,
            controller=self.location_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations_data()
            self.entity_updated.emit("location")

    def _edit_selected_location(self):
        if not self.locations_table or not self.locations_table.currentItem():
            self.show_info("Edit Location", "Please select a location to edit.")
            return
        selected_row = self.locations_table.currentRow()
        location_id_item = self.locations_table.item(selected_row, 0)
        location_id = (
            location_id_item.data(Qt.ItemDataRole.UserRole) or location_id_item.text()
        )
        location_to_edit = self.location_controller.get_location_by_id(location_id)
        if location_to_edit:
            dialog = AddEditLocationDialog(
                self,
                controller=self.location_controller,
                location=location_to_edit,
                current_user_id=self.current_user_id,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_locations_data()
                self.entity_updated.emit("location")
        else:
            self.show_error("Error", f"Location with ID '{location_id}' not found.")
            self.load_locations_data()

    def _toggle_selected_location_active_status(self):
        if not self.locations_table or not self.locations_table.currentItem():
            self.show_info("Toggle Active Status", "Please select a location.")
            return
        selected_row = self.locations_table.currentRow()
        location_id_item = self.locations_table.item(selected_row, 0)
        location_id = (
            location_id_item.data(Qt.ItemDataRole.UserRole) or location_id_item.text()
        )
        loc_obj = self.location_controller.get_location_by_id(location_id)
        if not loc_obj:
            self.show_error("Error", f"Location {location_id} not found.")
            return
        action = "deactivate" if loc_obj.is_active else "activate"
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} location '{loc_obj.location_name}'?",
        ):
            success, message = self.location_controller.toggle_location_active_status(
                location_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_locations_data()
                self.entity_updated.emit("location")
            else:
                self.show_error("Error", message)

    def _delete_selected_location(self):
        if not self.locations_table or not self.locations_table.currentItem():
            self.show_info("Delete Location", "Please select a location to delete.")
            return
        selected_row = self.locations_table.currentRow()
        location_id_item = self.locations_table.item(selected_row, 0)
        location_id = (
            location_id_item.data(Qt.ItemDataRole.UserRole) or location_id_item.text()
        )
        location_name = location_id_item.text()
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to permanently delete location '{location_name}'?\nThis action cannot be undone.",
        ):
            success, message = self.location_controller.delete_location(
                location_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_locations_data()
                self.entity_updated.emit("location_deleted")
            else:
                self.show_error("Delete Failed", message)

    def _update_location_action_buttons_state(self):
        has_selection = (
            self.locations_table is not None
            and self.locations_table.currentItem() is not None
        )
        if self.edit_location_btn:
            self.edit_location_btn.setEnabled(has_selection)
        if self.toggle_location_active_btn:
            self.toggle_location_active_btn.setEnabled(has_selection)
        if self.delete_location_btn:
            self.delete_location_btn.setEnabled(has_selection)
        if has_selection and self.toggle_location_active_btn and self.locations_table:
            selected_row = self.locations_table.currentRow()
            location_id_item = self.locations_table.item(selected_row, 0)
            if not location_id_item:
                return
            loc_id = (
                location_id_item.data(Qt.ItemDataRole.UserRole)
                or location_id_item.text()
            )
            loc_obj = self.location_controller.get_location_by_id(loc_id)
            if loc_obj:
                action_text = "Deactivate" if loc_obj.is_active else "Activate"
                self.toggle_location_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_location_active_btn,
                    "toggle_inactive" if loc_obj.is_active else "standard",
                )

    # --- Veterinarians Tab Methods ---
    def _create_veterinarians_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        button_layout = self._create_standard_button_layout()
        self.add_vet_btn = QPushButton("➕ Add New Veterinarian")
        self._apply_standard_button_style(self.add_vet_btn, "add")
        self.edit_vet_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_vet_btn, "edit")
        self.toggle_vet_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_vet_active_btn)
        button_layout.addWidget(self.add_vet_btn)
        button_layout.addWidget(self.edit_vet_btn)
        button_layout.addWidget(self.toggle_vet_active_btn)
        top_bar_layout.addLayout(button_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.vet_status_filter_combo = QComboBox()
        self.vet_status_filter_combo.addItems(["Active", "Inactive", "All"])
        self.vet_status_filter_combo.setCurrentText(
            self._active_filters.get(self.VETERINARIAN_TAB_INDEX, "active")
        )
        self.vet_status_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.vet_status_filter_combo)
        main_layout.addLayout(top_bar_layout)
        self.vets_table = self._create_table_widget(
            ["Name", "License #", "Specialty", "Phone", "Email", "Status"]
        )
        main_layout.addWidget(self.vets_table)
        self._update_veterinarian_action_buttons_state()
        return tab_widget

    def load_veterinarians_data(self):
        self.logger.info("Loading veterinarians data for tab...")
        if not self.vets_table or not self.vet_status_filter_combo:
            self.logger.error("Veterinarians table or filter combo not initialized.")
            return
        try:
            status_filter = self.vet_status_filter_combo.currentText().lower()
            self._active_filters[self.VETERINARIAN_TAB_INDEX] = status_filter
            vets = self.veterinarian_controller.get_all_veterinarians(
                status_filter=status_filter
            )
            self.vets_table.setRowCount(0)
            for vet in vets:
                row_position = self.vets_table.rowCount()
                self.vets_table.insertRow(row_position)
                name_item = QTableWidgetItem(f"{vet.first_name} {vet.last_name}")
                name_item.setData(Qt.ItemDataRole.UserRole, vet.vet_id)
                status_item = QTableWidgetItem(
                    "Active" if vet.is_active else "Inactive"
                )
                status_item.setForeground(
                    QColor("#68D391") if vet.is_active else QColor("#FC8181")
                )
                self.vets_table.setItem(row_position, 0, name_item)
                self.vets_table.setItem(
                    row_position, 1, QTableWidgetItem(vet.license_number or "")
                )
                self.vets_table.setItem(
                    row_position, 2, QTableWidgetItem(vet.specialty or "")
                )
                self.vets_table.setItem(
                    row_position, 3, QTableWidgetItem(vet.phone or "")
                )
                self.vets_table.setItem(
                    row_position, 4, QTableWidgetItem(vet.email or "")
                )
                self.vets_table.setItem(row_position, 5, status_item)
            self.logger.info(f"Loaded {len(vets)} veterinarians.")
        except Exception as e:
            self.logger.error(f"Error loading veterinarians: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load veterinarians: {e}")
        self._update_veterinarian_action_buttons_state()

    def _on_vet_filter_changed(self, index: int):
        self.load_veterinarians_data()

    def _add_veterinarian(self):
        dialog = AddEditVeterinarianDialog(
            parent_view=self,
            controller=self.veterinarian_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_veterinarians_data()
            self.entity_updated.emit("veterinarian")
            self.show_info("Success", "Veterinarian added successfully.")

    def _edit_selected_veterinarian(self):
        selected_rows = self.vets_table.selectionModel().selectedRows()
        if not selected_rows:
            self.show_info("Edit Veterinarian", "Please select a veterinarian to edit.")
            return
        vet_id = selected_rows[0].data(Qt.ItemDataRole.UserRole)
        vet_to_edit = self.veterinarian_controller.get_veterinarian_by_id(vet_id)
        if not vet_to_edit:
            self.show_error("Error", "Could not retrieve veterinarian details.")
            return
        dialog = AddEditVeterinarianDialog(
            parent_view=self,
            controller=self.veterinarian_controller,
            current_user_id=self.current_user_id,
            veterinarian=vet_to_edit,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_veterinarians_data()
            self.entity_updated.emit("veterinarian")
            self.show_info("Success", "Veterinarian updated successfully.")

    def _toggle_selected_veterinarian_status(self):
        selected_rows = self.vets_table.selectionModel().selectedRows()
        if not selected_rows:
            self.show_info("Toggle Status", "Please select a veterinarian.")
            return
        vet_id = selected_rows[0].data(Qt.ItemDataRole.UserRole)
        vet_name = self.vets_table.item(selected_rows[0].row(), 0).text()
        current_status_text = self.vets_table.item(selected_rows[0].row(), 5).text()
        action_text = "deactivate" if current_status_text == "Active" else "activate"
        if self.show_question(
            "Confirm Status Change",
            f"Are you sure you want to {action_text} {vet_name}?",
        ):
            success, message = self.veterinarian_controller.toggle_veterinarian_status(
                vet_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_veterinarians_data()
            else:
                self.show_error("Error", message)

    def _update_veterinarian_action_buttons_state(self):
        has_selection = bool(
            self.vets_table is not None
            and self.vets_table.selectionModel().hasSelection()
        )
        if self.edit_vet_btn:
            self.edit_vet_btn.setEnabled(has_selection)
        if self.toggle_vet_active_btn:
            self.toggle_vet_active_btn.setEnabled(has_selection)
        if has_selection:
            selected_row = self.vets_table.currentRow()
            status_text = self.vets_table.item(selected_row, 5).text()
            action_text = "Deactivate" if status_text == "Active" else "Activate"
            self.toggle_vet_active_btn.setText(f"🔄 {action_text} Selected")
            self._apply_standard_button_style(
                self.toggle_vet_active_btn,
                "toggle_inactive" if status_text == "Active" else "standard",
            )

    # --- Categories/Processes Tab Methods ---
    def _create_categories_processes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("➕ Add Category (L1)")
        self._apply_standard_button_style(self.add_category_btn, "add")
        self.add_process_btn = QPushButton("➕ Add Process (L2)")
        self._apply_standard_button_style(self.add_process_btn, "add")
        self.edit_category_process_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_category_process_btn, "edit")
        self.toggle_category_process_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_category_process_active_btn)
        self.delete_category_process_btn = QPushButton("🗑️ Delete Selected")
        self._apply_standard_button_style(self.delete_category_process_btn, "delete")
        top_bar_layout.addWidget(self.add_category_btn)
        top_bar_layout.addWidget(self.add_process_btn)
        top_bar_layout.addWidget(self.edit_category_process_btn)
        top_bar_layout.addWidget(self.toggle_category_process_active_btn)
        top_bar_layout.addWidget(self.delete_category_process_btn)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItems(["Active", "Inactive", "All"])
        self.category_filter_combo.setCurrentText(
            self._active_filters.get(self.CATEGORY_PROCESS_TAB_INDEX, "active")
        )
        self.category_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.category_filter_combo)
        layout.addLayout(top_bar_layout)
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderLabels(
            ["Category/Process Name", "Level", "Status", "ID"]
        )
        self.categories_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.categories_tree.setStyleSheet(
            f"""QTreeWidget {{ background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; }} QHeaderView::section {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_SECONDARY}; padding: 5px; border: none; border-bottom: 1px solid {AppConfig.DARK_BORDER}; font-weight: 500; }} QTreeWidget::item:selected {{ background-color: {AppConfig.DARK_HIGHLIGHT_BG}; color: {AppConfig.DARK_HIGHLIGHT_TEXT}; }} QTreeWidget::item {{ padding: 3px; }}"""
        )
        header = self.categories_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.categories_tree)
        self._update_category_action_buttons_state()
        return tab

    def load_categories_processes_data(self):
        self.logger.info("Loading charge code categories/processes data...")
        if not self.categories_tree or not self.category_filter_combo:
            self.logger.error("Categories tree or filter combo not initialized.")
            return
        self.categories_tree.clear()
        try:
            level1_categories = (
                self.charge_code_controller.get_all_charge_code_categories_hierarchical()
            )
            ui_status_filter = self.category_filter_combo.currentText().lower()
            self._active_filters[self.CATEGORY_PROCESS_TAB_INDEX] = ui_status_filter
            for cat_l1 in level1_categories:
                has_visible_children = False
                child_items = []
                for cat_l2 in cat_l1.children:
                    if (
                        ui_status_filter == "all"
                        or (ui_status_filter == "active" and cat_l2.is_active)
                        or (ui_status_filter == "inactive" and not cat_l2.is_active)
                    ):
                        l2_item = QTreeWidgetItem()
                        l2_item.setText(0, cat_l2.name)
                        l2_item.setText(1, str(cat_l2.level))
                        l2_item.setText(2, "Active" if cat_l2.is_active else "Inactive")
                        l2_item.setText(3, str(cat_l2.category_id))
                        l2_item.setData(
                            0,
                            Qt.ItemDataRole.UserRole,
                            {"id": cat_l2.category_id, "level": 2, "obj": cat_l2},
                        )
                        child_items.append(l2_item)
                        has_visible_children = True
                is_l1_visible = (
                    ui_status_filter == "all"
                    or (ui_status_filter == "active" and cat_l1.is_active)
                    or (ui_status_filter == "inactive" and not cat_l1.is_active)
                )
                if is_l1_visible or has_visible_children:
                    l1_item = QTreeWidgetItem(self.categories_tree)
                    l1_item.setText(0, cat_l1.name)
                    l1_item.setText(1, str(cat_l1.level))
                    l1_item.setText(2, "Active" if cat_l1.is_active else "Inactive")
                    l1_item.setText(3, str(cat_l1.category_id))
                    l1_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        {"id": cat_l1.category_id, "level": 1, "obj": cat_l1},
                    )
                    l1_item.addChildren(child_items)
            self.categories_tree.expandAll()
            self.logger.info(
                f"Displayed categories in tree (UI filter: '{ui_status_filter}')."
            )
        except Exception as e:
            self.logger.error(f"Error loading categories/processes: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load categories: {e}")
        self._update_category_action_buttons_state()

    def _on_category_filter_changed(self, index: int):
        self.load_categories_processes_data()

    def _add_category_or_process(self, is_process: bool = False):
        selected_item = (
            self.categories_tree.currentItem() if self.categories_tree else None
        )
        parent_category: Optional[ChargeCodeCategory] = None
        if is_process:
            if not selected_item:
                self.show_warning(
                    "Add Process",
                    "Please select a Level 1 Category to add a Process under.",
                )
                return
            item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if item_data.get("level") != 1:
                self.show_warning(
                    "Add Process",
                    "Processes (Level 2) can only be added under a Level 1 Category.",
                )
                return
            parent_category = item_data.get("obj")
        dialog = AddEditChargeCodeCategoryDialog(
            self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            category_to_edit=None,
            parent_category=parent_category,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_categories_processes_data()
            self.entity_updated.emit("charge_code_category")

    def _edit_selected_category_process(self):
        if not self.categories_tree or not self.categories_tree.currentItem():
            self.show_info("Edit Item", "Please select a category or process to edit.")
            return
        selected_item = self.categories_tree.currentItem()
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        category_to_edit: Optional[ChargeCodeCategory] = item_data.get("obj")
        if not category_to_edit:
            self.show_error("Error", "Could not retrieve item details to edit.")
            self.load_categories_processes_data()
            return

        # MODIFIED: Logic to safely get parent category
        parent_for_dialog = None
        if category_to_edit.level == 2:
            # The .parent attribute is now eager-loaded by the controller query
            parent_for_dialog = category_to_edit.parent

        dialog = AddEditChargeCodeCategoryDialog(
            self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            category_to_edit=category_to_edit,
            parent_category=parent_for_dialog,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_categories_processes_data()
            self.entity_updated.emit("charge_code_category")

    def _toggle_selected_category_process_active_status(self):
        if not self.categories_tree or not self.categories_tree.currentItem():
            self.show_info("Toggle Status", "Please select an item.")
            return
        selected_item = self.categories_tree.currentItem()
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        item_id = item_data.get("id")
        item_obj: Optional[ChargeCodeCategory] = item_data.get("obj")
        if not item_obj:
            self.show_error("Error", f"Item with ID {item_id} not found.")
            return
        action = "deactivate" if item_obj.is_active else "activate"
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} '{item_obj.name}'?",
        ):
            success, message = (
                self.charge_code_controller.toggle_charge_code_category_status(
                    item_id, self.current_user_id
                )
            )
            if success:
                self.show_info("Success", message)
                self.load_categories_processes_data()
            else:
                self.show_error("Error", message)

    def _delete_selected_category_process(self):
        if not self.categories_tree or not self.categories_tree.currentItem():
            self.show_info("Delete Item", "Please select an item to delete.")
            return
        selected_item = self.categories_tree.currentItem()
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        item_id = item_data.get("id")
        item_name = selected_item.text(0)
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{item_name}'?\nThis may fail if it is in use.\nThis action cannot be undone.",
        ):
            success, message = self.charge_code_controller.delete_charge_code_category(
                item_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_categories_processes_data()
            else:
                self.show_error("Delete Failed", message)

    def _update_category_action_buttons_state(self):
        if not self.categories_tree:
            return
        has_selection = self.categories_tree.currentItem() is not None
        is_l1_selected = False
        item_obj: Optional[ChargeCodeCategory] = None
        if has_selection:
            item_data = self.categories_tree.currentItem().data(
                0, Qt.ItemDataRole.UserRole
            )
            if item_data:
                is_l1_selected = item_data.get("level") == 1
                item_obj = item_data.get("obj")
        if self.add_category_btn:
            self.add_category_btn.setEnabled(True)
        if self.add_process_btn:
            self.add_process_btn.setEnabled(is_l1_selected)
        if self.edit_category_process_btn:
            self.edit_category_process_btn.setEnabled(has_selection)
        if self.toggle_category_process_active_btn:
            self.toggle_category_process_active_btn.setEnabled(has_selection)
        if self.delete_category_process_btn:
            self.delete_category_process_btn.setEnabled(has_selection)
        if has_selection and self.toggle_category_process_active_btn and item_obj:
            action_text = "Deactivate" if item_obj.is_active else "Activate"
            self.toggle_category_process_active_btn.setText(
                f"🔄 {action_text} Selected"
            )
            self._apply_standard_button_style(
                self.toggle_category_process_active_btn,
                "toggle_inactive" if item_obj.is_active else "standard",
            )

    # --- Charge Codes Tab Methods ---
    def _create_charge_codes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        button_layout = self._create_standard_button_layout()
        self.add_charge_code_btn = QPushButton("➕ Add New Charge Code")
        self._apply_standard_button_style(self.add_charge_code_btn, "add")
        self.edit_charge_code_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_charge_code_btn, "edit")
        self.toggle_charge_code_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_charge_code_active_btn)
        self.delete_charge_code_btn = QPushButton("🗑️ Delete Selected")
        self._apply_standard_button_style(self.delete_charge_code_btn, "delete")
        button_layout.addWidget(self.add_charge_code_btn)
        button_layout.addWidget(self.edit_charge_code_btn)
        button_layout.addWidget(self.toggle_charge_code_active_btn)
        button_layout.addWidget(self.delete_charge_code_btn)
        top_bar_layout.addLayout(button_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.charge_code_status_filter_combo = QComboBox()
        self.charge_code_status_filter_combo.addItems(["Active", "Inactive", "All"])
        self.charge_code_status_filter_combo.setCurrentText(
            self._active_filters.get(self.CHARGE_CODE_TAB_INDEX, "active")
        )
        self.charge_code_status_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.charge_code_status_filter_combo)
        layout.addLayout(top_bar_layout)
        self.charge_codes_table = self._create_table_widget(
            [
                "Code",
                "Alternate Code",
                "Category",
                "Description",
                "Std. Price",
                "Active",
            ]
        )
        if self.charge_codes_table:
            self.charge_codes_table.horizontalHeader().setSectionResizeMode(
                3, QHeaderView.ResizeMode.Stretch
            )
        for i in [0, 1, 2, 4, 5]:
            self.charge_codes_table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        layout.addWidget(self.charge_codes_table)
        self._update_charge_code_action_buttons_state()
        return tab

    def load_charge_codes_data(self):
        self.logger.info("Loading charge codes data for tab...")
        if not self.charge_codes_table or not self.charge_code_status_filter_combo:
            self.logger.error("Charge codes table or filter combo not initialized.")
            return
        try:
            status_filter = self.charge_code_status_filter_combo.currentText().lower()
            self.logger.info(f"Charge code status filter: {status_filter}")
            self._active_filters[self.CHARGE_CODE_TAB_INDEX] = status_filter
            charge_codes = self.charge_code_controller.get_all_charge_codes(
                status_filter=status_filter
            )
            self.charge_codes_table.setRowCount(0)
            for c_obj in charge_codes:
                row_position = self.charge_codes_table.rowCount()
                self.charge_codes_table.insertRow(row_position)
                self.charge_codes_table.setItem(
                    row_position, 0, QTableWidgetItem(c_obj.code)
                )
                self.charge_codes_table.setItem(
                    row_position, 1, QTableWidgetItem(c_obj.alternate_code or "")
                )
                category_path_str = "N/A"
                if c_obj.category_id:
                    path_objects = self.charge_code_controller.get_category_path(
                        c_obj.category_id
                    )
                    if path_objects:
                        category_path_str = " > ".join(
                            [p["name"] for p in path_objects]
                        )
                self.charge_codes_table.setItem(
                    row_position, 2, QTableWidgetItem(category_path_str)
                )
                self.charge_codes_table.setItem(
                    row_position, 3, QTableWidgetItem(c_obj.description)
                )
                price_str = (
                    f"${c_obj.standard_charge:.2f}"
                    if c_obj.standard_charge is not None
                    else "$0.00"
                )
                price_item = QTableWidgetItem(price_str)
                price_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.charge_codes_table.setItem(row_position, 4, price_item)
                self.charge_codes_table.setItem(
                    row_position,
                    5,
                    QTableWidgetItem("Yes" if c_obj.is_active else "No"),
                )
                self.charge_codes_table.item(row_position, 0).setData(
                    Qt.ItemDataRole.UserRole, c_obj.id
                )
            self.logger.info(
                f"Loaded {len(charge_codes)} charge codes based on filter '{status_filter}'."
            )
        except AttributeError as ae:
            self.logger.error(f"Error loading charge codes: {ae}", exc_info=True)
            self.show_error("Load Error", f"Could not load charge codes: {ae}")
        except Exception as e:
            self.logger.error(f"General error loading charge codes: {e}", exc_info=True)
            self.show_error("Load Error", f"An unexpected error occurred: {e}")
        self._update_charge_code_action_buttons_state()

    def _on_charge_code_filter_changed(self, index: int):
        self.load_charge_codes_data()

    def _add_charge_code(self):
        dialog = AddEditChargeCodeDialog(
            self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_charge_codes_data()
            self.entity_updated.emit("charge_code")

    def _edit_selected_charge_code(self):
        if not self.charge_codes_table or not self.charge_codes_table.currentItem():
            self.show_info("Edit Charge Code", "Please select a charge code to edit.")
            return
        selected_row = self.charge_codes_table.currentRow()
        charge_code_id = self.charge_codes_table.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        charge_code_to_edit = self.charge_code_controller.get_charge_code_by_id(
            charge_code_id
        )
        if charge_code_to_edit:
            dialog = AddEditChargeCodeDialog(
                self,
                controller=self.charge_code_controller,
                charge_code=charge_code_to_edit,
                current_user_id=self.current_user_id,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_charge_codes_data()
                self.entity_updated.emit("charge_code")
        else:
            self.show_error(
                "Error", f"Charge code with ID '{charge_code_id}' not found."
            )
            self.load_charge_codes_data()

    def _toggle_selected_charge_code_active_status(self):
        if not self.charge_codes_table or not self.charge_codes_table.currentItem():
            self.show_info("Toggle Active Status", "Please select a charge code.")
            return
        selected_row = self.charge_codes_table.currentRow()
        charge_code_id = self.charge_codes_table.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        cc_obj = self.charge_code_controller.get_charge_code_by_id(charge_code_id)
        if not cc_obj:
            self.show_error("Error", f"Charge code {charge_code_id} not found.")
            return
        action = "deactivate" if cc_obj.is_active else "activate"
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} charge code '{cc_obj.code} - {cc_obj.description}'?",
        ):
            success, message = self.charge_code_controller.toggle_charge_code_status(
                charge_code_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_charge_codes_data()
                self.entity_updated.emit("charge_code")
            else:
                self.show_error("Error", message)

    def _delete_selected_charge_code(self):
        if not self.charge_codes_table or not self.charge_codes_table.currentItem():
            self.show_info(
                "Delete Charge Code", "Please select a charge code to delete."
            )
            return
        selected_row = self.charge_codes_table.currentRow()
        charge_code_id = self.charge_codes_table.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        charge_code_name = self.charge_codes_table.item(selected_row, 0).text()
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to permanently delete charge code '{charge_code_name}'?\nThis action cannot be undone.",
        ):
            success, message = self.charge_code_controller.delete_charge_code(
                charge_code_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_charge_codes_data()
                self.entity_updated.emit("charge_code_deleted")
            else:
                self.show_error("Delete Failed", message)

    def _update_charge_code_action_buttons_state(self):
        has_selection = (
            self.charge_codes_table is not None
            and self.charge_codes_table.currentItem() is not None
        )
        if self.edit_charge_code_btn:
            self.edit_charge_code_btn.setEnabled(has_selection)
        if self.toggle_charge_code_active_btn:
            self.toggle_charge_code_active_btn.setEnabled(has_selection)
        if self.delete_charge_code_btn:
            self.delete_charge_code_btn.setEnabled(has_selection)
        if (
            has_selection
            and self.toggle_charge_code_active_btn
            and self.charge_codes_table
        ):
            selected_row = self.charge_codes_table.currentRow()
            charge_code_id_item = self.charge_codes_table.item(selected_row, 0)
            if not charge_code_id_item:
                return
            charge_code_id = charge_code_id_item.data(Qt.ItemDataRole.UserRole)
            cc_obj = self.charge_code_controller.get_charge_code_by_id(charge_code_id)
            if cc_obj:
                action_text = "Deactivate" if cc_obj.is_active else "Activate"
                self.toggle_charge_code_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_charge_code_active_btn,
                    "toggle_inactive" if cc_obj.is_active else "standard",
                )

    # --- Owners Tab Methods ---
    def _create_owners_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        button_layout = self._create_standard_button_layout()
        self.add_owner_btn = QPushButton("➕ Add New Owner")
        self._apply_standard_button_style(self.add_owner_btn, "add")
        self.edit_owner_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_owner_btn, "edit")
        self.toggle_owner_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_owner_active_btn)
        self.delete_owner_btn = QPushButton("🗑️ Delete Selected")
        self._apply_standard_button_style(self.delete_owner_btn, "delete")
        button_layout.addWidget(self.add_owner_btn)
        button_layout.addWidget(self.edit_owner_btn)
        button_layout.addWidget(self.toggle_owner_active_btn)
        button_layout.addWidget(self.delete_owner_btn)
        top_bar_layout.addLayout(button_layout)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(QLabel("Filter Status:"))
        self.owner_status_filter_combo = QComboBox()
        self.owner_status_filter_combo.addItems(["Active", "Inactive", "All"])
        self.owner_status_filter_combo.setCurrentText(
            self._active_filters.get(self.OWNER_TAB_INDEX, "active")
        )
        self.owner_status_filter_combo.setStyleSheet(self.get_form_input_style())
        top_bar_layout.addWidget(self.owner_status_filter_combo)
        layout.addLayout(top_bar_layout)
        self.owners_table = self._create_table_widget(
            [
                "Account #",
                "Farm Name",
                "Last Name",
                "First Name",
                "City",
                "State",
                "Phone",
                "Active",
            ]
        )
        if self.owners_table:
            self.owners_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )
            self.owners_table.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.Stretch
            )
        layout.addWidget(self.owners_table)
        self._update_owner_action_buttons_state()
        return tab

    def load_owners_data(self):
        self.logger.info("Loading owners data for tab...")
        if not self.owners_table or not self.owner_status_filter_combo:
            self.logger.error("Owners table or filter combo not initialized.")
            return
        try:
            status_filter = self.owner_status_filter_combo.currentText().lower()
            self._active_filters[self.OWNER_TAB_INDEX] = status_filter
            owners = self.owner_controller.get_all_master_owners(
                status_filter=status_filter
            )
            self.owners_table.setRowCount(0)
            for owner_obj in owners:
                row_pos = self.owners_table.rowCount()
                self.owners_table.insertRow(row_pos)
                self.owners_table.setItem(
                    row_pos, 0, QTableWidgetItem(owner_obj.account_number or "")
                )
                self.owners_table.setItem(
                    row_pos, 1, QTableWidgetItem(owner_obj.farm_name or "")
                )
                self.owners_table.setItem(
                    row_pos, 2, QTableWidgetItem(owner_obj.last_name or "")
                )
                self.owners_table.setItem(
                    row_pos, 3, QTableWidgetItem(owner_obj.first_name or "")
                )
                self.owners_table.setItem(
                    row_pos, 4, QTableWidgetItem(owner_obj.city or "")
                )
                state_display = owner_obj.state_code or ""
                if (
                    hasattr(owner_obj, "state")
                    and owner_obj.state
                    and hasattr(owner_obj.state, "state_code")
                ):
                    state_display = owner_obj.state.state_code
                self.owners_table.setItem(row_pos, 5, QTableWidgetItem(state_display))
                self.owners_table.setItem(
                    row_pos, 6, QTableWidgetItem(owner_obj.phone or "")
                )
                self.owners_table.setItem(
                    row_pos, 7, QTableWidgetItem("Yes" if owner_obj.is_active else "No")
                )
                self.owners_table.item(row_pos, 0).setData(
                    Qt.ItemDataRole.UserRole, owner_obj.owner_id
                )
            self.logger.info(f"Loaded {len(owners)} owners.")
        except Exception as e:
            self.logger.error(f"Error loading owners: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load owners: {e}")
        self._update_owner_action_buttons_state()

    def _on_owner_filter_changed(self, index: int):
        self.load_owners_data()

    def _add_owner(self):
        dialog = AddEditOwnerDialog(
            self,
            owner_controller=self.owner_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_owners_data()
            self.entity_updated.emit("owner")

    def _edit_selected_owner(self):
        if not self.owners_table or not self.owners_table.currentItem():
            self.show_info("Edit Owner", "Please select an owner.")
            return
        selected_row = self.owners_table.currentRow()
        owner_id_item = self.owners_table.item(selected_row, 0)
        owner_id = owner_id_item.data(Qt.ItemDataRole.UserRole) or owner_id_item.text()
        owner_to_edit = self.owner_controller.get_owner_by_id(owner_id)
        if owner_to_edit:
            dialog = AddEditOwnerDialog(
                self,
                owner_controller=self.owner_controller,
                owner_object=owner_to_edit,
                current_user_id=self.current_user_id,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_owners_data()
                self.entity_updated.emit("owner")
        else:
            self.show_error("Error", f"Owner ID '{owner_id}' not found.")
            self.load_owners_data()

    def _toggle_selected_owner_active_status(self):
        if not self.owners_table or not self.owners_table.currentItem():
            self.show_info("Toggle Status", "Please select an owner.")
            return
        selected_row = self.owners_table.currentRow()
        owner_id_item = self.owners_table.item(selected_row, 0)
        owner_id = owner_id_item.data(Qt.ItemDataRole.UserRole) or owner_id_item.text()
        owner_obj = self.owner_controller.get_owner_by_id(owner_id)
        if not owner_obj:
            self.show_error("Error", f"Owner ID {owner_id} not found.")
            return
        action = "deactivate" if owner_obj.is_active else "activate"
        name_display = (
            owner_obj.farm_name
            or f"{owner_obj.first_name or ''} {owner_obj.last_name or ''}".strip()
            or f"ID: {owner_obj.owner_id}"
        )
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} owner '{name_display}'?",
        ):
            success, message = self.owner_controller.toggle_owner_active_status(
                owner_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_owners_data()
                self.entity_updated.emit("owner")
            else:
                self.show_error("Error", message)

    def _delete_selected_owner(self):
        if not self.owners_table or not self.owners_table.currentItem():
            self.show_info("Delete Owner", "Please select an owner to delete.")
            return
        selected_row = self.owners_table.currentRow()
        owner_id_item = self.owners_table.item(selected_row, 0)
        owner_id = owner_id_item.data(Qt.ItemDataRole.UserRole)
        display_name = (
            self.owners_table.item(selected_row, 1).text()
            or self.owners_table.item(selected_row, 2).text()
        )
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to permanently delete owner '{display_name}'?\nThis action cannot be undone.",
        ):
            success, message = self.owner_controller.delete_master_owner(
                owner_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_owners_data()
                self.entity_updated.emit("owner_deleted")
            else:
                self.show_error("Delete Failed", message)

    def _update_owner_action_buttons_state(self):
        has_selection = (
            self.owners_table is not None
            and self.owners_table.currentItem() is not None
        )
        if self.edit_owner_btn:
            self.edit_owner_btn.setEnabled(has_selection)
        if self.toggle_owner_active_btn:
            self.toggle_owner_active_btn.setEnabled(has_selection)
        if self.delete_owner_btn:
            self.delete_owner_btn.setEnabled(has_selection)
        if has_selection and self.toggle_owner_active_btn and self.owners_table:
            selected_row = self.owners_table.currentRow()
            owner_id_item = self.owners_table.item(selected_row, 0)
            if not owner_id_item:
                return
            owner_id = (
                owner_id_item.data(Qt.ItemDataRole.UserRole) or owner_id_item.text()
            )
            owner_obj = self.owner_controller.get_owner_by_id(owner_id)
            if owner_obj:
                action_text = "Deactivate" if owner_obj.is_active else "Activate"
                self.toggle_owner_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_owner_active_btn,
                    "toggle_inactive" if owner_obj.is_active else "standard",
                )

    # --- Company Profile Tab ---
    def _create_company_profile_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        title = QLabel("Company Profile Management")
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 14, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {AppConfig.DARK_TEXT_PRIMARY};")
        description = QLabel(
            "Here you can set your company's information, which will be used on invoices and other reports."
        )
        description.setStyleSheet(f"color: {AppConfig.DARK_TEXT_SECONDARY};")
        description.setWordWrap(True)
        self.edit_profile_btn = QPushButton("✏️ Edit Company Profile")
        self._apply_standard_button_style(self.edit_profile_btn, "edit")
        self.edit_profile_btn.setMinimumHeight(40)
        self.edit_profile_btn.setFixedWidth(250)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(self.edit_profile_btn)
        return tab

    def _launch_company_profile_dialog(self):
        dialog = CompanyProfileDialog(self, self.current_user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.entity_updated.emit("company_profile")
            self.show_info("Success", "Company profile has been updated.")
