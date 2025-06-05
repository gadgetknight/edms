# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.3.18
Purpose: Admin screen for managing users, locations, charge codes, categories, and owners.
         - Removed unnecessary super().setup_ui() call in setup_ui method.
Last Updated: June 4, 2025
Author: Gemini (based on user's previous version)

Changelog:
- v1.3.18 (2025-06-04):
    - Removed the call to `super().setup_ui()` from the `setup_ui` method
      to resolve an AttributeError. The BaseView.__init__ already calls
      the subclass's setup_ui.
- v1.3.17 (2025-06-04):
    - Changed import from `.dialogs.add_edit_master_owner_dialog import AddEditMasterOwnerDialog`
      to `from .dialogs.add_edit_owner_dialog import AddEditOwnerDialog` to match
      the user-provided filename.
- v1.3.16 (2025-06-04):
    - In `load_charge_codes_data`, changed `c_obj.charge_code_id` to `c_obj.id`
      to reflect the updated ChargeCode model primary key.
# ... (Rest of previous changelog)
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
from config.app_config import AppConfig  # Used for styling constants

from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.charge_code_controller import ChargeCodeController
from controllers.owner_controller import OwnerController

from models import (
    User,
    Location,
    ChargeCode,
    Owner as OwnerModel,
    ChargeCodeCategory,
)

# Dialog imports
from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .dialogs.add_edit_owner_dialog import AddEditOwnerDialog
from .dialogs.add_edit_charge_code_category_dialog import (
    AddEditChargeCodeCategoryDialog,
)


class UserManagementScreen(BaseView):
    """
    Main administrative screen for managing various system entities.
    """

    back_to_main_menu = Signal()
    entity_updated = Signal(str)

    USER_TAB_INDEX = 0
    LOCATION_TAB_INDEX = 1
    CATEGORY_PROCESS_TAB_INDEX = 2
    CHARGE_CODE_TAB_INDEX = 3
    OWNER_TAB_INDEX = 4

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"UserManagementScreen __init__ called for user: {current_user_id}"
        )
        super().__init__(
            parent
        )  # This will call self.setup_ui() due to BaseView's __init__

        self.current_user_id = current_user_id
        if not self.current_user_id:
            self.logger.error(
                "UserManagementScreen initialized without a current_user_id!"
            )

        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.charge_code_controller = ChargeCodeController()
        self.owner_controller = OwnerController()

        self.users_table: Optional[QTableWidget] = None
        self.add_user_btn: Optional[QPushButton] = None
        self.edit_user_btn: Optional[QPushButton] = None
        self.toggle_user_active_btn: Optional[QPushButton] = None

        self.locations_table: Optional[QTableWidget] = None
        self.add_location_btn: Optional[QPushButton] = None
        self.edit_location_btn: Optional[QPushButton] = None
        self.toggle_location_active_btn: Optional[QPushButton] = None

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
        self.charge_code_status_filter_combo: Optional[QComboBox] = None

        self.owners_table: Optional[QTableWidget] = None
        self.add_owner_btn: Optional[QPushButton] = None
        self.edit_owner_btn: Optional[QPushButton] = None
        self.toggle_owner_active_btn: Optional[QPushButton] = None

        self.tab_widget: Optional[QTabWidget] = None

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self._refresh_current_tab_data)

        self._active_filters: Dict[int, str] = {
            self.CATEGORY_PROCESS_TAB_INDEX: "active",
            self.CHARGE_CODE_TAB_INDEX: "active",
        }

        self.setWindowTitle("User and System Management")
        self.resize(1000, 700)
        self.logger.info("UserManagementScreen __init__ completed.")

    def setup_ui(self):
        self.logger.info("Setting up UserManagementScreen UI...")
        # MODIFIED: Removed super().setup_ui() call as BaseView.__init__ already calls this method.
        # super().setup_ui() # This line was causing the AttributeError

        main_layout = QVBoxLayout(
            self.central_widget
        )  # self.central_widget from BaseView
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_widget_style())

        users_tab_widget = self._create_users_tab()
        locations_tab_widget = self._create_locations_tab()
        categories_processes_tab_widget = self._create_categories_processes_tab()
        charge_codes_tab_widget = self._create_charge_codes_tab()
        owners_tab_widget = self._create_owners_tab()

        self.tab_widget.addTab(users_tab_widget, "👤 Manage Users")
        self.tab_widget.addTab(locations_tab_widget, "📍 Manage Locations")
        self.tab_widget.addTab(
            categories_processes_tab_widget, "🗂️ Manage Categories/Processes"
        )
        self.tab_widget.addTab(charge_codes_tab_widget, "💲 Manage Charge Codes")
        self.tab_widget.addTab(owners_tab_widget, "🤝 Manage Master Owners")

        main_layout.addWidget(self.tab_widget)
        self.central_widget.setLayout(main_layout)

        self._setup_connections()  # Call after UI elements are created
        if self.tab_widget:  # Ensure tab_widget is not None
            self.tab_widget.setCurrentIndex(0)
            self._refresh_current_tab_data()

        self.logger.info("UserManagementScreen UI setup complete.")

    # ... (Rest of the methods: _get_tab_widget_style, _create_standard_button_layout,
    #      _apply_standard_button_style, _setup_connections, _on_tab_changed,
    #      _refresh_current_tab_data, _create_table_widget,
    #      all User Tab methods, all Location Tab methods, all Charge Codes Tab methods,
    #      all Categories/Processes Tab methods, all Owners Tab methods remain unchanged
    #      from version 1.3.17, as they were not related to the super().setup_ui() error.)
    # For brevity, only the __init__ and setup_ui methods are shown with the fix.
    # The full content of the other methods should be retained from the previous complete version (v1.3.17).

    def _get_tab_widget_style(self) -> str:
        # (This method remains unchanged from version 1.3.17)
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
        # (This method remains unchanged from version 1.3.17)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        return button_layout

    def _apply_standard_button_style(
        self, button: QPushButton, button_type: str = "standard"
    ):
        # (This method remains unchanged from version 1.3.17)
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

    def _setup_connections(self):
        # (This method remains unchanged from version 1.3.17)
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
        if self.users_table:
            self.users_table.itemSelectionChanged.connect(
                self._update_user_action_buttons_state
            )

        if self.add_location_btn:
            self.add_location_btn.clicked.connect(self._add_location)
        if self.edit_location_btn:
            self.edit_location_btn.clicked.connect(self._edit_selected_location)
        if self.toggle_location_active_btn:
            self.toggle_location_active_btn.clicked.connect(
                self._toggle_selected_location_active_status
            )
        if self.locations_table:
            self.locations_table.itemSelectionChanged.connect(
                self._update_location_action_buttons_state
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
        if self.owners_table:
            self.owners_table.itemSelectionChanged.connect(
                self._update_owner_action_buttons_state
            )

        self.logger.debug("Connections setup complete.")

    def _on_tab_changed(self, index: int):
        # (This method remains unchanged from version 1.3.17)
        self.logger.info(
            f"Tab changed to index: {index}, new tab title: {self.tab_widget.tabText(index) if self.tab_widget else 'N/A'}"
        )
        self._refresh_current_tab_data()

    def _refresh_current_tab_data(self, force_reload: bool = False):
        # (This method remains unchanged from version 1.3.17)
        if not self.tab_widget:
            self.logger.warning("Tab widget not available for refresh.")
            return
        current_index = self.tab_widget.currentIndex()
        self.logger.debug(f"Refreshing data for tab index: {current_index}")
        if current_index == self.USER_TAB_INDEX:
            self.load_users_data()
        elif current_index == self.LOCATION_TAB_INDEX:
            self.load_locations_data()
        elif current_index == self.CATEGORY_PROCESS_TAB_INDEX:
            self.load_categories_processes_data()
        elif current_index == self.CHARGE_CODE_TAB_INDEX:
            self.load_charge_codes_data()
        elif current_index == self.OWNER_TAB_INDEX:
            self.load_owners_data()
        else:
            self.logger.warning(
                f"No data loading action defined for tab index {current_index}"
            )

    def _create_table_widget(self, headers: List[str]) -> QTableWidget:
        # (This method remains unchanged from version 1.3.17)
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
            QTableWidget::item:selected {{
                background-color: {AppConfig.DARK_HIGHLIGHT_BG};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
            }}
        """
        )
        table.horizontalHeader().setStretchLastSection(True)
        for i in range(len(headers) - 1):
            table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        return table

    # --- Users Tab Methods (unchanged from v1.3.17) ---
    def _create_users_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        button_layout = self._create_standard_button_layout()
        self.add_user_btn = QPushButton("➕ Add New User")
        self._apply_standard_button_style(self.add_user_btn, "add")
        self.edit_user_btn = QPushButton("✏️ Edit Selected User")
        self._apply_standard_button_style(self.edit_user_btn, "edit")
        self.toggle_user_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_user_active_btn)
        button_layout.addWidget(self.add_user_btn)
        button_layout.addWidget(self.edit_user_btn)
        button_layout.addWidget(self.toggle_user_active_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        self.users_table = self._create_table_widget(
            ["Login ID", "Full Name", "Email", "Roles", "Active", "Last Login"]
        )
        layout.addWidget(self.users_table)
        self._update_user_action_buttons_state()
        return tab

    def load_users_data(self):
        self.logger.info("Loading users data for tab...")
        if not self.users_table:
            self.logger.error("Users table not initialized.")
            return
        try:
            users = self.user_controller.get_all_users_with_roles()
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

    def _add_user(self):
        dialog = AddEditUserDialog(
            parent=self,
            controller=self.user_controller,
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
        user_id = user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
        user_to_edit = self.user_controller.get_user_by_id(user_id)
        if user_to_edit:
            dialog = AddEditUserDialog(
                parent=self,
                controller=self.user_controller,
                user=user_to_edit,
                current_user_id=self.current_user_id,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_users_data()
                self.entity_updated.emit("user")
        else:
            self.show_error("Error", f"User with ID '{user_id}' not found.")
            self.load_users_data()

    def _toggle_selected_user_active_status(self):
        if not self.users_table or not self.users_table.currentItem():
            self.show_info("Toggle Active Status", "Please select a user.")
            return
        selected_row = self.users_table.currentRow()
        user_id_item = self.users_table.item(selected_row, 0)
        user_id = user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
        user_obj = self.user_controller.get_user_by_id(user_id)
        if not user_obj:
            self.show_error("Error", f"User {user_id} not found.")
            return
        action = "deactivate" if user_obj.is_active else "activate"
        name_display = user_obj.user_name or user_obj.user_id
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} user '{name_display}'?",
        ):
            if user_obj.user_id == self.current_user_id and action == "deactivate":
                self.show_warning(
                    "Action Denied", "You cannot deactivate your own account."
                )
                return
            success, message = self.user_controller.toggle_user_active_status(
                user_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_users_data()
                self.entity_updated.emit("user")
            else:
                self.show_error("Error", message)

    def _update_user_action_buttons_state(self):
        has_selection = (
            self.users_table is not None and self.users_table.currentItem() is not None
        )
        if self.edit_user_btn:
            self.edit_user_btn.setEnabled(has_selection)
        if self.toggle_user_active_btn:
            self.toggle_user_active_btn.setEnabled(has_selection)
        if has_selection and self.toggle_user_active_btn and self.users_table:
            selected_row = self.users_table.currentRow()
            user_id_item = self.users_table.item(selected_row, 0)
            user_id = user_id_item.data(Qt.ItemDataRole.UserRole) or user_id_item.text()
            user_obj = self.user_controller.get_user_by_id(user_id)
            if user_obj:
                action_text = "Deactivate" if user_obj.is_active else "Activate"
                self.toggle_user_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_user_active_btn,
                    "toggle_inactive" if user_obj.is_active else "standard",
                )

    # --- Locations Tab Methods (unchanged from v1.3.17) ---
    def _create_locations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        button_layout = self._create_standard_button_layout()
        self.add_location_btn = QPushButton("➕ Add New Location")
        self._apply_standard_button_style(self.add_location_btn, "add")
        self.edit_location_btn = QPushButton("✏️ Edit Selected Location")
        self._apply_standard_button_style(self.edit_location_btn, "edit")
        self.toggle_location_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_location_active_btn)
        button_layout.addWidget(self.add_location_btn)
        button_layout.addWidget(self.edit_location_btn)
        button_layout.addWidget(self.toggle_location_active_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        self.locations_table = self._create_table_widget(
            ["Name", "Address", "City", "State", "Zip", "Contact", "Active"]
        )
        layout.addWidget(self.locations_table)
        self._update_location_action_buttons_state()
        return tab

    def load_locations_data(self):
        self.logger.info("Loading locations data for tab...")
        if not self.locations_table:
            self.logger.error("Locations table not initialized.")
            return
        try:
            locations = self.location_controller.get_all_locations_detailed()
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
                self.locations_table.setItem(
                    row_position, 3, QTableWidgetItem(loc_obj.state_code or "")
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
            self.logger.info(
                f"Loaded {len(locations)} locations with detailed address."
            )
        except Exception as e:
            self.logger.error(f"Error loading locations: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load locations: {e}")
        self._update_location_action_buttons_state()

    def _add_location(self):
        dialog = AddEditLocationDialog(
            parent=self,
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
                parent=self,
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
            success, message = self.location_controller.toggle_location_status(
                location_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_locations_data()
                self.entity_updated.emit("location")
            else:
                self.show_error("Error", message)

    def _update_location_action_buttons_state(self):
        has_selection = (
            self.locations_table is not None
            and self.locations_table.currentItem() is not None
        )
        if self.edit_location_btn:
            self.edit_location_btn.setEnabled(has_selection)
        if self.toggle_location_active_btn:
            self.toggle_location_active_btn.setEnabled(has_selection)
        if has_selection and self.toggle_location_active_btn and self.locations_table:
            selected_row = self.locations_table.currentRow()
            location_id_item = self.locations_table.item(selected_row, 0)
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

    # --- Charge Codes Tab Methods (unchanged from v1.3.17) ---
    def _create_charge_codes_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        top_bar_layout = QHBoxLayout()
        self.add_charge_code_btn = QPushButton("➕ Add New Charge Code")
        self._apply_standard_button_style(self.add_charge_code_btn, "add")
        self.edit_charge_code_btn = QPushButton("✏️ Edit Selected")
        self._apply_standard_button_style(self.edit_charge_code_btn, "edit")
        self.toggle_charge_code_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_charge_code_active_btn)
        top_bar_layout.addWidget(self.add_charge_code_btn)
        top_bar_layout.addWidget(self.edit_charge_code_btn)
        top_bar_layout.addWidget(self.toggle_charge_code_active_btn)
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
            charge_codes = (
                self.charge_code_controller.get_all_charge_codes_with_category_path(
                    status_filter=status_filter
                )
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
                category_display = getattr(c_obj, "category_path_display", "N/A")
                self.charge_codes_table.setItem(
                    row_position, 2, QTableWidgetItem(category_display)
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
            parent=self,
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
                parent=self,
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
            success, message = (
                self.charge_code_controller.toggle_charge_code_active_status(
                    charge_code_id, self.current_user_id
                )
            )
            if success:
                self.show_info("Success", message)
                self.load_charge_codes_data()
                self.entity_updated.emit("charge_code")
            else:
                self.show_error("Error", message)

    def _update_charge_code_action_buttons_state(self):
        has_selection = (
            self.charge_codes_table is not None
            and self.charge_codes_table.currentItem() is not None
        )
        if self.edit_charge_code_btn:
            self.edit_charge_code_btn.setEnabled(has_selection)
        if self.toggle_charge_code_active_btn:
            self.toggle_charge_code_active_btn.setEnabled(has_selection)
        if (
            has_selection
            and self.toggle_charge_code_active_btn
            and self.charge_codes_table
        ):
            selected_row = self.charge_codes_table.currentRow()
            charge_code_id = self.charge_codes_table.item(selected_row, 0).data(
                Qt.ItemDataRole.UserRole
            )
            cc_obj = self.charge_code_controller.get_charge_code_by_id(charge_code_id)
            if cc_obj:
                action_text = "Deactivate" if cc_obj.is_active else "Activate"
                self.toggle_charge_code_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_charge_code_active_btn,
                    "toggle_inactive" if cc_obj.is_active else "standard",
                )

    # --- Categories/Processes Tab Methods (unchanged from v1.3.17) ---
    def _create_categories_processes_tab(self) -> QWidget:
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
            f"""
            QTreeWidget {{ background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; }}
            QHeaderView::section {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_SECONDARY}; padding: 5px; border: none; border-bottom: 1px solid {AppConfig.DARK_BORDER}; font-weight: 500; }}
            QTreeWidget::item:selected {{ background-color: {AppConfig.DARK_HIGHLIGHT_BG}; color: {AppConfig.DARK_HIGHLIGHT_TEXT}; }}
            QTreeWidget::item {{ padding: 3px; }}
        """
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
        status_filter = self.category_filter_combo.currentText().lower()
        self.logger.info(f"CCC active_filter: {status_filter}")
        self._active_filters[self.CATEGORY_PROCESS_TAB_INDEX] = status_filter
        try:
            level1_categories = self.charge_code_controller.get_charge_code_categories(
                level=1, status_filter=status_filter
            )
            for cat_l1 in level1_categories:
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
                level2_processes = (
                    self.charge_code_controller.get_charge_code_categories(
                        parent_id=cat_l1.category_id,
                        level=2,
                        status_filter=status_filter,
                    )
                )
                for cat_l2 in level2_processes:
                    l2_item = QTreeWidgetItem(l1_item)
                    l2_item.setText(0, cat_l2.name)
                    l2_item.setText(1, str(cat_l2.level))
                    l2_item.setText(2, "Active" if cat_l2.is_active else "Inactive")
                    l2_item.setText(3, str(cat_l2.category_id))
                    l2_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        {"id": cat_l2.category_id, "level": 2, "obj": cat_l2},
                    )
            self.categories_tree.expandAll()
            self.logger.info(
                f"Displayed {len(level1_categories)} top-level categories in tree based on filter '{status_filter}'."
            )
        except Exception as e:
            self.logger.error(f"Error loading categories/processes: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load categories: {e}")
        self._update_category_action_buttons_state()

    def _on_category_filter_changed(self, index: int):
        self.load_categories_processes_data()

    def _add_category_or_process(self, is_process: bool = False):
        parent_category_id: Optional[int] = None
        parent_category_name: Optional[str] = None
        selected_item = (
            self.categories_tree.currentItem() if self.categories_tree else None
        )
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
            parent_category_id = item_data.get("id")
            parent_category_name = selected_item.text(0)
        dialog_title = "Add New Process" if is_process else "Add New Category"
        level_to_add = 2 if is_process else 1
        dialog = AddEditChargeCodeCategoryDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            level=level_to_add,
            parent_id=parent_category_id,
            parent_name=parent_category_name,
            category_to_edit=None,
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
        category_id = item_data.get("id")
        category_to_edit = self.charge_code_controller.get_category_by_id(category_id)
        if not category_to_edit:
            self.show_error(
                "Error",
                f"Could not find category/process with ID {category_id} to edit.",
            )
            self.load_categories_processes_data()
            return
        parent_name_for_dialog: Optional[str] = None
        if category_to_edit.parent:
            parent_name_for_dialog = category_to_edit.parent.name
        dialog = AddEditChargeCodeCategoryDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            level=category_to_edit.level,
            parent_id=category_to_edit.parent_id,
            parent_name=parent_name_for_dialog,
            category_to_edit=category_to_edit,
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
            item_obj = self.charge_code_controller.get_category_by_id(item_id)
        if not item_obj:
            self.show_error("Error", f"Item with ID {item_id} not found.")
            return
        action = "deactivate" if item_obj.is_active else "activate"
        item_name_display = item_obj.name
        if self.show_question(
            f"Confirm {action.capitalize()}",
            f"Are you sure you want to {action} '{item_name_display}'?",
        ):
            success, message = (
                self.charge_code_controller.toggle_category_active_status(
                    item_id, self.current_user_id
                )
            )
            if success:
                self.show_info("Success", message)
                self.load_categories_processes_data()
                self.entity_updated.emit("charge_code_category")
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
            f"Are you sure you want to permanently delete '{item_name}'? This action cannot be undone.",
        ):
            success, message = self.charge_code_controller.delete_category_or_process(
                item_id, self.current_user_id
            )
            if success:
                self.show_info("Success", message)
                self.load_categories_processes_data()
                self.entity_updated.emit("charge_code_category_deleted")
            else:
                self.show_error("Delete Failed", message)

    def _update_category_action_buttons_state(self):
        if not self.categories_tree:
            return
        has_selection = self.categories_tree.currentItem() is not None
        is_l1_selected = False
        if has_selection:
            item_data = self.categories_tree.currentItem().data(
                0, Qt.ItemDataRole.UserRole
            )
            if item_data and item_data.get("level") == 1:
                is_l1_selected = True
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
        if (
            has_selection
            and self.toggle_category_process_active_btn
            and self.categories_tree
        ):
            item_data = self.categories_tree.currentItem().data(
                0, Qt.ItemDataRole.UserRole
            )
            item_obj: Optional[ChargeCodeCategory] = (
                item_data.get("obj") if item_data else None
            )
            if item_obj:
                action_text = "Deactivate" if item_obj.is_active else "Activate"
                self.toggle_category_process_active_btn.setText(
                    f"🔄 {action_text} Selected"
                )
                self._apply_standard_button_style(
                    self.toggle_category_process_active_btn,
                    "toggle_inactive" if item_obj.is_active else "standard",
                )

    # --- Owners Tab Methods (unchanged from v1.3.17, uses corrected AddEditOwnerDialog) ---
    def _create_owners_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        button_layout = self._create_standard_button_layout()
        self.add_owner_btn = QPushButton("➕ Add New Owner")
        self._apply_standard_button_style(self.add_owner_btn, "add")
        self.edit_owner_btn = QPushButton("✏️ Edit Selected Owner")
        self._apply_standard_button_style(self.edit_owner_btn, "edit")
        self.toggle_owner_active_btn = QPushButton("🔄 Toggle Active Status")
        self._apply_standard_button_style(self.toggle_owner_active_btn)
        button_layout.addWidget(self.add_owner_btn)
        button_layout.addWidget(self.edit_owner_btn)
        button_layout.addWidget(self.toggle_owner_active_btn)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
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
        if not self.owners_table:
            self.logger.error("Owners table not initialized.")
            return
        try:
            owners = self.owner_controller.get_all_owners()
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
                self.owners_table.setItem(
                    row_pos, 5, QTableWidgetItem(owner_obj.state_code or "")
                )
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

    def _add_owner(self):
        dialog = AddEditOwnerDialog(
            parent=self,
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
        owner_id = self.owners_table.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        owner_to_edit = self.owner_controller.get_owner_by_id(owner_id)
        if owner_to_edit:
            dialog = AddEditOwnerDialog(
                parent=self,
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
        owner_id = self.owners_table.item(selected_row, 0).data(
            Qt.ItemDataRole.UserRole
        )
        owner_obj = self.owner_controller.get_owner_by_id(owner_id)
        if not owner_obj:
            self.show_error("Error", f"Owner ID {owner_id} not found.")
            return
        action = "deactivate" if owner_obj.is_active else "activate"
        name_display = (
            owner_obj.farm_name
            or f"{owner_obj.first_name or ''} {owner_obj.last_name or ''}".strip()
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

    def _update_owner_action_buttons_state(self):
        has_selection = (
            self.owners_table is not None
            and self.owners_table.currentItem() is not None
        )
        if self.edit_owner_btn:
            self.edit_owner_btn.setEnabled(has_selection)
        if self.toggle_owner_active_btn:
            self.toggle_owner_active_btn.setEnabled(has_selection)
        if has_selection and self.toggle_owner_active_btn and self.owners_table:
            owner_id = self.owners_table.item(self.owners_table.currentRow(), 0).data(
                Qt.ItemDataRole.UserRole
            )
            owner_obj = self.owner_controller.get_owner_by_id(owner_id)
            if owner_obj:
                action_text = "Deactivate" if owner_obj.is_active else "Activate"
                self.toggle_owner_active_btn.setText(f"🔄 {action_text} Selected")
                self._apply_standard_button_style(
                    self.toggle_owner_active_btn,
                    "toggle_inactive" if owner_obj.is_active else "standard",
                )
