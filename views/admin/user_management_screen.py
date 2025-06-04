# views/admin/user_management_screen.py
"""
EDSI Veterinary Management System - User Management Screen
Version: 1.12.29
Purpose: Provides a tabbed UI for managing users, locations, charge codes, owners,
         and charge code categories/processes.
         - Corrected indentation error in _on_location_selected.
Last Updated: June 3, 2025
Author: Gemini

Changelog:
- v1.12.29 (2025-06-03):
    - In `_on_location_selected()`: Corrected an indentation error for the
      `if current_row >= 0:` check to ensure it's properly nested,
      preventing runtime errors and ensuring correct logic execution.
- v1.12.28 (2025-06-03):
    - In `_create_charge_codes_tab()`: Reordered columns and added "Alternate Code".
    - In `load_charge_codes_data()`: Updated to match new column order.
- v1.12.27 (2025-06-03):
    - Corrected call to `get_all_charge_code_categories_hierarchical`
      in `load_charge_code_categories_data`.
# ... (previous changelog entries)
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
    QRadioButton,
    QButtonGroup,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QCloseEvent, QColor

from views.base_view import BaseView
from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.charge_code_controller import ChargeCodeController
from controllers.owner_controller import OwnerController

from models import (
    User as UserModel,
    Location as LocationModel,
    ChargeCode as ChargeCodeModel,
)
from models import ChargeCodeCategory as ChargeCodeCategoryModel, Owner as OwnerModel
from models import StateProvince as StateProvinceModel

from .dialogs.add_edit_user_dialog import AddEditUserDialog
from .dialogs.add_edit_location_dialog import AddEditLocationDialog
from .dialogs.add_edit_charge_code_dialog import AddEditChargeCodeDialog
from .dialogs.add_edit_owner_dialog import AddEditOwnerDialog
from .dialogs.add_edit_charge_code_category_dialog import (
    AddEditChargeCodeCategoryDialog,
)

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
    # ... (class remains unchanged from v1.12.28) ...
    def __init__(self, user_model: UserModel, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)
        label_style = (
            f"color: {DARK_TEXT_SECONDARY}; padding-top: 2px; font-size: 11px;"
        )
        value_box_style = f"background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; padding: 4px 6px; border-radius: 3px; font-size: 11px; min-height: 18px;"
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
    # ... (attributes remain unchanged from v1.12.28) ...
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
    cc_filter_button_group: Optional[QButtonGroup] = None
    cc_active_radio: Optional[QRadioButton] = None
    cc_inactive_radio: Optional[QRadioButton] = None
    cc_all_radio: Optional[QRadioButton] = None
    charge_code_categories_tree: Optional[QTreeWidget] = None
    add_ccc_category_button: Optional[QPushButton] = None
    add_ccc_process_button: Optional[QPushButton] = None
    edit_ccc_button: Optional[QPushButton] = None
    toggle_ccc_status_button: Optional[QPushButton] = None
    delete_ccc_button: Optional[QPushButton] = None
    current_selected_ccc_id: Optional[int] = None
    current_selected_ccc_level: Optional[int] = None
    current_selected_ccc_object: Optional[ChargeCodeCategoryModel] = None
    ccc_filter_button_group: Optional[QButtonGroup] = None
    ccc_active_radio: Optional[QRadioButton] = None
    ccc_inactive_radio: Optional[QRadioButton] = None
    ccc_all_radio: Optional[QRadioButton] = None
    owners_table: Optional[QTableWidget]
    add_owner_button: Optional[QPushButton]
    edit_owner_button: Optional[QPushButton]
    delete_owner_button: Optional[QPushButton]
    current_selected_owner_id: Optional[int] = None

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        # ... (__init__ remains unchanged from v1.12.28) ...
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
        self.cc_filter_button_group = None
        self.cc_active_radio, self.cc_inactive_radio, self.cc_all_radio = (
            None,
            None,
            None,
        )
        self.charge_code_categories_tree = None
        (
            self.add_ccc_category_button,
            self.add_ccc_process_button,
            self.edit_ccc_button,
            self.toggle_ccc_status_button,
            self.delete_ccc_button,
        ) = (None, None, None, None, None)
        self.current_selected_ccc_id = None
        self.current_selected_ccc_level = None
        self.current_selected_ccc_object = None
        self.ccc_filter_button_group = None
        self.ccc_active_radio, self.ccc_inactive_radio, self.ccc_all_radio = (
            None,
            None,
            None,
        )
        self.owners_table = None
        (self.add_owner_button, self.edit_owner_button, self.delete_owner_button) = (
            None,
            None,
            None,
        )
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = current_user_id
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

    def get_version(self) -> str:  # ... (method remains unchanged) ...
        try:
            module_docstring = __doc__
            if module_docstring:
                version_line = next(
                    line
                    for line in module_docstring.splitlines()
                    if line.strip().startswith("Version:")
                )
                return version_line.split("Version:")[1].strip()
            self.logger.warning("File-level docstring not found or Version missing.")
            return "Unknown (No File Docstring Version)"
        except StopIteration:
            self.logger.warning(
                "Could not find 'Version:' line in file-level docstring."
            )
            return "Unknown (No Version Line)"
        except Exception as e:
            self.logger.error(
                f"Error parsing version from file-level docstring: {e}", exc_info=True
            )
            return "Unknown (Parsing Error)"

    def _get_crud_button_style(
        self, button_type="default", is_add_button_specific_style=False
    ) -> str:  # ... (method remains unchanged) ...
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
        return f"QPushButton {{ background-color: {bg_color}; color: {text_color}; border: 1px solid {border_color}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px; }} QPushButton:hover {{ background-color: {QColor(bg_color).lighter(115).name()}; }} QPushButton:pressed {{ background-color: {QColor(bg_color).darker(110).name()}; }} QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}"

    def setup_ui(self):  # ... (method remains unchanged) ...
        self.logger.info(
            f"****** UserManagementScreen.setup_ui() (v{self.get_version()}) ENTERED ******"
        )
        container_layout = self.central_widget.layout()
        if not container_layout:
            container_layout = QVBoxLayout(self.central_widget)
            self.central_widget.setLayout(container_layout)
        if container_layout is not None:
            while container_layout.count():
                item = container_layout.takeAt(0)
                widget_to_remove = None
                if item is not None:
                    widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    widget_to_remove.deleteLater()
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND}; border-top-left-radius: 0px; border-top-right-radius: 6px; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }} QTabBar::tab {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY}; border: 1px solid {DARK_BORDER}; border-bottom: none; padding: 8px 20px; margin-right: 1px; border-top-left-radius: 5px; border-top-right-radius: 5px; min-width: 150px; }} QTabBar::tab:selected {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border-bottom: 1px solid {DARK_WIDGET_BACKGROUND}; }} QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; }}"
        )
        user_management_tab = self._create_user_management_tab()
        self.main_tab_widget.addTab(user_management_tab, "👤 Manage Users")
        locations_tab = self._create_locations_tab()
        self.main_tab_widget.addTab(locations_tab, "📍 Manage Locations")
        charge_code_categories_tab = self._create_charge_code_categories_tab()
        self.main_tab_widget.addTab(
            charge_code_categories_tab, "🗂️ Manage Categories/Processes"
        )
        charge_codes_tab = self._create_charge_codes_tab()
        self.main_tab_widget.addTab(charge_codes_tab, "💲 Manage Charge Codes")
        owners_tab = self._create_owners_tab()
        self.main_tab_widget.addTab(owners_tab, "👥 Manage Owner List")
        container_layout.addWidget(self.main_tab_widget)
        self.main_tab_widget.currentChanged.connect(self._on_tab_changed)
        self.logger.info(
            f"UserManagementScreen.setup_ui (v{self.get_version()}) FINISHED."
        )

    def _on_tab_changed(self, index: int):  # ... (method remains unchanged) ...
        self.logger.info(
            f"Tab changed to index: {index}, new tab title: {self.main_tab_widget.tabText(index) if self.main_tab_widget else 'N/A'}"
        )
        self.current_selected_user_id = None
        self.current_selected_location_id = None
        self.current_selected_charge_code_id = None
        self.current_selected_ccc_id = None
        self.current_selected_ccc_level = None
        self.current_selected_ccc_object = None
        self.current_selected_owner_id = None
        tab_widgets_and_clear_methods = [
            (self.users_list_widget, 0),
            (self.locations_table, 1),
            (self.charge_code_categories_tree, 2),
            (self.charge_codes_table, 3),
            (self.owners_table, 4),
        ]
        for widget, tab_index in tab_widgets_and_clear_methods:
            if (
                widget
                and hasattr(widget, "selectionModel")
                and widget.selectionModel()
                and (
                    not self.main_tab_widget
                    or self.main_tab_widget.widget(tab_index)
                    != self.main_tab_widget.currentWidget()
                )
            ):
                widget.selectionModel().clear()
            elif (
                widget
                and not hasattr(widget, "selectionModel")
                and hasattr(widget, "clearSelection")
                and (
                    not self.main_tab_widget
                    or self.main_tab_widget.widget(tab_index)
                    != self.main_tab_widget.currentWidget()
                )
            ):
                widget.clearSelection()
        current_tab_text = (
            self.main_tab_widget.tabText(index) if self.main_tab_widget else ""
        )
        if "Manage Users" in current_tab_text:
            self.load_users_data()
        elif "Manage Locations" in current_tab_text:
            self.load_locations_data()
        elif "Manage Categories/Processes" in current_tab_text:
            self.load_charge_code_categories_data()
        elif "Manage Charge Codes" in current_tab_text:
            self.load_charge_codes_data()
        elif "Manage Owner List" in current_tab_text:
            self.load_master_owners_data()
        self._update_crud_button_states()
        self._update_ccc_buttons_state()

    def _create_crud_button_panel(
        self,
        add_text: str,
        edit_text_base: str,
        delete_text_base: str,
        add_slot,
        edit_slot,
        delete_slot,
        add_tooltip: str = "",
        edit_tooltip: str = "",
        delete_tooltip: str = "",
    ) -> (
        QHBoxLayout,
        QPushButton,
        QPushButton,
        QPushButton,
    ):  # ... (method remains unchanged) ...
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        add_button = QPushButton(add_text)
        is_user_add_btn = "User" in add_text
        add_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=is_user_add_btn)
        )
        add_button.clicked.connect(add_slot)
        if add_tooltip:
            add_button.setToolTip(add_tooltip)
        edit_button = QPushButton(f"Edit Selected {edit_text_base}")
        edit_button.setStyleSheet(self._get_crud_button_style("default"))
        edit_button.clicked.connect(edit_slot)
        edit_button.setEnabled(False)
        if edit_tooltip:
            edit_button.setToolTip(edit_tooltip)
        delete_button = QPushButton(f"Delete Selected {delete_text_base}")
        delete_button.setStyleSheet(self._get_crud_button_style("delete"))
        delete_button.clicked.connect(delete_slot)
        delete_button.setEnabled(False)
        if delete_tooltip:
            delete_button.setToolTip(delete_tooltip)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        return button_layout, add_button, edit_button, delete_button

    def _create_user_management_tab(
        self,
    ) -> QWidget:  # ... (method remains unchanged) ...
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

    def _create_locations_tab(self) -> QWidget:  # ... (method remains unchanged) ...
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

    def _create_charge_code_categories_tab(
        self,
    ) -> QWidget:  # ... (method remains unchanged) ...
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        ccc_buttons_layout = QHBoxLayout()
        ccc_buttons_layout.setSpacing(10)
        self.add_ccc_category_button = QPushButton("➕ Add Category (L1)")
        self.add_ccc_category_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=True)
        )
        self.add_ccc_category_button.setToolTip("Add a new top-level category.")
        self.add_ccc_category_button.clicked.connect(self._add_new_main_category)
        ccc_buttons_layout.addWidget(self.add_ccc_category_button)
        self.add_ccc_process_button = QPushButton("➕ Add Process (L2)")
        self.add_ccc_process_button.setStyleSheet(
            self._get_crud_button_style(is_add_button_specific_style=True)
        )
        self.add_ccc_process_button.setToolTip(
            "Add a new process under the selected Level 1 Category."
        )
        self.add_ccc_process_button.clicked.connect(self._add_new_process_to_selected)
        self.add_ccc_process_button.setEnabled(False)
        ccc_buttons_layout.addWidget(self.add_ccc_process_button)
        self.edit_ccc_button = QPushButton("Edit Selected")
        self.edit_ccc_button.setStyleSheet(self._get_crud_button_style())
        self.edit_ccc_button.setToolTip(
            "Edit the name or status of the selected Category/Process."
        )
        self.edit_ccc_button.clicked.connect(self._edit_selected_ccc)
        self.edit_ccc_button.setEnabled(False)
        ccc_buttons_layout.addWidget(self.edit_ccc_button)
        self.toggle_ccc_status_button = QPushButton("Toggle Active Status")
        self.toggle_ccc_status_button.setStyleSheet(
            self._get_crud_button_style("default")
        )
        self.toggle_ccc_status_button.setToolTip(
            "Toggle the active/inactive status of the selected Category/Process."
        )
        self.toggle_ccc_status_button.clicked.connect(self._toggle_selected_ccc_status)
        self.toggle_ccc_status_button.setEnabled(False)
        ccc_buttons_layout.addWidget(self.toggle_ccc_status_button)
        self.delete_ccc_button = QPushButton("Delete Selected")
        self.delete_ccc_button.setStyleSheet(self._get_crud_button_style("delete"))
        self.delete_ccc_button.setToolTip(
            "Delete the selected Category/Process (if not in use)."
        )
        self.delete_ccc_button.clicked.connect(self._delete_selected_ccc)
        self.delete_ccc_button.setEnabled(False)
        ccc_buttons_layout.addWidget(self.delete_ccc_button)
        ccc_buttons_layout.addStretch()
        main_layout.addLayout(ccc_buttons_layout)
        ccc_filter_layout = QHBoxLayout()
        ccc_filter_label = QLabel("Show:")
        ccc_filter_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-right: 5px;"
        )
        self.ccc_active_radio = QRadioButton("Active")
        self.ccc_inactive_radio = QRadioButton("Inactive")
        self.ccc_all_radio = QRadioButton("All")
        self.ccc_filter_button_group = QButtonGroup(self)
        self.ccc_filter_button_group.addButton(self.ccc_active_radio)
        self.ccc_filter_button_group.addButton(self.ccc_inactive_radio)
        self.ccc_filter_button_group.addButton(self.ccc_all_radio)
        self.ccc_active_radio.setChecked(True)
        radio_style = f"QRadioButton {{ color: {DARK_TEXT_SECONDARY}; }}"
        for radio in [
            self.ccc_active_radio,
            self.ccc_inactive_radio,
            self.ccc_all_radio,
        ]:
            if radio:
                radio.setStyleSheet(radio_style)
                radio.toggled.connect(self._on_ccc_filter_changed)
                ccc_filter_layout.addWidget(radio)
        ccc_filter_layout.addStretch()
        main_layout.addLayout(ccc_filter_layout)
        tree_label = QLabel("Manage Categories & Processes:")
        tree_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 5px;"
        )
        main_layout.addWidget(tree_label)
        self.charge_code_categories_tree = QTreeWidget()
        self.charge_code_categories_tree.setColumnCount(3)
        self.charge_code_categories_tree.setHeaderLabels(["Name", "Level", "Status"])
        self.charge_code_categories_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.charge_code_categories_tree.setStyleSheet(
            f"QTreeWidget {{ border: 1px solid {DARK_BORDER}; border-radius: 4px; background-color: {DARK_WIDGET_BACKGROUND}; }} QTreeWidget::item:selected {{ background-color: {QColor(DARK_PRIMARY_ACTION).lighter(130).name()}; color: {DARK_TEXT_PRIMARY}; }} QHeaderView::section {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_SECONDARY}; padding: 4px; border: 1px solid {DARK_BORDER}; font-weight: bold; }}"
        )
        self.charge_code_categories_tree.itemSelectionChanged.connect(
            self._on_ccc_tree_item_selected
        )
        main_layout.addWidget(self.charge_code_categories_tree)
        self._update_ccc_buttons_state()
        return tab_widget

    def _create_charge_codes_tab(
        self,
    ) -> QWidget:  # ... (method remains unchanged from v1.12.28) ...
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
        if self.delete_charge_code_button:
            self.delete_charge_code_button.setText("Toggle Active Status")
            self.delete_charge_code_button.setToolTip(
                "Toggle the active/inactive status of the selected charge code"
            )
        main_layout.addLayout(buttons_layout)
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Show:")
        filter_label.setStyleSheet(f"color: {DARK_TEXT_SECONDARY}; margin-right: 5px;")
        self.cc_active_radio = QRadioButton("Active")
        self.cc_inactive_radio = QRadioButton("Inactive")
        self.cc_all_radio = QRadioButton("All")
        self.cc_filter_button_group = QButtonGroup(self)
        self.cc_filter_button_group.addButton(self.cc_active_radio)
        self.cc_filter_button_group.addButton(self.cc_inactive_radio)
        self.cc_filter_button_group.addButton(self.cc_all_radio)
        self.cc_active_radio.setChecked(True)
        radio_style = f"QRadioButton {{ color: {DARK_TEXT_SECONDARY}; }}"
        for radio in [self.cc_active_radio, self.cc_inactive_radio, self.cc_all_radio]:
            if radio:
                radio.setStyleSheet(radio_style)
                radio.toggled.connect(self._on_charge_code_filter_changed)
                filter_layout.addWidget(radio)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        current_items_label = QLabel("Managed Charge Codes:")
        current_items_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; padding-top: 5px;"
        )
        main_layout.addWidget(current_items_label)
        self.charge_codes_table = QTableWidget()
        self.charge_codes_table.setColumnCount(6)
        self.charge_codes_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Alternate Code",
                "Category",
                "Description",
                "Std. Price",
                "Active",
            ]
        )
        self.charge_codes_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.charge_codes_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        header = self.charge_codes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        selected_bg_color = QColor(DARK_PRIMARY_ACTION).lighter(130).name()
        text_color = DARK_TEXT_PRIMARY
        self.charge_codes_table.setStyleSheet(
            f"QTableWidget::item:selected {{ background-color: {selected_bg_color}; color: {text_color}; }}"
        )
        self.charge_codes_table.itemSelectionChanged.connect(
            self._on_charge_code_selected
        )
        main_layout.addWidget(self.charge_codes_table)
        return tab_widget

    @Slot()
    def _on_charge_code_filter_changed(self):  # ... (method remains unchanged) ...
        sender = self.sender()
        if sender and isinstance(sender, QRadioButton) and sender.isChecked():
            self.load_charge_codes_data()

    @Slot()
    def _on_ccc_filter_changed(self):  # ... (method remains unchanged) ...
        sender = self.sender()
        if sender and isinstance(sender, QRadioButton) and sender.isChecked():
            self.load_charge_code_categories_data()

    def _create_owners_tab(self) -> QWidget:  # ... (method remains unchanged) ...
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
        if self.add_owner_button:
            self.add_owner_button.setEnabled(True)
        if self.edit_owner_button:
            self.edit_owner_button.setEnabled(True)
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
        header = self.owners_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        selected_bg_color = QColor(DARK_PRIMARY_ACTION).lighter(130).name()
        self.owners_table.setStyleSheet(
            f"QTableWidget::item:selected {{ background-color: {selected_bg_color}; color: {DARK_TEXT_PRIMARY}; }}"
        )
        self.owners_table.itemSelectionChanged.connect(self._on_master_owner_selected)
        main_layout.addWidget(self.owners_table)
        return tab_widget

    def _update_crud_button_states(self):  # ... (method remains unchanged) ...
        current_tab_index = (
            self.main_tab_widget.currentIndex() if self.main_tab_widget else -1
        )
        current_tab_text = (
            self.main_tab_widget.tabText(current_tab_index)
            if self.main_tab_widget
            else ""
        )
        user_selected = self.current_selected_user_id is not None
        location_selected = self.current_selected_location_id is not None
        charge_code_selected = self.current_selected_charge_code_id is not None
        owner_selected = self.current_selected_owner_id is not None
        is_users_tab = "Manage Users" in current_tab_text
        is_locations_tab = "Manage Locations" in current_tab_text
        is_charge_codes_tab = "Manage Charge Codes" in current_tab_text
        is_owners_tab = "Manage Owner List" in current_tab_text
        is_ccc_tab = "Manage Categories/Processes" in current_tab_text
        if self.add_user_button:
            self.add_user_button.setEnabled(is_users_tab)
        if self.edit_user_button:
            self.edit_user_button.setEnabled(is_users_tab and user_selected)
        if self.delete_user_button:
            self.delete_user_button.setEnabled(is_users_tab and user_selected)
        if self.add_location_button:
            self.add_location_button.setEnabled(is_locations_tab)
        if self.edit_location_button:
            self.edit_location_button.setEnabled(is_locations_tab and location_selected)
        if self.delete_location_button:
            self.delete_location_button.setEnabled(
                is_locations_tab and location_selected
            )
        if self.add_charge_code_button:
            self.add_charge_code_button.setEnabled(is_charge_codes_tab)
        if self.edit_charge_code_button:
            self.edit_charge_code_button.setEnabled(
                is_charge_codes_tab and charge_code_selected
            )
        if self.delete_charge_code_button:
            self.delete_charge_code_button.setEnabled(
                is_charge_codes_tab and charge_code_selected
            )
        if self.add_owner_button:
            self.add_owner_button.setEnabled(is_owners_tab)
        if self.edit_owner_button:
            self.edit_owner_button.setEnabled(is_owners_tab and owner_selected)
        if self.delete_owner_button:
            self.delete_owner_button.setEnabled(is_owners_tab and owner_selected)
        self._update_ccc_buttons_state(is_active_tab=is_ccc_tab)

    def load_all_data(self):  # ... (method remains unchanged) ...
        self.logger.info(
            "UserManagementScreen: Loading initial data for the first tab."
        )
        if self.main_tab_widget and self.main_tab_widget.count() > 0:
            self._on_tab_changed(self.main_tab_widget.currentIndex())
        else:
            self.logger.warning(
                "load_all_data: main_tab_widget not ready or has no tabs."
            )
        self.update_status("User Management Ready.")

    def load_users_data(self):  # ... (method remains unchanged) ...
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

    def load_locations_data(self):  # ... (method remains unchanged) ...
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

    def load_charge_codes_data(self):  # MODIFIED for new column order
        self.logger.info("Loading charge codes data for tab...")
        if not self.charge_codes_table:
            self.logger.warning("Charge codes table not ready.")
            return
        status_filter = "all"
        if self.cc_active_radio and self.cc_active_radio.isChecked():
            status_filter = "active"
        elif self.cc_inactive_radio and self.cc_inactive_radio.isChecked():
            status_filter = "inactive"
        self.logger.info(f"Charge code status filter: {status_filter}")
        try:
            ccs = self.charge_code_controller.get_all_charge_codes(
                status_filter=status_filter
            )
            self.charge_codes_table.setRowCount(0)
            self.charge_codes_table.setSortingEnabled(False)
            for r, c_obj in enumerate(ccs):
                self.charge_codes_table.insertRow(r)
                # New column order: Code (0), Alternate Code (1), Category (2), Description (3), Std. Price (4), Active (5)
                self.charge_codes_table.setItem(r, 0, QTableWidgetItem(c_obj.code))
                self.charge_codes_table.item(r, 0).setData(
                    Qt.ItemDataRole.UserRole, c_obj.charge_code_id
                )
                self.charge_codes_table.setItem(
                    r, 1, QTableWidgetItem(c_obj.alternate_code or "")
                )

                category_display_text = "N/A"
                if c_obj.category_id is not None:
                    if self.charge_code_controller:
                        path_objects = self.charge_code_controller.get_category_path(
                            c_obj.category_id
                        )
                        if path_objects:
                            category_display_text = " > ".join(
                                cat.name
                                for cat in path_objects
                                if cat and hasattr(cat, "name")
                            )
                        else:
                            if c_obj.category and hasattr(c_obj.category, "name"):
                                category_display_text = c_obj.category.name
                                self.logger.warning(
                                    f"Could not get category path for Charge Code '{c_obj.code}' (ID {c_obj.category_id}), using direct name: {category_display_text}"
                                )
                            else:
                                category_display_text = (
                                    f"Error: Cat. ID {c_obj.category_id} unresolvable"
                                )
                    else:
                        category_display_text = "Error: Controller missing"
                elif c_obj.category and hasattr(c_obj.category, "name"):
                    category_display_text = c_obj.category.name
                    self.logger.warning(
                        f"Charge Code '{c_obj.code}' has no category_id but category object '{c_obj.category.name}' exists."
                    )
                self.charge_codes_table.setItem(
                    r, 2, QTableWidgetItem(category_display_text)
                )

                self.charge_codes_table.setItem(
                    r, 3, QTableWidgetItem(c_obj.description or "")
                )
                self.charge_codes_table.setItem(
                    r,
                    4,
                    QTableWidgetItem(
                        f"{c_obj.standard_charge:.2f}"
                        if c_obj.standard_charge is not None
                        else "0.00"
                    ),
                )
                self.charge_codes_table.setItem(
                    r, 5, QTableWidgetItem("Yes" if c_obj.is_active else "No")
                )

            self.charge_codes_table.setSortingEnabled(True)
            self.charge_codes_table.resizeColumnsToContents()
            self.charge_codes_table.setColumnWidth(0, 75)  # Code
            # Column 1 (Alternate Code) is ResizeToContents
            # Column 2 (Category) is Stretch
            self.charge_codes_table.setColumnWidth(3, 250)  # Description
            # Column 4 (Std. Price) and 5 (Active) are ResizeToContents

            self.logger.info(f"Loaded {len(ccs)} charge codes.")
        except Exception as e:
            self.logger.error(f"Error loading charge codes: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load charge codes: {e}")
        self.current_selected_charge_code_id = None
        self._update_crud_button_states()

    def load_master_owners_data(self):  # ... (method remains unchanged) ...
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
            self.owners_table.resizeColumnsToContents()
            self.owners_table.setColumnWidth(0, 120)
            self.owners_table.setColumnWidth(2, 150)
            self.logger.info(f"Loaded {len(owners)} master owners.")
        except Exception as e:
            self.logger.error(f"Error loading master owners: {e}", exc_info=True)
            self.show_error("Load Error", f"Could not load master owners: {e}")
        self.current_selected_owner_id = None
        self._update_crud_button_states()

    # --- Slot Methods (existing ones remain unchanged, new ones for CCC below) ---
    @Slot()
    def _on_user_selected(self):  # ... (method remains unchanged) ...
        self.current_selected_user_id = None
        if self.users_list_widget and self.users_list_widget.currentItem():
            self.current_selected_user_id = self.users_list_widget.currentItem().data(
                Qt.ItemDataRole.UserRole
            )
        self.logger.info(f"User selected from list: {self.current_selected_user_id}")
        self._update_crud_button_states()

    @Slot()
    def _add_new_user(self):  # ... (method remains unchanged) ...
        dialog = AddEditUserDialog(
            parent_view=self,
            user_controller=self.user_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_users_data()
            self.update_status("User added successfully.")

    @Slot()
    def _edit_selected_user(self):  # ... (method remains unchanged) ...
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
        )
        if dialog.exec():
            self.load_users_data()
            self.update_status(f"User '{user_to_edit.user_id}' updated.")
            self._try_reselect_item(
                self.users_list_widget, self.current_selected_user_id
            )

    @Slot()
    def _delete_selected_user(self):  # ... (method remains unchanged) ...
        self._generic_delete_action(
            self.current_selected_user_id,
            "User",
            self.user_controller.delete_user_permanently,
            self.load_users_data,
            "current_selected_user_id",
            self.users_list_widget,
        )

    @Slot()
    def _on_location_selected(self):  # Fixed in v1.12.22
        self.current_selected_location_id = None
        item = None
        current_row = -1
        if self.locations_table and self.locations_table.selectedItems():
            current_row = self.locations_table.currentRow()
            if current_row >= 0:  # Correctly indented
                item = self.locations_table.item(current_row, 0)
        if item:
            self.current_selected_location_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(
            f"Location selected (row: {current_row}): {self.current_selected_location_id}"
        )
        self._update_crud_button_states()

    @Slot()
    def _add_new_location(self):  # ... (method remains unchanged) ...
        dialog = AddEditLocationDialog(
            parent_view=self,
            controller=self.location_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_locations_data()
            self.update_status("Location added.")

    @Slot()
    def _edit_selected_location(self):  # ... (method remains unchanged) ...
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
    def _delete_selected_location(self):  # ... (method remains unchanged) ...
        self._generic_delete_action(
            self.current_selected_location_id,
            "Location",
            self.location_controller.delete_location,
            self.load_locations_data,
            "current_selected_location_id",
            self.locations_table,
        )

    @Slot()
    def _on_charge_code_selected(self):  # ... (method remains unchanged) ...
        self.current_selected_charge_code_id = None
        item = None
        if self.charge_codes_table and self.charge_codes_table.selectedItems():
            current_row = self.charge_codes_table.currentRow()
            if current_row >= 0 and (
                item := self.charge_codes_table.item(current_row, 0)
            ):
                self.current_selected_charge_code_id = item.data(
                    Qt.ItemDataRole.UserRole
                )
        self.logger.info(
            f"Charge Code selected: {self.current_selected_charge_code_id}"
        )
        self._update_crud_button_states()

    @Slot()
    def _add_new_charge_code(self):  # ... (method remains unchanged) ...
        dialog = AddEditChargeCodeDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_charge_codes_data()
            self.update_status("Charge code added.")

    @Slot()
    def _edit_selected_charge_code(self):  # ... (method remains unchanged) ...
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
        )
        if dialog.exec():
            self.load_charge_codes_data()
            self.update_status(f"Charge code '{cc_to_edit.code}' updated.")
            self._try_reselect_item(
                self.charge_codes_table, self.current_selected_charge_code_id
            )

    @Slot()
    def _delete_selected_charge_code(self):  # ... (method remains unchanged) ...
        self._generic_delete_action(
            self.current_selected_charge_code_id,
            "Charge Code",
            self.charge_code_controller.toggle_charge_code_status,
            self.load_charge_codes_data,
            "current_selected_charge_code_id",
            self.charge_codes_table,
        )

    @Slot()
    def _on_master_owner_selected(self):  # ... (method remains unchanged) ...
        self.current_selected_owner_id = None
        item = None
        current_row = -1
        if self.owners_table and self.owners_table.selectedItems():
            current_row = self.owners_table.currentRow()
            if current_row >= 0:
                item = self.owners_table.item(current_row, 0)
        if item:
            self.current_selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
        self.logger.info(
            f"Master Owner selected (row: {current_row}): {self.current_selected_owner_id}"
        )
        self._update_crud_button_states()

    @Slot()
    def _add_new_owner(self):  # ... (method remains unchanged) ...
        dialog = AddEditOwnerDialog(
            parent_view=self,
            owner_controller=self.owner_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_master_owners_data()
            self.update_status("Owner added successfully.")

    @Slot()
    def _edit_selected_owner(self):  # ... (method remains unchanged) ...
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
            self.load_master_owners_data()
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
    def _delete_selected_owner(self):  # ... (method remains unchanged) ...
        self._generic_delete_action(
            self.current_selected_owner_id,
            "Master Owner",
            self.owner_controller.delete_master_owner,
            self.load_master_owners_data,
            "current_selected_owner_id",
            self.owners_table,
        )

    # --- Charge Code Category/Process Management Methods ---
    def load_charge_code_categories_data(
        self,
    ):  # ... (method remains unchanged from v1.12.26) ...
        self.logger.info("Loading charge code categories/processes data...")
        if not self.charge_code_categories_tree or not self.charge_code_controller:
            self.logger.warning("Charge code categories tree or controller not ready.")
            return
        self.charge_code_categories_tree.clear()
        active_filter = "all"
        if self.ccc_active_radio and self.ccc_active_radio.isChecked():
            active_filter = "active"
        elif self.ccc_inactive_radio and self.ccc_inactive_radio.isChecked():
            active_filter = "inactive"
        self.logger.info(f"CCC active_filter: {active_filter}")
        try:
            all_l1_categories = (
                self.charge_code_controller.get_all_charge_code_categories_hierarchical()
            )
            displayed_l1_count = 0
            for l1_cat in all_l1_categories:
                l1_is_active = l1_cat.is_active
                children_of_l1_to_display = []
                has_any_child_matching_filter = False
                if hasattr(l1_cat, "children") and l1_cat.children:
                    for l2_proc in l1_cat.children:
                        l2_is_active = l2_proc.is_active
                        child_matches_filter = False
                        if active_filter == "all":
                            child_matches_filter = True
                        elif active_filter == "active" and l2_is_active:
                            child_matches_filter = True
                        elif active_filter == "inactive" and not l2_is_active:
                            child_matches_filter = True
                        if child_matches_filter:
                            children_of_l1_to_display.append(l2_proc)
                            has_any_child_matching_filter = True
                show_this_l1_item = False
                if active_filter == "all":
                    show_this_l1_item = True
                elif active_filter == "active":
                    show_this_l1_item = l1_is_active
                elif active_filter == "inactive":
                    show_this_l1_item = (not l1_is_active) or (
                        l1_is_active and has_any_child_matching_filter
                    )
                if show_this_l1_item:
                    displayed_l1_count += 1
                    l1_item_tree_node = QTreeWidgetItem(
                        self.charge_code_categories_tree
                    )
                    l1_item_tree_node.setText(0, l1_cat.name)
                    l1_item_tree_node.setText(1, str(l1_cat.level))
                    l1_item_tree_node.setText(
                        2, "Active" if l1_cat.is_active else "Inactive"
                    )
                    l1_item_tree_node.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        {"id": l1_cat.category_id, "level": 1, "obj": l1_cat},
                    )
                    for l2_proc_to_display in sorted(
                        children_of_l1_to_display, key=lambda x: x.name
                    ):
                        l2_item_tree_node_child = QTreeWidgetItem(l1_item_tree_node)
                        l2_item_tree_node_child.setText(0, l2_proc_to_display.name)
                        l2_item_tree_node_child.setText(
                            1, str(l2_proc_to_display.level)
                        )
                        l2_item_tree_node_child.setText(
                            2, "Active" if l2_proc_to_display.is_active else "Inactive"
                        )
                        l2_item_tree_node_child.setData(
                            0,
                            Qt.ItemDataRole.UserRole,
                            {
                                "id": l2_proc_to_display.category_id,
                                "level": 2,
                                "obj": l2_proc_to_display,
                            },
                        )
                    l1_item_tree_node.setExpanded(True)
            self.charge_code_categories_tree.resizeColumnToContents(0)
            self.charge_code_categories_tree.resizeColumnToContents(1)
            self.charge_code_categories_tree.resizeColumnToContents(2)
            self.logger.info(
                f"Displayed {displayed_l1_count} top-level categories in tree based on filter '{active_filter}'."
            )
        except Exception as e:
            self.logger.error(
                f"Error loading charge code categories into tree: {e}", exc_info=True
            )
            self.show_error("Load Error", f"Could not load categories/processes: {e}")
        self.current_selected_ccc_id = None
        self.current_selected_ccc_level = None
        self.current_selected_ccc_object = None
        self._update_ccc_buttons_state()

    @Slot()
    def _on_ccc_tree_item_selected(self):  # ... (method remains unchanged) ...
        self.current_selected_ccc_id = None
        self.current_selected_ccc_level = None
        self.current_selected_ccc_object = None
        selected_items = (
            self.charge_code_categories_tree.selectedItems()
            if self.charge_code_categories_tree
            else []
        )
        if selected_items:
            item_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if isinstance(item_data, dict):
                self.current_selected_ccc_id = item_data.get("id")
                self.current_selected_ccc_level = item_data.get("level")
                self.current_selected_ccc_object = item_data.get("obj")
                self.logger.info(
                    f"CCC selected: ID={self.current_selected_ccc_id}, Level={self.current_selected_ccc_level}, Name='{selected_items[0].text(0)}'"
                )
        else:
            self.logger.info("CCC selection cleared.")
        self._update_ccc_buttons_state()

    def _update_ccc_buttons_state(
        self, is_active_tab: bool = True
    ):  # ... (method remains unchanged) ...
        if not self.charge_code_categories_tree:
            return
        item_selected = self.current_selected_ccc_id is not None
        is_level1_selected = item_selected and self.current_selected_ccc_level == 1
        ccc_tab_is_current = False
        if self.main_tab_widget and self.main_tab_widget.currentWidget():
            current_widget_title = self.main_tab_widget.tabText(
                self.main_tab_widget.currentIndex()
            )
            if "Manage Categories/Processes" in current_widget_title:
                ccc_tab_is_current = True
        effective_enable = is_active_tab and ccc_tab_is_current
        if self.add_ccc_category_button:
            self.add_ccc_category_button.setEnabled(effective_enable)
        if self.add_ccc_process_button:
            self.add_ccc_process_button.setEnabled(
                effective_enable and is_level1_selected
            )
        if self.edit_ccc_button:
            self.edit_ccc_button.setEnabled(effective_enable and item_selected)
        if self.toggle_ccc_status_button:
            self.toggle_ccc_status_button.setEnabled(effective_enable and item_selected)
        if self.delete_ccc_button:
            self.delete_ccc_button.setEnabled(effective_enable and item_selected)
        if not effective_enable:
            if self.add_ccc_category_button:
                self.add_ccc_category_button.setEnabled(False)
            if self.add_ccc_process_button:
                self.add_ccc_process_button.setEnabled(False)
            if self.edit_ccc_button:
                self.edit_ccc_button.setEnabled(False)
            if self.toggle_ccc_status_button:
                self.toggle_ccc_status_button.setEnabled(False)
            if self.delete_ccc_button:
                self.delete_ccc_button.setEnabled(False)

    @Slot()
    def _add_new_main_category(self):  # ... (method remains unchanged) ...
        dialog = AddEditChargeCodeCategoryDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
        )
        if dialog.exec():
            self.load_charge_code_categories_data()
            self.update_status("New Category (Level 1) added.")

    @Slot()
    def _add_new_process_to_selected(self):  # ... (method remains unchanged) ...
        if not self.current_selected_ccc_object or self.current_selected_ccc_level != 1:
            self.show_warning(
                "Add Process", "Select a Level 1 Category to add a Process under."
            )
            return
        parent_category_name = self.current_selected_ccc_object.name
        dialog = AddEditChargeCodeCategoryDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            parent_category=self.current_selected_ccc_object,
        )
        if dialog.exec():
            self.load_charge_code_categories_data()
            self.update_status(f"New Process added under '{parent_category_name}'.")

    @Slot()
    def _edit_selected_ccc(self):  # ... (method remains unchanged) ...
        if not self.current_selected_ccc_object:
            self.show_warning("Edit", "Select a Category or Process to edit.")
            return
        dialog = AddEditChargeCodeCategoryDialog(
            parent=self,
            controller=self.charge_code_controller,
            current_user_id=self.current_user_id,
            category_to_edit=self.current_selected_ccc_object,
        )
        if dialog.exec():
            self.load_charge_code_categories_data()
            item_type = (
                "Process" if self.current_selected_ccc_level == 2 else "Category"
            )
            self.update_status(f"{item_type} updated.")

    @Slot()
    def _toggle_selected_ccc_status(
        self,
    ):  # ... (method remains unchanged from v1.12.26) ...
        if not self.current_selected_ccc_object:
            self.show_warning("Toggle Status", "Please select a Category or Process.")
            return
        ccc = self.current_selected_ccc_object
        new_status = not ccc.is_active
        action_verb = "activate" if new_status else "deactivate"
        item_type = "Process" if ccc.level == 2 else "Category"
        if self.show_question(
            "Confirm Status Change",
            f"Are you sure you want to {action_verb} the {item_type} '{ccc.name}'?",
        ):
            success, message = (
                self.charge_code_controller.toggle_charge_code_category_status(
                    ccc.category_id, self.current_user_id
                )
            )
            if success:
                self.load_charge_code_categories_data()
                self.update_status(message)
            else:
                self.show_error("Error", message)

    @Slot()
    def _delete_selected_ccc(self):  # ... (method remains unchanged) ...
        if not self.current_selected_ccc_object:
            self.show_warning("Delete", "Select a Category or Process to delete.")
            return
        ccc = self.current_selected_ccc_object
        item_type = "Process" if ccc.level == 2 else "Category"
        if self.show_question(
            "Confirm Delete",
            f"Are you sure you want to delete the {item_type} '{ccc.name}'? This cannot be undone.",
        ):
            success, message = self.charge_code_controller.delete_charge_code_category(
                ccc.category_id, self.current_user_id
            )
            if success:
                self.load_charge_code_categories_data()
                self.update_status(message)
            else:
                self.show_error("Delete Failed", message)

    def _try_reselect_item(
        self, list_or_table_widget, item_id_to_select
    ):  # ... (method remains unchanged) ...
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
                    (
                        self._on_user_selected()
                        if list_or_table_widget == self.users_list_widget
                        else None
                    )
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

    def _generic_delete_action(
        self,
        item_id,
        item_name_singular: str,
        controller_delete_method,
        load_data_method,
        current_selection_attr: str,
        list_or_table_widget,
    ):  # ... (method remains unchanged) ...
        if not item_id:
            self.show_warning(
                f"Action required",
                f"Please select a {item_name_singular.lower()} to action.",
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
            name_col_idx = 0
            if item_name_singular == "Master Owner":
                name_col_idx = 1
            elif item_name_singular == "Location":
                name_col_idx = 0
            id_item = list_or_table_widget.item(current_row, 0)
            id_val = (
                str(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else str(item_id)
            )
            name_val_item = list_or_table_widget.item(
                current_row, name_col_idx if item_name_singular != "Charge Code" else 0
            )
            name_val = name_val_item.text() if name_val_item else ""
            if (
                item_name_singular == "Charge Code"
                and not name_val
                and list_or_table_widget.columnCount() > 1
            ):
                desc_item = list_or_table_widget.item(current_row, 1)
                name_val = desc_item.text() if desc_item else ""
            item_repr = (
                f"{item_name_singular} '{name_val}' (ID: {id_val})"
                if name_val
                else f"{item_name_singular} (ID: {id_val})"
            )
        confirm_dialog_title = f"Confirm Action"
        confirm_action_text = f"permanently delete {item_repr}"
        if (
            item_name_singular == "Charge Code"
            and controller_delete_method
            == self.charge_code_controller.toggle_charge_code_status
        ):
            confirm_action_text = f"toggle the active/inactive status for {item_repr}"
        if self.show_question(
            confirm_dialog_title, f"Are you sure you want to {confirm_action_text}?"
        ):
            try:
                success, message = controller_delete_method(
                    item_id, self.current_user_id
                )
                if success:
                    self.update_status(message)
                    load_data_method()
                    setattr(self, current_selection_attr, None)
                else:
                    self.show_error(f"{item_name_singular} Action Failed", message)
            except Exception as e:
                self.logger.error(
                    f"Error actioning {item_name_singular.lower()} ID {item_id}: {e}",
                    exc_info=True,
                )
                self.show_error("Operation Error", f"An unexpected error occurred: {e}")
        self._update_crud_button_states()

    def closeEvent(self, event: QCloseEvent):  # ... (method remains unchanged) ...
        self.logger.info("User Management screen closing.")
        super().closeEvent(event)
