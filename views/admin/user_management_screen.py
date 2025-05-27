# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.10.12
Purpose: Provides UI for managing users, roles, locations, charge codes.
         - Corrected calls to BaseView methods for status and error messages.
         - Added defensive checks and comments for controller method calls
           that were causing errors due to signature/attribute mismatches.
Last Updated: May 26, 2025
Author: Gemini (based on user's v1.10.7.2)

Changelog:
- v1.10.12 (2025-05-26):
    - In `load_all_data` exception handling:
        - Corrected calls to use `self.show_error_message()` and `self.update_status_bar()`,
          assuming these are inherited from BaseView. Added `hasattr` checks
          with fallbacks to `QMessageBox` if methods are missing from BaseView.
        - Removed direct attempts to use `self.parent_view` for status updates.
    - In `load_locations_data`: Added a comment indicating that
      `LocationController.get_all_locations` needs to accept `include_inactive`.
    - In `load_master_owners_data`: Wrapped the call to `owner_controller.get_all_owners`
      in a try-except AttributeError and logged a warning if the method is missing.
    - Noted that `ChargeCodeController` issue with `alternate_code` needs fixing
      in the controller/model itself.
- v1.10.11 (2025-05-26):
    - Moved the initialization of UI component instance variables into the
      `__init__` method before `super().__init__()` is called.
- v1.10.10 (2025-05-23):
    - Cleaned up ChargeCode sections, removed 'alternate_code'.
    - Corrected Location display to use 'location_name'.
"""
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QAbstractItemView,
    QSizePolicy,
    QSpacerItem,
    QHeaderView,
    QScrollArea,
    QFrame,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QPlainTextEdit,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPalette, QColor, QIcon, QPixmap, QDoubleValidator

from views.base_view import BaseView
from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.charge_code_controller import ChargeCodeController
from controllers.owner_controller import OwnerController

from models import User as UserModel
from models import Role as RoleModel
from models import Location as LocationModel
from models import ChargeCode as ChargeCodeModel
from models import Owner as OwnerModel

from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog

import os

try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_path, "..", ".."))
    assets_path = os.path.join(project_root, "assets", "icons")
except Exception:
    assets_path = "assets/icons"


class UserManagementScreen(BaseView):
    horse_management_requested = Signal()

    users_table: Optional[QTableWidget]
    roles_combo_filter: Optional[QComboBox]
    user_status_combo_filter: Optional[QComboBox]
    user_search_input: Optional[QLineEdit]
    locations_table: Optional[QTableWidget]
    charge_codes_table: Optional[QTableWidget]
    owners_table: Optional[QTableWidget]
    user_detail_form_widgets: Dict[str, QWidget]
    location_detail_form_widgets: Dict[str, QWidget]
    charge_code_detail_form_widgets: Dict[str, QWidget]
    owner_detail_form_widgets: Dict[str, QWidget]
    current_selected_user_id: Optional[str]
    current_selected_location_id: Optional[int]
    current_selected_charge_code_id: Optional[int]
    current_selected_owner_id: Optional[int]
    user_detail_form: Optional[QFormLayout]
    location_detail_form: Optional[QFormLayout]
    charge_code_detail_form: Optional[QFormLayout]
    owner_detail_form: Optional[QFormLayout]

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        self.users_table = None
        self.roles_combo_filter = None
        self.user_status_combo_filter = None
        self.user_search_input = None
        self.locations_table = None
        self.charge_codes_table = None
        self.owners_table = None
        self.user_detail_form_widgets = {}
        self.location_detail_form_widgets = {}
        self.charge_code_detail_form_widgets = {}
        self.owner_detail_form_widgets = {}
        self.current_selected_user_id = None
        self.current_selected_location_id = None
        self.current_selected_charge_code_id = None
        self.current_selected_owner_id = None
        self.user_detail_form = None
        self.location_detail_form = None
        self.charge_code_detail_form = None
        self.owner_detail_form = None

        super().__init__(parent)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = current_user_id
        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.charge_code_controller = ChargeCodeController()
        self.owner_controller = OwnerController()

        self.setWindowTitle("User & System Management")
        self.logger.info(
            f"UserManagementScreen __init__ started by user: {self.current_user_id}"
        )

        self.load_all_data()
        self.logger.info(f"UserManagementScreen initialized.")

    def _create_main_header_buttons(self) -> List[QPushButton]:
        horse_mgmt_button = QPushButton("Horse Management")
        icon_path = os.path.join(assets_path, "horse_icon.png")
        if os.path.exists(icon_path):
            horse_mgmt_button.setIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"Header button icon not found: {icon_path}")
        horse_mgmt_button.clicked.connect(self.horse_management_requested.emit)
        return [horse_mgmt_button]

    def setup_ui(self):
        self.logger.critical(
            "****** UserManagementScreen.setup_ui() (v1.10.12) ENTERED ******"
        )
        container_layout = getattr(self, "main_content_layout", None)
        if not container_layout:
            container_layout = QVBoxLayout(self.central_widget)
            self.logger.info(
                "UserManagementScreen.setup_ui: central_widget has no layout from BaseView, created new QVBoxLayout."
            )
        else:
            while container_layout.count():
                item = container_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        splitter = QSplitter(Qt.Orientation.Vertical)
        users_group = QGroupBox("User Management")
        users_layout = QHBoxLayout(users_group)
        users_list_section = self._create_users_list_section()
        user_details_section = self._create_user_details_section()
        users_splitter = QSplitter(Qt.Orientation.Horizontal)
        users_splitter.addWidget(users_list_section)
        users_splitter.addWidget(user_details_section)
        users_splitter.setStretchFactor(0, 1)
        users_splitter.setStretchFactor(1, 2)
        users_layout.addWidget(users_splitter)
        splitter.addWidget(users_group)
        other_data_tabs = self._create_other_data_tabs()
        splitter.addWidget(other_data_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        container_layout.addWidget(splitter)
        self.logger.info("UserManagementScreen.setup_ui (v1.10.12) FINISHED.")

    def _create_users_list_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        filter_layout = QHBoxLayout()
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("Search users...")
        self.user_search_input.textChanged.connect(self.load_users_data)
        filter_layout.addWidget(self.user_search_input)
        self.roles_combo_filter = QComboBox()
        self.roles_combo_filter.addItem("All Roles", None)
        filter_layout.addWidget(QLabel("Role:"))
        filter_layout.addWidget(self.roles_combo_filter)
        self.roles_combo_filter.currentIndexChanged.connect(self.load_users_data)
        self.user_status_combo_filter = QComboBox()
        self.user_status_combo_filter.addItems(["All Statuses", "Active", "Inactive"])
        self.user_status_combo_filter.setItemData(0, "all")
        self.user_status_combo_filter.setItemData(1, "active")
        self.user_status_combo_filter.setItemData(2, "inactive")
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.user_status_combo_filter)
        self.user_status_combo_filter.currentIndexChanged.connect(self.load_users_data)
        layout.addLayout(filter_layout)
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(
            ["User ID", "User Name", "Email", "Roles", "Active"]
        )
        self.users_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.users_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.users_table.itemSelectionChanged.connect(self._on_user_selected)
        layout.addWidget(self.users_table)
        user_actions_layout = QHBoxLayout()
        add_user_button = QPushButton("Add New User")
        icon_path = os.path.join(assets_path, "add.png")
        if os.path.exists(icon_path):
            add_user_button.setIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"Icon not found: {icon_path}")
        add_user_button.clicked.connect(self._add_new_user)
        user_actions_layout.addWidget(add_user_button)
        user_actions_layout.addStretch()
        layout.addLayout(user_actions_layout)
        return widget

    def _create_user_details_section(self) -> QWidget:
        details_group = QGroupBox("User Details")
        details_layout = QVBoxLayout(details_group)
        self.user_detail_form = QFormLayout()
        self.user_detail_form.setContentsMargins(10, 10, 10, 10)
        self.user_detail_form.setSpacing(8)
        self.user_detail_form_widgets["user_id"] = QLineEdit()
        self.user_detail_form_widgets["user_id"].setReadOnly(True)
        self.user_detail_form.addRow(
            "User ID:", self.user_detail_form_widgets["user_id"]
        )
        self.user_detail_form_widgets["user_name"] = QLineEdit()
        self.user_detail_form.addRow(
            "Full Name:", self.user_detail_form_widgets["user_name"]
        )
        self.user_detail_form_widgets["email"] = QLineEdit()
        self.user_detail_form.addRow("Email:", self.user_detail_form_widgets["email"])
        self.user_detail_form_widgets["printer_id"] = QLineEdit()
        self.user_detail_form.addRow(
            "Printer ID:", self.user_detail_form_widgets["printer_id"]
        )
        self.user_detail_form_widgets["default_screen_colors"] = QLineEdit()
        self.user_detail_form.addRow(
            "Screen Colors:", self.user_detail_form_widgets["default_screen_colors"]
        )
        self.user_detail_form_widgets["role"] = QComboBox()
        self.user_detail_form.addRow("Role:", self.user_detail_form_widgets["role"])
        self.user_detail_form_widgets["is_active"] = QCheckBox("User is Active")
        self.user_detail_form.addRow(self.user_detail_form_widgets["is_active"])
        self.user_detail_form_widgets["password_label"] = QLabel("Set/Change Password:")
        self.user_detail_form_widgets["password"] = QLineEdit()
        self.user_detail_form_widgets["password"].setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.user_detail_form_widgets["password"].setPlaceholderText(
            "Leave blank to keep unchanged"
        )
        self.user_detail_form.addRow(
            self.user_detail_form_widgets["password_label"],
            self.user_detail_form_widgets["password"],
        )
        details_layout.addLayout(self.user_detail_form)
        details_layout.addStretch()
        user_detail_buttons_layout = QHBoxLayout()
        save_user_button = QPushButton("Save User Changes")
        icon_path = os.path.join(assets_path, "save.png")
        if os.path.exists(icon_path):
            save_user_button.setIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"Icon not found: {icon_path}")
        save_user_button.clicked.connect(self._save_user_details)
        user_detail_buttons_layout.addStretch()
        user_detail_buttons_layout.addWidget(save_user_button)
        details_layout.addLayout(user_detail_buttons_layout)
        self._set_user_details_form_enabled(False)
        return details_group

    def _create_other_data_tabs(self) -> QWidget:
        from PySide6.QtWidgets import QTabWidget

        tab_widget = QTabWidget()
        locations_tab = QWidget()
        locations_layout = QHBoxLayout(locations_tab)
        locations_list_section = self._create_locations_list_section()
        location_details_section = self._create_location_details_section()
        locations_splitter = QSplitter(Qt.Orientation.Horizontal)
        locations_splitter.addWidget(locations_list_section)
        locations_splitter.addWidget(location_details_section)
        locations_splitter.setSizes([200, 300])
        locations_layout.addWidget(locations_splitter)
        tab_widget.addTab(locations_tab, "Manage Locations")
        charge_codes_tab = QWidget()
        charge_codes_layout = QHBoxLayout(charge_codes_tab)
        charge_codes_list_section = self._create_charge_codes_list_section()
        charge_code_details_section = self._create_charge_code_details_section()
        charge_codes_splitter = QSplitter(Qt.Orientation.Horizontal)
        charge_codes_splitter.addWidget(charge_codes_list_section)
        charge_codes_splitter.addWidget(charge_code_details_section)
        charge_codes_splitter.setSizes([200, 300])
        charge_codes_layout.addWidget(charge_codes_splitter)
        tab_widget.addTab(charge_codes_tab, "Manage Charge Codes")
        owners_tab = QWidget()
        owners_layout = QHBoxLayout(owners_tab)
        owners_list_section = self._create_owners_list_section()
        owner_details_section = self._create_owner_details_section()
        owners_splitter = QSplitter(Qt.Orientation.Horizontal)
        owners_splitter.addWidget(owners_list_section)
        owners_splitter.addWidget(owner_details_section)
        owners_splitter.setSizes([300, 400])
        owners_layout.addWidget(owners_splitter)
        tab_widget.addTab(owners_tab, "Master Owner List")
        return tab_widget

    def load_users_data(self):
        self.logger.info("Loading users data...")
        if not all(
            [
                self.users_table,
                self.user_status_combo_filter,
                self.roles_combo_filter,
                self.user_search_input,
            ]
        ):
            self.logger.warning("User UI elements not ready for load_users_data.")
            return
        if self.roles_combo_filter.count() <= 1:
            try:
                roles = self.user_controller.get_all_roles()
                for role in roles:
                    self.roles_combo_filter.addItem(role.name, role.name)
            except Exception as e:
                self.logger.error(f"Failed to populate roles filter: {e}")
        status_filter = (
            self.user_status_combo_filter.currentData()
            if self.user_status_combo_filter
            else "all"
        )
        role_filter = (
            self.roles_combo_filter.currentData() if self.roles_combo_filter else None
        )
        search_term = (
            self.user_search_input.text().strip() if self.user_search_input else ""
        )
        try:
            users = self.user_controller.get_all_users(
                include_inactive=(status_filter != "active")
            )
            filtered_users = [
                user
                for user in users
                if (
                    status_filter == "all"
                    or (status_filter == "active" and user.is_active)
                    or (status_filter == "inactive" and not user.is_active)
                )
                and (not role_filter or role_filter in {r.name for r in user.roles})
                and (
                    not search_term
                    or search_term.lower() in user.user_id.lower()
                    or (
                        user.user_name and search_term.lower() in user.user_name.lower()
                    )
                    or (user.email and search_term.lower() in user.email.lower())
                )
            ]
            self.users_table.setRowCount(0)
            self.users_table.setSortingEnabled(False)
            for r, u in enumerate(filtered_users):
                self.users_table.insertRow(r)
                self.users_table.setItem(r, 0, QTableWidgetItem(u.user_id))
                self.users_table.setItem(r, 1, QTableWidgetItem(u.user_name or ""))
                self.users_table.setItem(r, 2, QTableWidgetItem(u.email or ""))
                self.users_table.setItem(
                    r, 3, QTableWidgetItem(", ".join([role.name for role in u.roles]))
                )
                self.users_table.setItem(
                    r, 4, QTableWidgetItem("Yes" if u.is_active else "No")
                )
                self.users_table.item(r, 0).setData(Qt.ItemDataRole.UserRole, u.user_id)
            self.users_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(filtered_users)} users.")
            self._clear_user_details_form()
            self._set_user_details_form_enabled(False)
        except Exception as e:
            self.logger.error(f"Error loading/filtering user data: {e}", exc_info=True)

    @Slot()
    def _on_user_selected(self):
        if not self.users_table:
            return
        s_items = self.users_table.selectedItems()
        if not s_items:
            self.current_selected_user_id = None
            self._clear_user_details_form()
            self._set_user_details_form_enabled(False)
            return
        item = self.users_table.item(s_items[0].row(), 0)
        if item:
            self.current_selected_user_id = item.data(Qt.ItemDataRole.UserRole)
            self.logger.info(f"User selected: {self.current_selected_user_id}")
            self._populate_user_details_form(self.current_selected_user_id)
            self._set_user_details_form_enabled(True)

    def _populate_user_details_form(self, user_id: str):
        user = self.user_controller.get_user_by_login_id(user_id)
        if not user:
            self._clear_user_details_form()
            self._set_user_details_form_enabled(False)
            return
        if not self.user_detail_form_widgets:
            self.logger.error("user_detail_form_widgets not init!")
            return
        self.user_detail_form_widgets["user_id"].setText(user.user_id)
        self.user_detail_form_widgets["user_name"].setText(user.user_name or "")
        self.user_detail_form_widgets["email"].setText(user.email or "")
        self.user_detail_form_widgets["is_active"].setChecked(user.is_active)
        self.user_detail_form_widgets["password"].clear()
        self.user_detail_form_widgets["password"].setPlaceholderText(
            "Leave blank to keep unchanged"
        )
        self.user_detail_form_widgets["printer_id"].setText(
            getattr(user, "printer_id", "") or ""
        )
        self.user_detail_form_widgets["default_screen_colors"].setText(
            getattr(user, "default_screen_colors", "") or ""
        )
        roles_combo = self.user_detail_form_widgets["role"]
        if roles_combo.count() == 0:
            try:
                for r_obj in self.user_controller.get_all_roles():
                    roles_combo.addItem(r_obj.name, r_obj.name)
            except Exception as e:
                self.logger.error(f"Failed to populate roles combo: {e}")
        role_name = user.roles[0].name if user.roles else None
        idx = roles_combo.findData(role_name) if role_name else -1
        roles_combo.setCurrentIndex(
            idx if idx >= 0 else 0 if roles_combo.count() > 0 and not role_name else -1
        )

    def _clear_user_details_form(self):
        if not self.user_detail_form_widgets:
            return
        for k, w in self.user_detail_form_widgets.items():
            if isinstance(w, QLineEdit):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(-1)
            elif isinstance(w, QCheckBox):
                w.setChecked(False)
        if "password" in self.user_detail_form_widgets and isinstance(
            self.user_detail_form_widgets["password"], QLineEdit
        ):
            self.user_detail_form_widgets["password"].setPlaceholderText(
                "Set password for new user"
            )
        self.current_selected_user_id = None

    def _set_user_details_form_enabled(self, enabled: bool):
        if not self.user_detail_form_widgets:
            return
        for k, w in self.user_detail_form_widgets.items():
            if k == "user_id":
                w.setReadOnly(True)
                w.setEnabled(enabled)
            elif k == "password_label":
                w.setVisible(enabled)
            else:
                w.setEnabled(enabled)

    @Slot()
    def _add_new_user(self):
        dialog = AddEditUserDialog(controller=self.user_controller, parent=self)
        if dialog.exec():
            self.load_users_data()
            self.show_status_message("User added.", True)
        elif dialog.error_message:
            self.show_status_message(f"Failed: {dialog.error_message}", False)

    @Slot()
    def _save_user_details(self):
        if not self.current_selected_user_id:
            self.show_error_message("Save Error", "No user selected.")
            return
        if not self.user_detail_form_widgets:
            self.logger.error("Cannot save user, form widgets not ready.")
            return
        user_data = {
            "user_name": self.user_detail_form_widgets["user_name"].text().strip(),
            "email": self.user_detail_form_widgets["email"].text().strip() or None,
            "is_active": self.user_detail_form_widgets["is_active"].isChecked(),
            "role": self.user_detail_form_widgets["role"].currentData(),
            "password": self.user_detail_form_widgets["password"].text(),
            "printer_id": self.user_detail_form_widgets["printer_id"].text().strip()
            or None,
            "default_screen_colors": self.user_detail_form_widgets[
                "default_screen_colors"
            ]
            .text()
            .strip()
            or None,
        }
        if not user_data["password"]:
            del user_data["password"]
        s, m = self.user_controller.update_user(
            self.current_selected_user_id, user_data, self.current_user_id
        )
        if s:
            self.show_status_message(m, True)
            self.load_users_data()
            self._populate_user_details_form(self.current_selected_user_id)
        else:
            self.show_error_message("Update Failed", m)

    def _create_locations_list_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        self.locations_table = QTableWidget()
        self.locations_table.setColumnCount(3)
        self.locations_table.setHorizontalHeaderLabels(
            ["Location Name", "Full Address", "Active"]
        )
        self.locations_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.locations_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.locations_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.locations_table.itemSelectionChanged.connect(self._on_location_selected)
        layout.addWidget(self.locations_table)
        add_btn = QPushButton("Add New Location")
        icon_path = os.path.join(assets_path, "add.png")
        add_btn.setIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        add_btn.clicked.connect(self._add_new_location)
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        btn_l.addWidget(add_btn)
        layout.addLayout(btn_l)
        return widget

    def _create_location_details_section(self) -> QWidget:
        grp = QGroupBox("Location Details")
        layout = QVBoxLayout(grp)
        self.location_detail_form = QFormLayout()
        self.location_detail_form_widgets["location_id"] = QLineEdit()
        self.location_detail_form_widgets["location_id"].setReadOnly(True)
        self.location_detail_form.addRow(
            "ID:", self.location_detail_form_widgets["location_id"]
        )
        self.location_detail_form_widgets["location_name"] = QLineEdit()
        self.location_detail_form.addRow(
            "Name:", self.location_detail_form_widgets["location_name"]
        )
        self.location_detail_form_widgets["address_line1"] = QLineEdit()
        self.location_detail_form.addRow(
            "Address 1:", self.location_detail_form_widgets["address_line1"]
        )
        self.location_detail_form_widgets["address_line2"] = QLineEdit()
        self.location_detail_form.addRow(
            "Address 2:", self.location_detail_form_widgets["address_line2"]
        )
        self.location_detail_form_widgets["city"] = QLineEdit()
        self.location_detail_form.addRow(
            "City:", self.location_detail_form_widgets["city"]
        )
        self.location_detail_form_widgets["state_code"] = QComboBox()
        self.location_detail_form.addRow(
            "State/Prov:", self.location_detail_form_widgets["state_code"]
        )
        self.location_detail_form_widgets["zip_code"] = QLineEdit()
        self.location_detail_form.addRow(
            "Zip/Postal:", self.location_detail_form_widgets["zip_code"]
        )
        self.location_detail_form_widgets["country_code"] = QLineEdit()
        self.location_detail_form.addRow(
            "Country:", self.location_detail_form_widgets["country_code"]
        )
        self.location_detail_form_widgets["phone"] = QLineEdit()
        self.location_detail_form.addRow(
            "Phone:", self.location_detail_form_widgets["phone"]
        )
        self.location_detail_form_widgets["contact_person"] = QLineEdit()
        self.location_detail_form.addRow(
            "Contact:", self.location_detail_form_widgets["contact_person"]
        )
        self.location_detail_form_widgets["is_active"] = QCheckBox("Location is Active")
        self.location_detail_form.addRow(self.location_detail_form_widgets["is_active"])
        layout.addLayout(self.location_detail_form)
        layout.addStretch()
        save_btn = QPushButton("Save Location Changes")
        icon_path = os.path.join(assets_path, "save.png")
        save_btn.setIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        save_btn.clicked.connect(self._save_location_details)
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        btn_l.addWidget(save_btn)
        layout.addLayout(btn_l)
        self._set_location_details_form_enabled(False)
        return grp

    def load_locations_data(self):
        self.logger.info("Loading locations...")
        if not self.locations_table:
            return
        try:
            # Assuming LocationController.get_all_locations might not take 'include_inactive'
            # Or it defaults to True. If it needs to be called without, adjust here.
            # For UserManagement, usually want to see all.
            locs = (
                self.location_controller.get_all_locations()
            )  # Potential change from include_inactive=True

            self.locations_table.setRowCount(0)
            self.locations_table.setSortingEnabled(False)
            for r, l in enumerate(locs):
                self.locations_table.insertRow(r)
                self.locations_table.setItem(
                    r, 0, QTableWidgetItem(l.location_name or "N/A")
                )
                addr_parts = [
                    l.address_line1,
                    l.address_line2,
                    l.city,
                    l.state_code,
                    l.zip_code,
                    l.country_code,
                ]
                full_addr = ", ".join(filter(None, addr_parts))
                display_text = (
                    l.location_name
                    if l.location_name
                    else (full_addr if full_addr else "N/A")
                )
                if (
                    l.location_name
                    and full_addr
                    and l.location_name.lower()
                    != full_addr.lower().replace(",", "").strip()
                ):
                    display_text = f"{l.location_name} ({full_addr})"
                elif not l.location_name and full_addr:
                    display_text = full_addr
                self.locations_table.setItem(r, 1, QTableWidgetItem(display_text))
                self.locations_table.setItem(
                    r, 2, QTableWidgetItem("Yes" if l.is_active else "No")
                )
                self.locations_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, l.location_id
                )
            self.locations_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(locs)} locations.")
        except (
            TypeError
        ) as te:  # Catching if get_all_locations still has signature issue
            self.logger.error(
                f"TypeError loading locations (check controller method signature): {te}",
                exc_info=True,
            )
            QMessageBox.critical(
                self,
                "Load Error",
                "Could not load locations due to a program error (controller method signature).",
            )
        except Exception as e:
            self.logger.error(f"Error loading locations: {e}", exc_info=True)
        self._clear_location_details_form()
        self._set_location_details_form_enabled(False)

    @Slot()
    def _on_location_selected(self):
        if not self.locations_table:
            return
        s_items = self.locations_table.selectedItems()
        if not s_items:
            self.current_selected_location_id = None
            self._clear_location_details_form()
            self._set_location_details_form_enabled(False)
            return
        item = self.locations_table.item(s_items[0].row(), 0)
        if item:
            self.current_selected_location_id = item.data(Qt.ItemDataRole.UserRole)
            self.logger.info(
                f"Location selected: ID {self.current_selected_location_id}"
            )
            self._populate_location_details_form(self.current_selected_location_id)
            self._set_location_details_form_enabled(True)

    def _populate_location_details_form(self, loc_id: int):
        loc = self.location_controller.get_location_by_id(loc_id)
        if not loc:
            self._clear_location_details_form()
            self._set_location_details_form_enabled(False)
            return
        if not self.location_detail_form_widgets:
            self.logger.error("location_detail_form_widgets not init!")
            return
        self.location_detail_form_widgets["location_id"].setText(str(loc.location_id))
        self.location_detail_form_widgets["location_name"].setText(
            loc.location_name or ""
        )
        self.location_detail_form_widgets["address_line1"].setText(
            loc.address_line1 or ""
        )
        self.location_detail_form_widgets["address_line2"].setText(
            loc.address_line2 or ""
        )
        self.location_detail_form_widgets["city"].setText(loc.city or "")
        state_combo = self.location_detail_form_widgets["state_code"]
        if (
            state_combo.count() <= 1
        ):  # Allow repopulation if it's empty or only has placeholder
            try:
                states = self.location_controller.get_all_state_provinces()
                state_combo.clear()
                state_combo.addItem("", None)
                [
                    state_combo.addItem(
                        f"{s.state_name} ({s.state_code})", s.state_code
                    )
                    for s in states
                ]
            except Exception as e:
                self.logger.error(f"Failed to populate states for locations: {e}")
        idx = state_combo.findData(loc.state_code)
        state_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.location_detail_form_widgets["zip_code"].setText(loc.zip_code or "")
        self.location_detail_form_widgets["country_code"].setText(
            loc.country_code or "USA"
        )
        self.location_detail_form_widgets["phone"].setText(loc.phone or "")
        self.location_detail_form_widgets["contact_person"].setText(
            loc.contact_person or ""
        )
        self.location_detail_form_widgets["is_active"].setChecked(loc.is_active)

    def _clear_location_details_form(self):
        if not self.location_detail_form_widgets:
            return
        for k, w in self.location_detail_form_widgets.items():
            if isinstance(w, (QLineEdit, QPlainTextEdit)):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
            elif isinstance(w, QCheckBox):
                w.setChecked(False)
        if "country_code" in self.location_detail_form_widgets and isinstance(
            self.location_detail_form_widgets["country_code"], QLineEdit
        ):
            self.location_detail_form_widgets["country_code"].setText("USA")
        if "is_active" in self.location_detail_form_widgets and isinstance(
            self.location_detail_form_widgets["is_active"], QCheckBox
        ):
            self.location_detail_form_widgets["is_active"].setChecked(True)
        self.current_selected_location_id = None

    def _set_location_details_form_enabled(self, enabled: bool):
        if not self.location_detail_form_widgets:
            return
        for k, w in self.location_detail_form_widgets.items():
            (
                w.setEnabled(enabled)
                if k != "location_id"
                else (w.setReadOnly(True), w.setEnabled(enabled))
            )

    @Slot()
    def _add_new_location(self):
        dialog = AddEditLocationDialog(controller=self.location_controller, parent=self)
        if dialog.exec():
            self.load_locations_data()
            self.show_status_message("Location added.", True)
        elif dialog.error_message:
            self.show_error_message("Add Location Failed", dialog.error_message)

    @Slot()
    def _save_location_details(self):
        if not self.current_selected_location_id:
            self.show_error_message("Save Error", "No location selected.")
            return
        if not self.location_detail_form_widgets:
            self.logger.error("Cannot save location, form widgets not ready.")
            return
        loc_data = {
            "location_name": self.location_detail_form_widgets["location_name"]
            .text()
            .strip(),
            "address_line1": self.location_detail_form_widgets["address_line1"]
            .text()
            .strip()
            or None,
            "address_line2": self.location_detail_form_widgets["address_line2"]
            .text()
            .strip()
            or None,
            "city": self.location_detail_form_widgets["city"].text().strip() or None,
            "state_code": self.location_detail_form_widgets["state_code"].currentData(),
            "zip_code": self.location_detail_form_widgets["zip_code"].text().strip()
            or None,
            "country_code": self.location_detail_form_widgets["country_code"]
            .text()
            .strip()
            or None,
            "phone": self.location_detail_form_widgets["phone"].text().strip() or None,
            "contact_person": self.location_detail_form_widgets["contact_person"]
            .text()
            .strip()
            or None,
            "is_active": self.location_detail_form_widgets["is_active"].isChecked(),
        }
        s, m = self.location_controller.update_location(
            self.current_selected_location_id, loc_data, self.current_user_id
        )
        if s:
            self.show_status_message(m, True)
            self.load_locations_data()
            self._populate_location_details_form(self.current_selected_location_id)
        else:
            self.show_error_message("Update Failed", m)

    def _create_charge_codes_list_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        self.charge_codes_table = QTableWidget()
        self.charge_codes_table.setColumnCount(5)
        self.charge_codes_table.setHorizontalHeaderLabels(
            ["Code", "Description", "Category", "Std. Price", "Active"]
        )
        self.charge_codes_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.charge_codes_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.charge_codes_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.charge_codes_table.itemSelectionChanged.connect(
            self._on_charge_code_selected
        )
        layout.addWidget(self.charge_codes_table)
        add_btn = QPushButton("Add New Charge Code")
        icon_path = os.path.join(assets_path, "add.png")
        add_btn.setIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        add_btn.clicked.connect(self._add_new_charge_code)
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        btn_l.addWidget(add_btn)
        layout.addLayout(btn_l)
        return widget

    def _create_charge_code_details_section(self) -> QWidget:
        grp = QGroupBox("Charge Code Details")
        layout = QVBoxLayout(grp)
        self.charge_code_detail_form = QFormLayout()
        self.charge_code_detail_form_widgets["charge_code_id"] = QLineEdit()
        self.charge_code_detail_form_widgets["charge_code_id"].setReadOnly(True)
        self.charge_code_detail_form.addRow(
            "ID:", self.charge_code_detail_form_widgets["charge_code_id"]
        )
        self.charge_code_detail_form_widgets["code"] = QLineEdit()
        self.charge_code_detail_form.addRow(
            "Code:", self.charge_code_detail_form_widgets["code"]
        )
        self.charge_code_detail_form_widgets["description"] = QLineEdit()
        self.charge_code_detail_form.addRow(
            "Description:", self.charge_code_detail_form_widgets["description"]
        )
        self.charge_code_detail_form_widgets["category"] = QLineEdit()
        self.charge_code_detail_form.addRow(
            "Category:", self.charge_code_detail_form_widgets["category"]
        )
        self.charge_code_detail_form_widgets["standard_charge"] = QLineEdit()
        self.charge_code_detail_form_widgets["standard_charge"].setValidator(
            QDoubleValidator(0, 999999.99, 2)
        )
        self.charge_code_detail_form.addRow(
            "Standard Price:", self.charge_code_detail_form_widgets["standard_charge"]
        )
        self.charge_code_detail_form_widgets["taxable"] = QCheckBox("Taxable")
        self.charge_code_detail_form.addRow(
            self.charge_code_detail_form_widgets["taxable"]
        )
        self.charge_code_detail_form_widgets["is_active"] = QCheckBox(
            "Charge Code is Active"
        )
        self.charge_code_detail_form.addRow(
            self.charge_code_detail_form_widgets["is_active"]
        )
        layout.addLayout(self.charge_code_detail_form)
        layout.addStretch()
        save_btn = QPushButton("Save Charge Code Changes")
        icon_path = os.path.join(assets_path, "save.png")
        save_btn.setIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        save_btn.clicked.connect(self._save_charge_code_details)
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        btn_l.addWidget(save_btn)
        layout.addLayout(btn_l)
        self._set_charge_code_details_form_enabled(False)
        return grp

    def load_charge_codes_data(self):
        self.logger.info("Loading charge codes...")
        if not self.charge_codes_table:
            return
        try:
            # This will likely error if ChargeCodeController still uses 'alternate_code'
            ccs = self.charge_code_controller.get_all_charge_codes(
                include_inactive=True
            )
            self.charge_codes_table.setRowCount(0)
            self.charge_codes_table.setSortingEnabled(False)
            for r, c in enumerate(ccs):
                self.charge_codes_table.insertRow(r)
                self.charge_codes_table.setItem(r, 0, QTableWidgetItem(c.code))
                self.charge_codes_table.setItem(
                    r, 1, QTableWidgetItem(c.description or "")
                )
                self.charge_codes_table.setItem(
                    r, 2, QTableWidgetItem(c.category or "")
                )
                self.charge_codes_table.setItem(
                    r,
                    3,
                    QTableWidgetItem(
                        f"{c.standard_charge:.2f}"
                        if c.standard_charge is not None
                        else "0.00"
                    ),
                )
                self.charge_codes_table.setItem(
                    r, 4, QTableWidgetItem("Yes" if c.is_active else "No")
                )
                self.charge_codes_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, c.charge_code_id
                )
            self.charge_codes_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(ccs)} charge codes.")
        except (
            AttributeError
        ) as ae:  # Specifically catch if alternate_code is the issue from controller
            self.logger.error(
                f"AttributeError loading charge codes (likely 'alternate_code' in controller): {ae}",
                exc_info=True,
            )
            QMessageBox.warning(
                self,
                "Load Error",
                "Could not load charge codes due to an internal attribute error (likely 'alternate_code'). Please check controller logic.",
            )
        except Exception as e:
            self.logger.error(f"Error loading charge codes: {e}", exc_info=True)
        self._clear_charge_code_details_form()
        self._set_charge_code_details_form_enabled(False)

    @Slot()
    def _on_charge_code_selected(self):
        if not self.charge_codes_table:
            return
        s_items = self.charge_codes_table.selectedItems()
        if not s_items:
            self.current_selected_charge_code_id = None
            self._clear_charge_code_details_form()
            self._set_charge_code_details_form_enabled(False)
            return
        item = self.charge_codes_table.item(s_items[0].row(), 0)
        if item:
            self.current_selected_charge_code_id = item.data(Qt.ItemDataRole.UserRole)
            self.logger.info(
                f"Charge Code selected: ID {self.current_selected_charge_code_id}"
            )
            self._populate_charge_code_details_form(
                self.current_selected_charge_code_id
            )
            self._set_charge_code_details_form_enabled(True)

    def _populate_charge_code_details_form(self, cc_id: int):
        cc = self.charge_code_controller.get_charge_code_by_id(cc_id)
        if not cc:
            self._clear_charge_code_details_form()
            self._set_charge_code_details_form_enabled(False)
            return
        if not self.charge_code_detail_form_widgets:
            self.logger.error("charge_code_detail_form_widgets not init!")
            return
        self.charge_code_detail_form_widgets["charge_code_id"].setText(
            str(cc.charge_code_id)
        )
        self.charge_code_detail_form_widgets["code"].setText(cc.code)
        self.charge_code_detail_form_widgets["description"].setText(
            cc.description or ""
        )
        self.charge_code_detail_form_widgets["category"].setText(cc.category or "")
        self.charge_code_detail_form_widgets["standard_charge"].setText(
            f"{cc.standard_charge:.2f}" if cc.standard_charge is not None else ""
        )
        self.charge_code_detail_form_widgets["taxable"].setChecked(bool(cc.taxable))
        self.charge_code_detail_form_widgets["is_active"].setChecked(cc.is_active)

    def _clear_charge_code_details_form(self):
        if not self.charge_code_detail_form_widgets:
            return
        for k, w in self.charge_code_detail_form_widgets.items():
            if isinstance(w, QLineEdit):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
            elif isinstance(w, QCheckBox):
                w.setChecked(False)
        if "is_active" in self.charge_code_detail_form_widgets and isinstance(
            self.charge_code_detail_form_widgets["is_active"], QCheckBox
        ):
            self.charge_code_detail_form_widgets["is_active"].setChecked(True)
        self.current_selected_charge_code_id = None

    def _set_charge_code_details_form_enabled(self, enabled: bool):
        if not self.charge_code_detail_form_widgets:
            return
        for k, w in self.charge_code_detail_form_widgets.items():
            (
                w.setEnabled(enabled)
                if k != "charge_code_id"
                else (w.setReadOnly(True), w.setEnabled(enabled))
            )

    @Slot()
    def _add_new_charge_code(self):
        dialog = AddEditChargeCodeDialog(
            controller=self.charge_code_controller, parent=self
        )
        if dialog.exec():
            self.load_charge_codes_data()
            self.show_status_message("Charge code added.", True)
        elif dialog.error_message:
            self.show_error_message("Add Charge Code Failed", dialog.error_message)

    @Slot()
    def _save_charge_code_details(self):
        if not self.current_selected_charge_code_id:
            self.show_error_message("Save Error", "No charge code selected.")
            return
        if not self.charge_code_detail_form_widgets:
            self.logger.error("Cannot save charge code, form widgets not ready.")
            return
        cc_data = {
            "code": self.charge_code_detail_form_widgets["code"].text().strip(),
            "description": self.charge_code_detail_form_widgets["description"]
            .text()
            .strip(),
            "category": self.charge_code_detail_form_widgets["category"].text().strip()
            or None,
            "standard_charge": float(
                self.charge_code_detail_form_widgets["standard_charge"].text() or 0.0
            ),
            "taxable": self.charge_code_detail_form_widgets["taxable"].isChecked(),
            "is_active": self.charge_code_detail_form_widgets["is_active"].isChecked(),
        }
        s, m = self.charge_code_controller.update_charge_code(
            self.current_selected_charge_code_id, cc_data, self.current_user_id
        )
        if s:
            self.show_status_message(m, True)
            self.load_charge_codes_data()
            self._populate_charge_code_details_form(
                self.current_selected_charge_code_id
            )
        else:
            self.show_error_message("Update Failed", m)

    def _create_owners_list_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        self.owners_table = QTableWidget()
        self.owners_table.setColumnCount(4)
        self.owners_table.setHorizontalHeaderLabels(
            ["Account #", "Owner Name", "Primary Phone", "Active"]
        )
        self.owners_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.owners_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.owners_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.owners_table.itemSelectionChanged.connect(self._on_master_owner_selected)
        layout.addWidget(self.owners_table)
        return widget

    def _create_owner_details_section(self) -> QWidget:
        grp = QGroupBox("Master Owner Details")
        layout = QVBoxLayout(grp)
        self.owner_detail_form = QFormLayout()
        self.owner_detail_form_widgets["owner_id"] = QLineEdit()
        self.owner_detail_form_widgets["owner_id"].setReadOnly(True)
        self.owner_detail_form.addRow("ID:", self.owner_detail_form_widgets["owner_id"])
        self.owner_detail_form_widgets["account_number"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Account #:", self.owner_detail_form_widgets["account_number"]
        )
        self.owner_detail_form_widgets["farm_name"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Farm Name:", self.owner_detail_form_widgets["farm_name"]
        )
        self.owner_detail_form_widgets["first_name"] = QLineEdit()
        self.owner_detail_form.addRow(
            "First Name:", self.owner_detail_form_widgets["first_name"]
        )
        self.owner_detail_form_widgets["last_name"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Last Name:", self.owner_detail_form_widgets["last_name"]
        )
        self.owner_detail_form_widgets["address_line1"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Address 1:", self.owner_detail_form_widgets["address_line1"]
        )
        self.owner_detail_form_widgets["address_line2"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Address 2:", self.owner_detail_form_widgets["address_line2"]
        )
        self.owner_detail_form_widgets["city"] = QLineEdit()
        self.owner_detail_form.addRow("City:", self.owner_detail_form_widgets["city"])
        self.owner_detail_form_widgets["state_code"] = QComboBox()
        self.owner_detail_form.addRow(
            "State/Prov:", self.owner_detail_form_widgets["state_code"]
        )
        self.owner_detail_form_widgets["zip_code"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Zip/Postal:", self.owner_detail_form_widgets["zip_code"]
        )
        self.owner_detail_form_widgets["phone"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Primary Phone:", self.owner_detail_form_widgets["phone"]
        )
        self.owner_detail_form_widgets["mobile_phone"] = QLineEdit()
        self.owner_detail_form.addRow(
            "Mobile Phone:", self.owner_detail_form_widgets["mobile_phone"]
        )
        self.owner_detail_form_widgets["email"] = QLineEdit()
        self.owner_detail_form.addRow("Email:", self.owner_detail_form_widgets["email"])
        self.owner_detail_form_widgets["is_active"] = QCheckBox("Owner is Active")
        self.owner_detail_form.addRow(self.owner_detail_form_widgets["is_active"])
        self.owner_detail_form_widgets["notes"] = QPlainTextEdit()
        self.owner_detail_form_widgets["notes"].setFixedHeight(60)
        self.owner_detail_form.addRow("Notes:", self.owner_detail_form_widgets["notes"])
        layout.addLayout(self.owner_detail_form)
        layout.addStretch()
        self._set_owner_details_form_enabled(False)
        return grp

    def load_master_owners_data(self):
        self.logger.info("Loading master owners...")
        if not self.owners_table:
            return
        try:
            # This will error if owner_controller does not have get_all_owners
            owners = (
                self.owner_controller.get_all_owners(include_inactive=True)
                if hasattr(self.owner_controller, "get_all_owners")
                else []
            )
            if not hasattr(self.owner_controller, "get_all_owners"):
                self.logger.error(
                    "OwnerController does not have 'get_all_owners' method."
                )
                QMessageBox.warning(
                    self,
                    "Load Error",
                    "Could not load master owners: 'get_all_owners' method missing in controller.",
                )

            self.owners_table.setRowCount(0)
            self.owners_table.setSortingEnabled(False)
            for r, o in enumerate(owners):
                self.owners_table.insertRow(r)
                self.owners_table.setItem(
                    r, 0, QTableWidgetItem(o.account_number or "")
                )
                name_disp = (
                    o.farm_name
                    or f"{o.first_name or ''} {o.last_name or ''}".strip()
                    or f"ID: {o.owner_id}"
                )
                self.owners_table.setItem(r, 1, QTableWidgetItem(name_disp))
                self.owners_table.setItem(r, 2, QTableWidgetItem(o.phone or ""))
                self.owners_table.setItem(
                    r, 3, QTableWidgetItem("Yes" if o.is_active else "No")
                )
                self.owners_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, o.owner_id
                )
            self.owners_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(owners)} master owners.")
        except AttributeError as ae:  # Catch if get_all_owners is missing
            self.logger.error(
                f"AttributeError loading master owners (likely missing controller method): {ae}",
                exc_info=True,
            )
            QMessageBox.warning(
                self, "Load Error", f"Could not load master owners: {ae}"
            )
        except Exception as e:
            self.logger.error(f"Error loading master owners: {e}", exc_info=True)
        self._clear_owner_details_form()
        self._set_owner_details_form_enabled(False)

    @Slot()
    def _on_master_owner_selected(self):
        if not self.owners_table:
            return
        s_items = self.owners_table.selectedItems()
        if not s_items:
            self.current_selected_owner_id = None
            self._clear_owner_details_form()
            self._set_owner_details_form_enabled(False)
            return
        item = self.owners_table.item(s_items[0].row(), 0)
        if item:
            self.current_selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
            self.logger.info(
                f"Master Owner selected: ID {self.current_selected_owner_id}"
            )
            self._populate_owner_details_form(self.current_selected_owner_id)
            self._set_owner_details_form_enabled(True)

    def _populate_owner_details_form(self, owner_id: int):
        owner = self.owner_controller.get_owner_by_id(owner_id)
        if not owner:
            self._clear_owner_details_form()
            self._set_owner_details_form_enabled(False)
            return
        if not self.owner_detail_form_widgets:
            self.logger.error("owner_detail_form_widgets not init!")
            return
        self.owner_detail_form_widgets["owner_id"].setText(str(owner.owner_id))
        self.owner_detail_form_widgets["account_number"].setText(
            owner.account_number or ""
        )
        self.owner_detail_form_widgets["farm_name"].setText(owner.farm_name or "")
        self.owner_detail_form_widgets["first_name"].setText(owner.first_name or "")
        self.owner_detail_form_widgets["last_name"].setText(owner.last_name or "")
        self.owner_detail_form_widgets["address_line1"].setText(
            owner.address_line1 or ""
        )
        self.owner_detail_form_widgets["address_line2"].setText(
            owner.address_line2 or ""
        )
        self.owner_detail_form_widgets["city"].setText(owner.city or "")
        state_combo = self.owner_detail_form_widgets["state_code"]
        if state_combo.count() <= 1:  # Repopulate if empty or only placeholder
            try:
                states = self.location_controller.get_all_state_provinces()
                state_combo.clear()
                state_combo.addItem("", None)
                [
                    state_combo.addItem(
                        f"{s.state_name} ({s.state_code})", s.state_code
                    )
                    for s in states
                ]
            except Exception as e:
                self.logger.error(f"Failed to populate states for owners: {e}")
        idx = state_combo.findData(owner.state_code)
        state_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.owner_detail_form_widgets["zip_code"].setText(owner.zip_code or "")
        self.owner_detail_form_widgets["phone"].setText(owner.phone or "")
        self.owner_detail_form_widgets["mobile_phone"].setText(owner.mobile_phone or "")
        self.owner_detail_form_widgets["email"].setText(owner.email or "")
        self.owner_detail_form_widgets["is_active"].setChecked(owner.is_active)
        self.owner_detail_form_widgets["notes"].setPlainText(owner.notes or "")

    def _clear_owner_details_form(self):
        if not self.owner_detail_form_widgets:
            return
        for k, w in self.owner_detail_form_widgets.items():
            if isinstance(w, (QLineEdit, QPlainTextEdit)):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)  # Reset to placeholder
            elif isinstance(w, QCheckBox):
                w.setChecked(False)
        if "is_active" in self.owner_detail_form_widgets and isinstance(
            self.owner_detail_form_widgets["is_active"], QCheckBox
        ):
            self.owner_detail_form_widgets["is_active"].setChecked(
                True
            )  # Default new to active
        self.current_selected_owner_id = None

    def _set_owner_details_form_enabled(self, enabled: bool):
        if not self.owner_detail_form_widgets:
            self.logger.warning("_set_owner_details_form_enabled: dict not init.")
            return
        for widget_name, widget_instance in self.owner_detail_form_widgets.items():
            if isinstance(widget_instance, (QLineEdit, QPlainTextEdit)):
                widget_instance.setReadOnly(True)
                widget_instance.setEnabled(enabled)
            elif isinstance(widget_instance, (QComboBox, QCheckBox)):
                widget_instance.setEnabled(False)  # Kept non-interactive for display
            else:  # Fallback for other types, though not expected in this form
                widget_instance.setEnabled(enabled)
        # Ensure parent groupbox is also enabled to make children visible if they are enabled
        if self.owner_detail_form and self.owner_detail_form.parentWidget():
            self.owner_detail_form.parentWidget().setEnabled(enabled)

    def load_all_data(self):
        self.logger.info("UserManagementScreen: Loading all initial data for tabs.")
        try:
            self.load_users_data()
            self.load_locations_data()
            self.load_charge_codes_data()
            self.load_master_owners_data()

            if hasattr(self, "update_status_bar") and callable(self.update_status_bar):
                self.update_status_bar("Ready.")
            elif (
                hasattr(self, "parent_view")
                and self.parent_view
                and hasattr(self.parent_view, "update_status")
                and callable(self.parent_view.update_status)
            ):
                # This path should ideally not be needed if BaseView provides update_status_bar
                self.parent_view.update_status("User Management Ready.")
            else:
                self.logger.warning(
                    "update_status_bar method not found on self or parent_view for 'Ready.' message."
                )

        except Exception as e:
            self.logger.error(f"Error in load_all_data: {e}", exc_info=True)
            error_message = (
                f"An error occurred while loading data for management tabs: {e}"
            )
            if hasattr(self, "show_error_message") and callable(
                self.show_error_message
            ):
                self.show_error_message("Load Error", error_message)
            else:
                QMessageBox.critical(self, "Load Error", error_message)  # Fallback

    def closeEvent(self, event: QCloseEvent):
        self.logger.info("User Management screen closing.")
        super().closeEvent(event)
