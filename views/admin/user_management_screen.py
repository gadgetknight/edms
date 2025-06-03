# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.12.14
Purpose: Provides a tabbed UI for managing users, locations, charge codes, and owners.
         - Integrates AddEditOwnerDialog for managing master owner list.
         - Updates Owners tab table styling and column widths.
         - Enables Add/Edit Owner buttons.
Last Updated: June 02, 2025
Author: Gemini

Changelog:
- v1.12.14 (2025-06-02):
    - Imported `AddEditOwnerDialog`.
    - In `_create_owners_tab()`:
        - Enabled "Add New Owner" and "Edit Selected Owner" buttons.
        - Applied consistent selection styling to `owners_table`.
        - Adjusted column resize modes for `owners_table` ("Owner Name" stretches,
          "Account #", "Primary Phone" interactive with initial width, "Active"
          resizes to content).
    - Implemented `_add_new_owner()` to use `AddEditOwnerDialog`.
    - Implemented `_edit_selected_owner()` to use `AddEditOwnerDialog`.
    - In `load_master_owners_data()`: Added explicit `setColumnWidth` calls
      for Account # and Primary Phone after `resizeColumnsToContents`.
- v1.12.13 (2025-05-31):
    - Fixed SyntaxError in `_try_reselect_item`.
- v1.12.12 (2025-06-02):
    - Adjusted Locations tab column widths for better layout.
- v1.12.11 (2025-05-31):
    - Adjusted Locations tab table column styling and updated tab titles.
- v1.12.10 (2025-05-31):
    - Fixed UnboundLocalError in _on_location_selected.
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
from models import StateProvince as StateProvinceModel

from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .dialogs.add_edit_owner_dialog import AddEditOwnerDialog  # ADDED

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
        (self.add_owner_button, self.edit_owner_button, self.delete_owner_button) = (
            None,
            None,
            None,
        )

        super().__init__(parent)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = current_user_id  # This is the admin using the screen
        self.user_controller = UserController()
        self.location_controller = LocationController()
        self.charge_code_controller = ChargeCodeController()
        self.owner_controller = OwnerController()

        self.setWindowTitle("User & System Management")
        self.resize(1200, 750)

        self.load_all_data()
        self.logger.info(
            f"UserManagementScreen (v{self.get_version()}) initialized for user: {self.current_user_id}"
        )

    def get_version(self) -> str:
        try:
            docstring = self.__class__.__doc__
            if docstring:
                version_line = next(
                    line
                    for line in docstring.splitlines()
                    if line.strip().startswith("Version:")
                )
                return version_line.split("Version:")[1].strip()
            self.logger.warning("Docstring not found for UserManagementScreen class.")
            return "Unknown (No Docstring)"
        except StopIteration:
            self.logger.warning(
                "Could not find 'Version:' line in UserManagementScreen docstring."
            )
            return "Unknown (No Version Line)"
        except Exception as e:
            self.logger.error(
                f"Error parsing version from UserManagementScreen docstring: {e}",
                exc_info=True,
            )
            return "Unknown (Parsing Error)"

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
        return (
            f"QPushButton {{ background-color: {bg_color}; color: {text_color}; border: 1px solid {border_color}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px; }} "
            f"QPushButton:hover {{ background-color: {QColor(bg_color).lighter(115).name()}; }} "
            f"QPushButton:pressed {{ background-color: {QColor(bg_color).darker(110).name()}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}"
        )

    def setup_ui(self):
        self.logger.info(
            f"****** UserManagementScreen.setup_ui() (v{self.get_version()}) ENTERED ******"
        )
        container_layout = self.central_widget.layout()
        if not container_layout:
            container_layout = QVBoxLayout(self.central_widget)
            self.central_widget.setLayout(container_layout)
        while container_layout.count():
            item = container_layout.takeAt(0)
            item.widget() and item.widget().deleteLater()

        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND}; border-top-left-radius: 0px; border-top-right-radius: 6px; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }} QTabBar::tab {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY}; border: 1px solid {DARK_BORDER}; border-bottom: none; padding: 8px 20px; margin-right: 1px; border-top-left-radius: 5px; border-top-right-radius: 5px; min-width: 150px; }} QTabBar::tab:selected {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border-bottom: 1px solid {DARK_WIDGET_BACKGROUND}; }} QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; }}"
        )

        user_management_tab = self._create_user_management_tab()
        self.main_tab_widget.addTab(user_management_tab, "👤 Manage Users")

        locations_tab = self._create_locations_tab()
        self.main_tab_widget.addTab(locations_tab, "📍 Manage Locations")

        charge_codes_tab = self._create_charge_codes_tab()
        self.main_tab_widget.addTab(charge_codes_tab, "💲 Manage Charge Codes")

        owners_tab = self._create_owners_tab()
        self.main_tab_widget.addTab(owners_tab, "👥 Manage Owner List")

        container_layout.addWidget(self.main_tab_widget)
        self.main_tab_widget.currentChanged.connect(self._on_tab_changed)
        self.logger.info(
            f"UserManagementScreen.setup_ui (v{self.get_version()}) FINISHED."
        )

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
            f"QListWidget {{ border: 1px solid {DARK_BORDER}; border-radius: 4px; background-color: {DARK_WIDGET_BACKGROUND}; }} QListWidget::item {{ border-bottom: 1px solid {DARK_HEADER_FOOTER}; padding: 0px; }} QListWidget::item:selected {{ background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()}; }} QListWidget::item:selected:!active {{ background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()}; color: {DARK_TEXT_PRIMARY}; }} QListWidget::item:selected:active {{ background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()}; color: {DARK_TEXT_PRIMARY}; }}"
        )
        self.users_list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.users_list_widget.currentItemChanged.connect(self._on_user_selected)
        main_layout.addWidget(self.users_list_widget)
        return tab_widget

    def _create_locations_tab(
        self,
    ) -> QWidget:  # Column resize modes and selection style updated in v1.12.11
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
        self.locations_table.setColumnCount(7)
        self.locations_table.setHorizontalHeaderLabels(
            ["Location Name", "Address", "City", "State", "Zip", "Country", "Active"]
        )
        self.locations_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.locations_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        header = self.locations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        selected_bg_color = QColor(DARK_PRIMARY_ACTION).lighter(130).name()
        self.locations_table.setStyleSheet(
            f"QTableWidget::item:selected {{ background-color: {selected_bg_color}; color: {DARK_TEXT_PRIMARY}; }}"
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

        # MODIFIED: Enable Add and Edit buttons
        if self.add_owner_button:
            self.add_owner_button.setEnabled(True)
        if self.edit_owner_button:
            self.edit_owner_button.setEnabled(
                True
            )  # Actual state managed by _update_crud_button_states

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

        # MODIFIED: Column resize strategy and selection style for owners_table
        header = self.owners_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Account #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Owner Name
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )  # Primary Phone
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Active

        selected_bg_color = QColor(DARK_PRIMARY_ACTION).lighter(130).name()
        self.owners_table.setStyleSheet(
            f"""
            QTableWidget::item:selected {{
                background-color: {selected_bg_color};
                color: {DARK_TEXT_PRIMARY};
            }}
            """
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

        # MODIFIED: Edit Owner button enabled based on selection, Add Owner is always enabled here
        if self.add_owner_button:
            self.add_owner_button.setEnabled(current_tab_index == 3)  # Or just True
        if self.edit_owner_button:
            self.edit_owner_button.setEnabled(current_tab_index == 3 and owner_selected)
        if self.delete_owner_button:
            self.delete_owner_button.setEnabled(
                current_tab_index == 3 and owner_selected
            )

    def load_all_data(self):
        self.logger.info(
            "UserManagementScreen: Loading initial data for the first tab."
        )
        self._on_tab_changed(0)
        self.update_status("User Management Ready.")

    def load_users_data(self):
        self.logger.info("Loading users data for User Management tab (custom list)...")
        if not self.users_list_widget:
            self.logger.warning("User list widget not ready.")
            return
        try:
            users = self.user_controller.get_all_users(include_inactive=True)
            self.users_list_widget.clear()
            for user_model_instance in users:
                list_item = QListWidgetItem(self.users_list_widget)
                item_widget = UserListItemWidget(
                    user_model_instance, self.users_list_widget
                )
                list_item.setSizeHint(item_widget.sizeHint())
                list_item.setData(Qt.ItemDataRole.UserRole, user_model_instance.user_id)
                self.users_list_widget.addItem(list_item)
                self.users_list_widget.setItemWidget(list_item, item_widget)
            self.logger.info(f"Loaded {len(users)} users into custom list.")
        except Exception as e:
            self.logger.error(
                f"Error loading user data into custom list: {e}", exc_info=True
            )
            self.show_error("Load Error", f"Could not load users: {e}")
        self.current_selected_user_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_user_selected(self):
        self.current_selected_user_id = None
        if self.users_list_widget and self.users_list_widget.currentItem():
            self.current_selected_user_id = self.users_list_widget.currentItem().data(
                Qt.ItemDataRole.UserRole
            )
        self.logger.info(f"User selected from list: {self.current_selected_user_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_user(self):
        dialog = AddEditUserDialog(
            parent_view=self,
            user_controller=self.user_controller,
            current_user_id=self.current_user_id,
        )  # Pass current_user_id if dialog needs it
        if dialog.exec():
            self.load_users_data()
            self.update_status("User added successfully.")

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
        dialog = AddEditUserDialog(
            parent_view=self,
            user_controller=self.user_controller,
            current_user_object=user_to_edit,
            current_user_id=self.current_user_id,
        )  # Pass current_user_id
        if dialog.exec():
            self.load_users_data()
            self.update_status(f"User '{user_to_edit.user_id}' updated.")
            self._try_reselect_item(
                self.users_list_widget, self.current_selected_user_id
            )

    def _try_reselect_item(
        self, list_or_table_widget, item_id_to_select
    ):  # Unchanged from v1.12.13
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
                    found = True
                    if list_or_table_widget == self.users_list_widget:
                        self._on_user_selected()
                    break
        elif isinstance(list_or_table_widget, QTableWidget):
            for row in range(list_or_table_widget.rowCount()):
                item_widget_in_table = list_or_table_widget.item(row, 0)
                if (
                    item_widget_in_table
                    and item_widget_in_table.data(Qt.ItemDataRole.UserRole)
                    == item_id_to_select
                ):
                    list_or_table_widget.setCurrentCell(row, 0)
                    found = True
                    if list_or_table_widget == self.locations_table:
                        self._on_location_selected()
                    elif list_or_table_widget == self.charge_codes_table:
                        self._on_charge_code_selected()
                    elif list_or_table_widget == self.owners_table:
                        self._on_master_owner_selected()
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

    def load_locations_data(self):  # Column width setting from v1.12.12
        self.logger.info("Loading locations data for tab...")
        if not self.locations_table:
            self.logger.warning("Locations table not ready.")
            return
        try:
            locations = self.location_controller.get_all_locations(status_filter="all")
            self.locations_table.setRowCount(0)
            self.locations_table.setSortingEnabled(False)
            for r, loc_obj in enumerate(locations):
                self.locations_table.insertRow(r)
                self.locations_table.setItem(
                    r, 0, QTableWidgetItem(loc_obj.location_name or "N/A")
                )
                self.locations_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, loc_obj.location_id
                )
                self.locations_table.setItem(
                    r, 1, QTableWidgetItem(loc_obj.address_line1 or "")
                )
                self.locations_table.setItem(r, 2, QTableWidgetItem(loc_obj.city or ""))
                state_name = (
                    loc_obj.state.state_name
                    if loc_obj.state
                    else (loc_obj.state_code or "")
                )
                self.locations_table.setItem(r, 3, QTableWidgetItem(state_name))
                self.locations_table.setItem(
                    r, 4, QTableWidgetItem(loc_obj.zip_code or "")
                )
                self.locations_table.setItem(
                    r, 5, QTableWidgetItem(loc_obj.country_code or "")
                )
                self.locations_table.setItem(
                    r, 6, QTableWidgetItem("Yes" if loc_obj.is_active else "No")
                )
            self.locations_table.setSortingEnabled(True)
            self.locations_table.resizeColumnsToContents()
            self.locations_table.setColumnWidth(0, 200)
            self.locations_table.setColumnWidth(2, 150)
            self.logger.info(
                f"Loaded {len(locations)} locations with detailed address."
            )
        except Exception as e:
            self.logger.error(f"Error loading locations: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load locations: {e}")
        self.current_selected_location_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_location_selected(self):
        self.current_selected_location_id = None
        item = None
        if self.locations_table and self.locations_table.selectedItems():
            current_row = self.locations_table.currentRow()
            (current_row >= 0 and (item := self.locations_table.item(current_row, 0)))
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
            self.update_status("Location added.")

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
            self.update_status(f"Location '{loc_to_edit.location_name}' updated.")
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
            self.show_error("Load Error", f"Could not load charge codes: {e}")
        self.current_selected_charge_code_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_charge_code_selected(self):
        self.current_selected_charge_code_id = None
        item = None
        if self.charge_codes_table and self.charge_codes_table.selectedItems():
            current_row = self.charge_codes_table.currentRow()
            (
                current_row >= 0
                and (item := self.charge_codes_table.item(current_row, 0))
            )
        if item:
            self.current_selected_charge_code_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(
            f"Charge Code selected: {self.current_selected_charge_code_id}"
        )
        self._update_crud_button_states()

    @Slot()
    def _add_new_charge_code(self):
        dialog = AddEditChargeCodeDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
        )  # Pass current_user_id
        if dialog.exec():
            self.load_charge_codes_data()
            self.update_status("Charge code added.")

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
        dialog = AddEditChargeCodeDialog(
            parent=self,
            controller=self.charge_code_controller,
            charge_code=cc_to_edit,
            current_user_id=self.current_user_id,
        )  # Pass current_user_id
        if dialog.exec():
            self.load_charge_codes_data()
            self.update_status(f"Charge code '{cc_to_edit.code}' updated.")
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
                self.show_error(
                    "Load Error", "Cannot load owners: Controller method missing."
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
            # MODIFIED: Apply column widths after populating
            self.owners_table.resizeColumnsToContents()
            self.owners_table.setColumnWidth(0, 120)  # Account #
            # Column 1 (Owner Name) is Stretch from _create_owners_tab
            self.owners_table.setColumnWidth(2, 150)  # Primary Phone
            # Column 3 (Active) is ResizeToContents

            self.logger.info(f"Loaded {len(owners)} master owners.")
        except Exception as e:
            self.logger.error(f"Error loading master owners: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load master owners: {e}")
        self.current_selected_owner_id = None
        self._update_crud_button_states()

    @Slot()
    def _on_master_owner_selected(self):
        self.current_selected_owner_id = None
        item = None
        if self.owners_table and self.owners_table.selectedItems():
            current_row = self.owners_table.currentRow()
            (current_row >= 0 and (item := self.owners_table.item(current_row, 0)))
        if item:
            self.current_selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(f"Master Owner selected: {self.current_selected_owner_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_owner(self):
        dialog = AddEditOwnerDialog(
            parent_view=self,
            owner_controller=self.owner_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_master_owners_data()
            self.update_status("Owner added successfully.")

    @Slot()
    def _edit_selected_owner(self):
        if not self.current_selected_owner_id:
            self.show_warning("Edit Owner", "Please select an owner to edit.")
            return
        owner_to_edit = self.owner_controller.get_owner_by_id(
            self.current_selected_owner_id
        )
        if not owner_to_edit:
            self.show_error(
                "Error", "Selected owner not found. It may have been deleted."
            )
            self.load_master_owners_data()  # Refresh list
            return

        dialog = AddEditOwnerDialog(
            parent_view=self,
            owner_controller=self.owner_controller,
            current_user_id=self.current_user_id,
            owner_object=owner_to_edit,
        )
        if dialog.exec():
            self.load_master_owners_data()
            owner_name_display = (
                owner_to_edit.farm_name
                or f"{owner_to_edit.first_name or ''} {owner_to_edit.last_name or ''}".strip()
                or f"ID {owner_to_edit.owner_id}"
            )
            self.update_status(f"Owner '{owner_name_display}' updated successfully.")
            self._try_reselect_item(self.owners_table, self.current_selected_owner_id)

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
        if (
            isinstance(list_or_table_widget, QListWidget)
            and list_or_table_widget.currentItem()
        ):
            current_row_widget = list_or_table_widget.itemWidget(
                list_or_table_widget.currentItem()
            )
            item_repr = (
                f"User '{current_row_widget.name_value_label.text()}' (ID: {current_row_widget.id_value_label.text()})"
                if isinstance(current_row_widget, UserListItemWidget)
                else item_repr
            )
        elif (
            isinstance(list_or_table_widget, QTableWidget)
            and list_or_table_widget.selectedItems()
        ):
            current_row = list_or_table_widget.currentRow()
            name_col_idx = (
                1 if item_name_singular in ["User", "Master Owner", "Location"] else 0
            )  # Location name is also col 0 but ID is there.
            # For locations, name is at index 0 where ID is. For Owners, name is at index 1.
            if item_name_singular == "Location":
                name_col_idx = 0

            if list_or_table_widget.columnCount() > name_col_idx:
                name_item = list_or_table_widget.item(current_row, name_col_idx)
                id_item_data_source_col = 0  # ID always in first column's UserRole data
                id_item = list_or_table_widget.item(
                    current_row, id_item_data_source_col
                )
                id_val = (
                    str(id_item.data(Qt.ItemDataRole.UserRole))
                    if id_item
                    else str(item_id)
                )  # Use actual ID from UserRole data
                name_val = name_item.text() if name_item else ""
                item_repr = f"{item_name_singular} '{name_val}' (ID: {id_val})"
        if self.show_question(
            f"Confirm Delete",
            f"Are you sure you want to permanently delete {item_repr}?",
        ):
            try:
                success, message = (
                    controller_delete_method(item_id)
                    if item_name_singular == "Charge Code"
                    and controller_delete_method
                    == self.charge_code_controller.toggle_charge_code_status
                    else controller_delete_method(item_id, self.current_user_id)
                )
                if success:
                    self.update_status(message)
                    load_data_method()
                    setattr(self, current_selection_attr, None)
                else:
                    self.show_error(f"Delete Failed", message)
            except Exception as e:
                self.logger.error(
                    f"Error deleting {item_name_singular.lower()} ID {item_id}: {e}",
                    exc_info=True,
                )
                self.show_error("Delete Error", f"An unexpected error occurred: {e}")
        self._update_crud_button_states()

    def closeEvent(self, event: QCloseEvent):
        self.logger.info("User Management screen closing.")
        super().closeEvent(event)
