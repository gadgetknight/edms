# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.12.5
Purpose: Provides a tabbed UI for managing users, locations, charge codes, and master owners.
         Corrected TypeError for AddEditUserDialog instantiation.
Last Updated: May 27, 2025
Author: Gemini (based on user's v1.12.4)

Changelog:
- v1.12.5 (2025-05-27):
    - Functional Fix: Corrected `AddEditUserDialog` instantiation in `_add_new_user`
      and `_edit_selected_user` to pass `parent_view` (as the first positional argument
      for the parent widget) and `user_controller`. For edit mode, `current_user_object`
      is passed instead of `user`. Removed `current_user_id` from the call as it's not
      an explicit __init__ parameter for the provided AddEditUserDialog v1.0.0.
      This resolves `TypeError: AddEditUserDialog.__init__() got an unexpected keyword argument 'parent'`.
- v1.12.4 (User Provided Baseline):
    - Docstring version set to 1.12.4. Assumed to contain fixes from v1.12.3 (conceptual).
- v1.12.3 (Conceptual - Contained the NameError fix for DARK_PRIMARY_ACTION):
    - Functional Fix: Ensured `QColor` is imported from `PySide6.QtGui`.
    - Functional Fix: Ensured all necessary color constants from `config.app_config`
      are correctly imported and accessible within stylesheet f-strings.
- v1.12.2 (2025-05-27 - Produced DARK_PRIMARY_ACTION NameError):
    - User Management Tab UI Refinement:
        - Removed the search input, roles filter, and status filter elements from this tab's layout.
        - Changed the user list from QTableWidget to QListWidget (`users_list_widget`).
        - Implemented `UserListItemWidget` for a custom row display.
- v1.11.0 (2025-05-27):
    - Major UI Refactor: Main layout to QTabWidget.
- v1.10.12 (2025-05-26) (User's original baseline from commit 4bf96c1):
    - Original structure.
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
    QHeaderView,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QCloseEvent, QColor

from views.base_view import BaseView
from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.charge_code_controller import ChargeCodeController
from controllers.owner_controller import OwnerController

from models import User as UserModel
from models import Location as LocationModel
from models import ChargeCode as ChargeCodeModel
from models import Owner as OwnerModel

from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog

from config.app_config import (
    DARK_SUCCESS_ACTION,
    DARK_DANGER_ACTION,
    DARK_BUTTON_BG,
    DARK_TEXT_PRIMARY,
    DARK_BORDER,
    DARK_BUTTON_HOVER,
    DARK_HEADER_FOOTER,
    DARK_TEXT_TERTIARY,
    DARK_TEXT_SECONDARY,
    DARK_WIDGET_BACKGROUND,
    DARK_PRIMARY_ACTION,
)

import os

try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_path, "..", ".."))
    assets_path = os.path.join(project_root, "assets", "icons")
except Exception:
    assets_path = "assets/icons"


class UserListItemWidget(QWidget):
    def __init__(self, user_model: UserModel, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)

        label_style = (
            f"color: {DARK_TEXT_SECONDARY}; padding-top: 2px; font-size: 11px;"
        )
        value_box_style = (
            f"background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; padding: 4px 6px; border-radius: 3px; "
            f"font-size: 11px; min-height: 18px;"
        )

        id_label_widget = QLabel("User ID:")
        id_label_widget.setStyleSheet(label_style)
        id_label_widget.setFixedWidth(65)
        self.id_value_label = QLabel(user_model.user_id)
        self.id_value_label.setStyleSheet(value_box_style)
        self.id_value_label.setMinimumWidth(100)

        name_label_widget = QLabel("User Name:")
        name_label_widget.setStyleSheet(label_style)
        name_label_widget.setFixedWidth(85)
        self.name_value_label = QLabel(user_model.user_name or "N/A")
        self.name_value_label.setStyleSheet(value_box_style)

        layout.addWidget(id_label_widget)
        layout.addWidget(self.id_value_label)
        layout.addSpacing(20)
        layout.addWidget(name_label_widget)
        layout.addWidget(self.name_value_label, 1)
        self.setMinimumHeight(
            max(
                self.id_value_label.sizeHint().height(),
                self.name_value_label.sizeHint().height(),
                28,
            )
            + 6
        )


class UserManagementScreen(BaseView):
    horse_management_requested = Signal()
    main_tab_widget: Optional[QTabWidget]

    users_list_widget: Optional[QListWidget]
    add_user_button: Optional[QPushButton]
    edit_user_button: Optional[QPushButton]
    delete_user_button: Optional[QPushButton]
    current_selected_user_id: Optional[str] = None

    locations_table: Optional[QTableWidget]
    add_location_button: Optional[QPushButton]
    edit_location_button: Optional[QPushButton]
    delete_location_button: Optional[QPushButton]
    current_selected_location_id: Optional[int] = None

    charge_codes_table: Optional[QTableWidget]
    add_charge_code_button: Optional[QPushButton]
    edit_charge_code_button: Optional[QPushButton]
    delete_charge_code_button: Optional[QPushButton]
    current_selected_charge_code_id: Optional[int] = None

    owners_table: Optional[QTableWidget]
    add_owner_button: Optional[QPushButton]
    edit_owner_button: Optional[QPushButton]
    delete_owner_button: Optional[QPushButton]
    current_selected_owner_id: Optional[int] = None

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        self.main_tab_widget = None
        self.users_list_widget = None
        self.add_user_button, self.edit_user_button, self.delete_user_button = (
            None,
            None,
            None,
        )
        self.locations_table = None
        (
            self.add_location_button,
            self.edit_location_button,
            self.delete_location_button,
        ) = (None, None, None)
        self.charge_codes_table = None
        (
            self.add_charge_code_button,
            self.edit_charge_code_button,
            self.delete_charge_code_button,
        ) = (None, None, None)
        self.owners_table = None
        self.add_owner_button, self.edit_owner_button, self.delete_owner_button = (
            None,
            None,
            None,
        )

        super().__init__(parent)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = (
            current_user_id  # This is the ID of the admin using this screen
        )
        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.charge_code_controller = ChargeCodeController()
        self.owner_controller = OwnerController()

        self.setWindowTitle("User & System Management")
        self.load_all_data()
        self.logger.info(
            f"UserManagementScreen (v1.12.5) initialized for user: {self.current_user_id}"
        )

    def _get_crud_button_style(
        self, button_type="default", is_add_button_specific_style=False
    ) -> str:
        base_style = f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;"
        if is_add_button_specific_style:
            bg_color = DARK_SUCCESS_ACTION
            text_color = "white"
            border_color = DARK_SUCCESS_ACTION
        elif button_type == "delete":
            bg_color = DARK_DANGER_ACTION
            text_color = "white"
            border_color = DARK_DANGER_ACTION
        else:
            bg_color = DARK_BUTTON_BG
            text_color = DARK_TEXT_PRIMARY
            border_color = DARK_BORDER

        return f"""
            QPushButton {{
                background-color: {bg_color}; color: {text_color}; border: 1px solid {border_color};
                border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {QColor(bg_color).lighter(115).name()}; }}
            QPushButton:pressed {{ background-color: {QColor(bg_color).darker(110).name()}; }}
            QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}
        """

    def setup_ui(self):
        self.logger.info(
            "****** UserManagementScreen.setup_ui() (v1.12.5) ENTERED ******"
        )
        container_layout = getattr(
            self, "main_content_layout", QVBoxLayout(self.central_widget)
        )
        if not hasattr(self, "main_content_layout"):
            self.central_widget.setLayout(container_layout)
        while container_layout.count():
            item = container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND};
                border-top-left-radius: 0px; border-top-right-radius: 6px;
                border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY};
                border: 1px solid {DARK_BORDER}; border-bottom: none; 
                padding: 8px 20px; margin-right: 1px;
                border-top-left-radius: 5px; border-top-right-radius: 5px; min-width: 150px;
            }}
            QTabBar::tab:selected {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border-bottom: 1px solid {DARK_WIDGET_BACKGROUND}; 
            }}
            QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
        """
        )

        user_management_tab = self._create_user_management_tab()
        self.main_tab_widget.addTab(user_management_tab, "👤 User Management")
        locations_tab = self._create_locations_tab()
        self.main_tab_widget.addTab(locations_tab, "📍 Manage Locations")
        charge_codes_tab = self._create_charge_codes_tab()
        self.main_tab_widget.addTab(charge_codes_tab, "💲 Manage Charge Codes")
        owners_tab = self._create_owners_tab()
        self.main_tab_widget.addTab(owners_tab, "👥 Master Owner List")

        container_layout.addWidget(self.main_tab_widget)
        self.main_tab_widget.currentChanged.connect(self._on_tab_changed)
        self.logger.info("UserManagementScreen.setup_ui (v1.12.5) FINISHED.")

    def _on_tab_changed(self, index: int):
        self.logger.info(f"Tab changed to index: {index}")
        self.current_selected_user_id = None
        self.current_selected_location_id = None
        self.current_selected_charge_code_id = None
        self.current_selected_owner_id = None

        if self.users_list_widget and index != 0:
            self.users_list_widget.clearSelection()
        if self.locations_table and index != 1:
            self.locations_table.clearSelection()
        if self.charge_codes_table and index != 2:
            self.charge_codes_table.clearSelection()
        if self.owners_table and index != 3:
            self.owners_table.clearSelection()

        if index == 0:
            self.load_users_data()
        elif index == 1:
            self.load_locations_data()
        elif index == 2:
            self.load_charge_codes_data()
        elif index == 3:
            self.load_master_owners_data()
        self._update_crud_button_states()

    def _create_crud_button_panel(
        self,
        add_text: str,
        edit_text_base: str,
        delete_text_base: str,
        add_slot,
        edit_slot,
        delete_slot,
    ) -> (QHBoxLayout, QPushButton, QPushButton, QPushButton):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        add_button = QPushButton(add_text)
        is_user_add_btn = "User" in add_text
        add_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=is_user_add_btn)
        )
        add_button.clicked.connect(add_slot)

        edit_button = QPushButton(f"Edit Selected {edit_text_base}")
        edit_button.setStyleSheet(self._get_crud_button_style("default"))
        edit_button.clicked.connect(edit_slot)
        edit_button.setEnabled(False)

        delete_button = QPushButton(f"Delete Selected {delete_text_base}")
        delete_button.setStyleSheet(self._get_crud_button_style("delete"))
        delete_button.clicked.connect(delete_slot)
        delete_button.setEnabled(False)

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        return button_layout, add_button, edit_button, delete_button

    def _create_user_management_tab(self) -> QWidget:
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        (
            crud_buttons_layout,
            self.add_user_button,
            self.edit_user_button,
            self.delete_user_button,
        ) = self._create_crud_button_panel(
            "➕ Add New User",
            "User",
            "User",
            self._add_new_user,
            self._edit_selected_user,
            self._delete_selected_user,
        )
        main_layout.addLayout(crud_buttons_layout)

        current_users_label = QLabel("Current Users:")
        current_users_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 10px;"
        )
        main_layout.addWidget(current_users_label)

        self.users_list_widget = QListWidget()
        self.users_list_widget.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {DARK_BORDER}; 
                border-radius: 4px; 
                background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item {{
                border-bottom: 1px solid {DARK_HEADER_FOOTER}; 
                padding: 0px;
            }}
            QListWidget::item:selected {{
                background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()};
            }}
             QListWidget::item:selected:!active {{
                background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()};
                color: {DARK_TEXT_PRIMARY};
            }}
            QListWidget::item:selected:active {{
                background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()};
                color: {DARK_TEXT_PRIMARY};
            }}
        """
        )
        self.users_list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.users_list_widget.currentItemChanged.connect(self._on_user_selected)
        main_layout.addWidget(self.users_list_widget)
        return tab_widget

    def _create_locations_tab(self) -> QWidget:
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        (
            buttons_layout,
            self.add_location_button,
            self.edit_location_button,
            self.delete_location_button,
        ) = self._create_crud_button_panel(
            "➕ Add New Location",
            "Location",
            "Location",
            self._add_new_location,
            self._edit_selected_location,
            self._delete_selected_location,
        )
        self.add_location_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=True)
        )
        main_layout.addLayout(buttons_layout)
        current_items_label = QLabel("Managed Locations:")
        current_items_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 10px;"
        )
        main_layout.addWidget(current_items_label)
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
        main_layout.addWidget(self.locations_table)
        return tab_widget

    def _create_charge_codes_tab(self) -> QWidget:
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        (
            buttons_layout,
            self.add_charge_code_button,
            self.edit_charge_code_button,
            self.delete_charge_code_button,
        ) = self._create_crud_button_panel(
            "➕ Add New Charge Code",
            "Charge Code",
            "Charge Code",
            self._add_new_charge_code,
            self._edit_selected_charge_code,
            self._delete_selected_charge_code,
        )
        self.add_charge_code_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=True)
        )
        main_layout.addLayout(buttons_layout)
        current_items_label = QLabel("Managed Charge Codes:")
        current_items_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 10px;"
        )
        main_layout.addWidget(current_items_label)
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
        main_layout.addWidget(self.charge_codes_table)
        return tab_widget

    def _create_owners_tab(self) -> QWidget:
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        (
            buttons_layout,
            self.add_owner_button,
            self.edit_owner_button,
            self.delete_owner_button,
        ) = self._create_crud_button_panel(
            "➕ Add New Owner",
            "Owner",
            "Owner",
            self._add_new_owner,
            self._edit_selected_owner,
            self._delete_selected_owner,
        )
        self.add_owner_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=True)
        )
        main_layout.addLayout(buttons_layout)
        self.add_owner_button.setEnabled(False)
        self.edit_owner_button.setEnabled(False)
        current_items_label = QLabel("Master Owner List:")
        current_items_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 10px;"
        )
        main_layout.addWidget(current_items_label)
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
        main_layout.addWidget(self.owners_table)
        return tab_widget

    def _update_crud_button_states(self):
        current_tab_index = (
            self.main_tab_widget.currentIndex() if self.main_tab_widget else -1
        )
        user_selected = self.current_selected_user_id is not None
        location_selected = self.current_selected_location_id is not None
        charge_code_selected = self.current_selected_charge_code_id is not None
        owner_selected = self.current_selected_owner_id is not None

        if self.edit_user_button:
            self.edit_user_button.setEnabled(current_tab_index == 0 and user_selected)
        if self.delete_user_button:
            self.delete_user_button.setEnabled(current_tab_index == 0 and user_selected)
        if self.edit_location_button:
            self.edit_location_button.setEnabled(
                current_tab_index == 1 and location_selected
            )
        if self.delete_location_button:
            self.delete_location_button.setEnabled(
                current_tab_index == 1 and location_selected
            )
        if self.edit_charge_code_button:
            self.edit_charge_code_button.setEnabled(
                current_tab_index == 2 and charge_code_selected
            )
        if self.delete_charge_code_button:
            self.delete_charge_code_button.setEnabled(
                current_tab_index == 2 and charge_code_selected
            )
        if self.edit_owner_button:
            self.edit_owner_button.setEnabled(
                current_tab_index == 3 and owner_selected and False
            )
        if self.delete_owner_button:
            self.delete_owner_button.setEnabled(
                current_tab_index == 3 and owner_selected
            )

    def load_all_data(self):
        self.logger.info(
            "UserManagementScreen: Loading initial data for the first tab."
        )
        self._on_tab_changed(0)
        if hasattr(self, "update_status_bar") and callable(self.update_status_bar):
            self.update_status_bar("Ready.")
        elif (
            hasattr(self, "parent_view")
            and self.parent_view
            and hasattr(self.parent_view, "update_status")
            and callable(self.parent_view.update_status)
        ):
            self.parent_view.update_status("User Management Ready.")
        else:
            self.logger.warning(
                "update_status_bar method not found on self or parent_view."
            )

    def load_users_data(self):
        self.logger.info("Loading users data for User Management tab (custom list)...")
        if not self.users_list_widget:
            self.logger.warning("User list widget not ready.")
            return
        try:
            users = self.user_controller.get_all_users(include_inactive=True)
            self.users_list_widget.clear()
            for user in users:
                list_item = QListWidgetItem(self.users_list_widget)
                item_widget = UserListItemWidget(user, self.users_list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                list_item.setData(Qt.ItemDataRole.UserRole, user.user_id)
                self.users_list_widget.addItem(list_item)
                self.users_list_widget.setItemWidget(list_item, item_widget)
            self.logger.info(f"Loaded {len(users)} users into custom list.")
        except Exception as e:
            self.logger.error(
                f"Error loading user data into custom list: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Load Error", f"Could not load users: {e}")
        self.current_selected_user_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_user_selected(self):
        self.current_selected_user_id = None
        if self.users_list_widget and self.users_list_widget.currentItem():
            list_item = self.users_list_widget.currentItem()
            self.current_selected_user_id = list_item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"User selected from list: {self.current_selected_user_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_user(self):
        # Corrected: AddEditUserDialog (v1.0.0) expects parent_view, user_controller, current_user_object
        dialog = AddEditUserDialog(
            parent_view=self,
            user_controller=self.user_controller,
            # current_user_object is None for new user (default)
            # current_user_id (for who is performing action) is not taken by this dialog's __init__
        )
        if dialog.exec():
            self.load_users_data()
            self.show_status_message("User added successfully.", True)

    @Slot()
    def _edit_selected_user(self):
        if not self.current_selected_user_id:
            self.show_warning("Edit User", "Select user.")
            return
        user_to_edit = self.user_controller.get_user_by_login_id(
            self.current_selected_user_id
        )
        if not user_to_edit:
            self.show_error("Error", "User not found.")
            self.load_users_data()
            return
        # Corrected: AddEditUserDialog expects parent_view, user_controller, current_user_object
        dialog = AddEditUserDialog(
            parent_view=self,
            user_controller=self.user_controller,
            current_user_object=user_to_edit,
        )
        if dialog.exec():
            self.load_users_data()
            self.show_status_message(f"User '{user_to_edit.user_id}' updated.", True)
            self._try_reselect_item(
                self.users_list_widget, self.current_selected_user_id
            )

    def _try_reselect_item(self, list_or_table_widget, item_id_to_select):
        if not list_or_table_widget or item_id_to_select is None:
            self._update_crud_button_states()
            return
        found = False
        if isinstance(list_or_table_widget, QListWidget):
            for i in range(list_or_table_widget.count()):
                list_item = list_or_table_widget.item(i)
                if (
                    list_item
                    and list_item.data(Qt.ItemDataRole.UserRole) == item_id_to_select
                ):
                    list_or_table_widget.setCurrentItem(list_item)
                    if list_or_table_widget == self.users_list_widget:
                        self._on_user_selected()
                    found = True
                    break
        elif isinstance(list_or_table_widget, QTableWidget):
            for row in range(list_or_table_widget.rowCount()):
                item = list_or_table_widget.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == item_id_to_select:
                    list_or_table_widget.setCurrentCell(row, 0)
                    if list_or_table_widget == self.locations_table:
                        self._on_location_selected()
                    elif list_or_table_widget == self.charge_codes_table:
                        self._on_charge_code_selected()
                    elif list_or_table_widget == self.owners_table:
                        self._on_master_owner_selected()
                    found = True
                    break
        if not found:
            if hasattr(list_or_table_widget, "clearSelection"):
                list_or_table_widget.clearSelection()
            if list_or_table_widget == self.users_list_widget:
                self.current_selected_user_id = None
            elif list_or_table_widget == self.locations_table:
                self.current_selected_location_id = None
            elif list_or_table_widget == self.charge_codes_table:
                self.current_selected_charge_code_id = None
            elif list_or_table_widget == self.owners_table:
                self.current_selected_owner_id = None
        self._update_crud_button_states()

    @Slot()
    def _delete_selected_user(self):
        self._generic_delete_action(
            self.current_selected_user_id,
            "User",
            self.user_controller.delete_user_permanently,
            self.load_users_data,
            "current_selected_user_id",
            self.users_list_widget,
        )

    def load_locations_data(self):
        self.logger.info("Loading locations data for tab...")
        if not self.locations_table:
            self.logger.warning("Locations table not ready.")
            return
        try:
            locs = self.location_controller.get_all_locations(status_filter="all")
            self.locations_table.setRowCount(0)
            self.locations_table.setSortingEnabled(False)
            for r, l_obj in enumerate(locs):
                self.locations_table.insertRow(r)
                self.locations_table.setItem(
                    r, 0, QTableWidgetItem(l_obj.location_name or "N/A")
                )
                addr_parts = [
                    l_obj.address_line1,
                    l_obj.address_line2,
                    l_obj.city,
                    l_obj.state_code,
                    l_obj.zip_code,
                    l_obj.country_code,
                ]
                full_addr = ", ".join(filter(None, addr_parts))
                display_text = (
                    l_obj.location_name
                    if l_obj.location_name
                    else (full_addr if full_addr else "N/A")
                )
                if (
                    l_obj.location_name
                    and full_addr
                    and l_obj.location_name.lower()
                    != full_addr.lower().replace(",", "").strip()
                ):
                    display_text = f"{l_obj.location_name} ({full_addr})"
                elif not l_obj.location_name and full_addr:
                    display_text = full_addr
                self.locations_table.setItem(r, 1, QTableWidgetItem(display_text))
                self.locations_table.setItem(
                    r, 2, QTableWidgetItem("Yes" if l_obj.is_active else "No")
                )
                self.locations_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, l_obj.location_id
                )
            self.locations_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(locs)} locations.")
        except Exception as e:
            self.logger.error(f"Error loading locations: {e}", exc_info=True)
        self.current_selected_location_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_location_selected(self):
        self.current_selected_location_id = None
        if self.locations_table and self.locations_table.selectedItems():
            item = self.locations_table.item(self.locations_table.currentRow(), 0)
            if item:
                self.current_selected_location_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Location selected: {self.current_selected_location_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_location(self):
        dialog = AddEditLocationDialog(
            parent_view=self,
            controller=self.location_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_locations_data()
            self.show_status_message("Location added.", True)

    @Slot()
    def _edit_selected_location(self):
        if not self.current_selected_location_id:
            self.show_warning("Edit Location", "Select location.")
            return
        loc_to_edit = self.location_controller.get_location_by_id(
            self.current_selected_location_id
        )
        if not loc_to_edit:
            self.show_error("Error", "Location not found.")
            self.load_locations_data()
            return
        dialog = AddEditLocationDialog(
            parent_view=self,
            controller=self.location_controller,
            location=loc_to_edit,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_locations_data()
            self.show_status_message(
                f"Location '{loc_to_edit.location_name}' updated.", True
            )
            self._try_reselect_item(
                self.locations_table, self.current_selected_location_id
            )

    @Slot()
    def _delete_selected_location(self):
        self._generic_delete_action(
            self.current_selected_location_id,
            "Location",
            self.location_controller.delete_location,
            self.load_locations_data,
            "current_selected_location_id",
            self.locations_table,
        )

    def load_charge_codes_data(self):
        self.logger.info("Loading charge codes data for tab...")
        if not self.charge_codes_table:
            self.logger.warning("Charge codes table not ready.")
            return
        try:
            ccs = self.charge_code_controller.get_all_charge_codes(status_filter="all")
            self.charge_codes_table.setRowCount(0)
            self.charge_codes_table.setSortingEnabled(False)
            for r, c_obj in enumerate(ccs):
                self.charge_codes_table.insertRow(r)
                self.charge_codes_table.setItem(r, 0, QTableWidgetItem(c_obj.code))
                self.charge_codes_table.setItem(
                    r, 1, QTableWidgetItem(c_obj.description or "")
                )
                self.charge_codes_table.setItem(
                    r, 2, QTableWidgetItem(c_obj.category or "")
                )
                self.charge_codes_table.setItem(
                    r,
                    3,
                    QTableWidgetItem(
                        f"{c_obj.standard_charge:.2f}"
                        if c_obj.standard_charge is not None
                        else "0.00"
                    ),
                )
                self.charge_codes_table.setItem(
                    r, 4, QTableWidgetItem("Yes" if c_obj.is_active else "No")
                )
                self.charge_codes_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, c_obj.charge_code_id
                )
            self.charge_codes_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(ccs)} charge codes.")
        except Exception as e:
            self.logger.error(f"Error loading charge codes: {e}", exc_info=True)
        self.current_selected_charge_code_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_charge_code_selected(self):
        self.current_selected_charge_code_id = None
        if self.charge_codes_table and self.charge_codes_table.selectedItems():
            item = self.charge_codes_table.item(self.charge_codes_table.currentRow(), 0)
            if item:
                self.current_selected_charge_code_id = item.data(
                    Qt.ItemDataRole.UserRole
                )
        self.logger.info(
            f"Charge Code selected: {self.current_selected_charge_code_id}"
        )
        self._update_crud_button_states()

    @Slot()
    def _add_new_charge_code(self):
        # AddEditChargeCodeDialog (v1.1.3) __init__: (self, parent, controller, charge_code=None)
        # It does not take current_user_id.
        dialog = AddEditChargeCodeDialog(
            parent=self, controller=self.charge_code_controller
        )
        if dialog.exec():
            self.load_charge_codes_data()
            self.show_status_message("Charge code added.", True)

    @Slot()
    def _edit_selected_charge_code(self):
        if not self.current_selected_charge_code_id:
            self.show_warning("Edit Charge Code", "Select charge code.")
            return
        cc_to_edit = self.charge_code_controller.get_charge_code_by_id(
            self.current_selected_charge_code_id
        )
        if not cc_to_edit:
            self.show_error("Error", "Charge code not found.")
            self.load_charge_codes_data()
            return
        # AddEditChargeCodeDialog (v1.1.3) __init__: (self, parent, controller, charge_code=None)
        dialog = AddEditChargeCodeDialog(
            parent=self, controller=self.charge_code_controller, charge_code=cc_to_edit
        )
        if dialog.exec():
            self.load_charge_codes_data()
            self.show_status_message(f"Charge code '{cc_to_edit.code}' updated.", True)
            self._try_reselect_item(
                self.charge_codes_table, self.current_selected_charge_code_id
            )

    @Slot()
    def _delete_selected_charge_code(self):
        self._generic_delete_action(
            self.current_selected_charge_code_id,
            "Charge Code",
            self.charge_code_controller.toggle_charge_code_status,
            self.load_charge_codes_data,
            "current_selected_charge_code_id",
            self.charge_codes_table,
        )

    def load_master_owners_data(self):
        self.logger.info("Loading master owners data for tab...")
        if not self.owners_table:
            self.logger.warning("Owners table not ready.")
            return
        try:
            owners = (
                self.owner_controller.get_all_master_owners(include_inactive=True)
                if hasattr(self.owner_controller, "get_all_master_owners")
                else []
            )
            if not hasattr(self.owner_controller, "get_all_master_owners"):
                self.logger.error("OwnerController missing 'get_all_master_owners'.")
                QMessageBox.warning(
                    self, "Load Error", "Cannot load owners: Controller method missing."
                )
                return
            self.owners_table.setRowCount(0)
            self.owners_table.setSortingEnabled(False)
            for r, o_obj in enumerate(owners):
                self.owners_table.insertRow(r)
                self.owners_table.setItem(
                    r, 0, QTableWidgetItem(o_obj.account_number or "")
                )
                name_disp = (
                    o_obj.farm_name
                    or f"{o_obj.first_name or ''} {o_obj.last_name or ''}".strip()
                    or f"ID: {o_obj.owner_id}"
                )
                self.owners_table.setItem(r, 1, QTableWidgetItem(name_disp))
                self.owners_table.setItem(r, 2, QTableWidgetItem(o_obj.phone or ""))
                self.owners_table.setItem(
                    r, 3, QTableWidgetItem("Yes" if o_obj.is_active else "No")
                )
                self.owners_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, o_obj.owner_id
                )
            self.owners_table.setSortingEnabled(True)
            self.logger.info(f"Loaded {len(owners)} master owners.")
        except Exception as e:
            self.logger.error(f"Error loading master owners: {e}", exc_info=True)
        self.current_selected_owner_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_master_owner_selected(self):
        self.current_selected_owner_id = None
        if self.owners_table and self.owners_table.selectedItems():
            item = self.owners_table.item(self.owners_table.currentRow(), 0)
            if item:
                self.current_selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Master Owner selected: {self.current_selected_owner_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_owner(self):
        self.show_info(
            "Not Implemented", "Adding master owners is not yet implemented."
        )

    @Slot()
    def _edit_selected_owner(self):
        self.show_info(
            "Not Implemented", "Editing master owners is not yet implemented."
        )

    @Slot()
    def _delete_selected_owner(self):
        self._generic_delete_action(
            self.current_selected_owner_id,
            "Master Owner",
            self.owner_controller.delete_master_owner,
            self.load_master_owners_data,
            "current_selected_owner_id",
            self.owners_table,
        )

    def _generic_delete_action(
        self,
        item_id,
        item_name_singular: str,
        controller_delete_method,
        load_data_method,
        current_selection_attr: str,
        list_or_table_widget,
    ):
        if not item_id:
            self.show_warning(
                f"Delete {item_name_singular}",
                f"Please select a {item_name_singular.lower()} to delete.",
            )
            return
        item_repr = f"{item_name_singular} ID {item_id}"
        current_row_widget = None
        if (
            isinstance(list_or_table_widget, QListWidget)
            and list_or_table_widget.currentItem()
        ):
            current_row_widget = list_or_table_widget.itemWidget(
                list_or_table_widget.currentItem()
            )
            if isinstance(current_row_widget, UserListItemWidget):
                item_repr = f"User '{current_row_widget.name_value_label.text()}' (ID: {current_row_widget.id_value_label.text()})"
        elif (
            isinstance(list_or_table_widget, QTableWidget)
            and list_or_table_widget.selectedItems()
        ):
            current_row = list_or_table_widget.currentRow()
            name_col_idx = 1 if item_name_singular in ["User", "Master Owner"] else 0
            if list_or_table_widget.columnCount() > name_col_idx:
                name_item = list_or_table_widget.item(current_row, name_col_idx)
                id_item = list_or_table_widget.item(current_row, 0)
                id_val = id_item.text() if id_item else str(item_id)
                name_val = name_item.text() if name_item else ""
                item_repr = f"{item_name_singular} '{name_val}' (ID: {id_val})"
        if (
            QMessageBox.question(
                self,
                f"Confirm Delete",
                f"Are you sure you want to permanently delete {item_repr}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                success, message = (
                    controller_delete_method(item_id)
                    if item_name_singular == "Charge Code"
                    else controller_delete_method(item_id, self.current_user_id)
                )
                if success:
                    self.show_status_message(message, True)
                    load_data_method()
                    setattr(self, current_selection_attr, None)
                else:
                    self.show_error_message(f"Delete Failed", message)
            except Exception as e:
                self.logger.error(
                    f"Error deleting {item_name_singular.lower()} ID {item_id}: {e}",
                    exc_info=True,
                )
                self.show_error_message(
                    "Delete Error", f"An unexpected error occurred: {e}"
                )
        self._update_crud_button_states()

    def closeEvent(self, event: QCloseEvent):
        self.logger.info("User Management screen closing.")
        super().closeEvent(event)
