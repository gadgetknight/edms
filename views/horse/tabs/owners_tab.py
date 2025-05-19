# views/horse/tabs/owners_tab.py

"""
EDSI Veterinary Management System - Horse Owners Tab
Version: 1.0.1
Purpose: Provides a tab widget for managing horse-owner associations.
         Corrects QListWidgetItem instantiation.
Last Updated: May 17, 2025
Author: Claude Assistant

Changelog:
- v1.0.1 (2025-05-17):
    - Corrected item creation in `load_owners_for_horse` to use `QListWidgetItem(text)`.
- v1.0.0 (2025-05-17):
    - Initial extraction from horse_unified_management.py.
"""

import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QDoubleSpinBox,
    QMessageBox,
    QDialog,
    QListWidgetItem,  # Added QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

from config.app_config import AppConfig
from models import Horse
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController

from ..dialogs.create_link_owner_dialog import CreateAndLinkOwnerDialog
from ..dialogs.link_existing_owner_dialog import LinkExistingOwnerDialog
from ..widgets.horse_owner_list_widget import HorseOwnerListWidget


class OwnersTab(QWidget):
    """Tab widget for managing horse-owner associations."""

    owner_association_changed = Signal(str)

    def __init__(
        self,
        parent_view,
        horse_controller: HorseController,
        owner_controller: OwnerController,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.owner_controller = owner_controller

        self.current_horse: Optional[Horse] = None
        self.current_horse_owners: List[Dict] = []
        self.selected_horse_owner_id: Optional[int] = None

        self.setStyleSheet(f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self._setup_ui(main_layout)
        self._setup_connections()
        self.update_buttons_state()

    def _get_generic_button_style(self):
        if hasattr(self.parent_view, "get_generic_button_style"):
            return self.parent_view.get_generic_button_style()
        return f"QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; padding: 5px; }}"

    def _get_input_style(self):
        if hasattr(self.parent_view, "get_form_input_style"):
            return self.parent_view.get_form_input_style()
        return f"QDoubleSpinBox {{ background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; padding: 5px; }}"

    def _setup_ui(self, main_layout: QVBoxLayout):
        owners_action_layout = QHBoxLayout()
        self.create_link_owner_btn = QPushButton("➕ Create New & Link")
        self.link_existing_owner_btn = QPushButton("🔗 Link Existing")
        self.remove_horse_owner_btn = QPushButton("➖ Remove Selected Owner")

        button_style = self._get_generic_button_style()
        create_link_style = button_style.replace(
            AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
        )
        self.create_link_owner_btn.setStyleSheet(
            create_link_style.replace(
                f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white;"
            )
        )
        self.link_existing_owner_btn.setStyleSheet(
            button_style.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
            )
        )
        remove_owner_style = button_style.replace(
            AppConfig.DARK_BUTTON_BG, AppConfig.DARK_DANGER_ACTION
        ).replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white;")
        self.remove_horse_owner_btn.setStyleSheet(remove_owner_style)

        owners_action_layout.addWidget(self.create_link_owner_btn)
        owners_action_layout.addWidget(self.link_existing_owner_btn)
        owners_action_layout.addWidget(self.remove_horse_owner_btn)
        owners_action_layout.addStretch()
        main_layout.addLayout(owners_action_layout)

        self.current_owners_list_widget = HorseOwnerListWidget()

        owners_list_label = QLabel("Current Owners & Percentages:")
        owners_list_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; background: transparent; margin-bottom: 5px; font-weight: bold;"
        )
        main_layout.addWidget(owners_list_label)
        main_layout.addWidget(self.current_owners_list_widget, 1)

        self.percentage_edit_frame = QFrame()
        self.percentage_edit_frame.setStyleSheet("background-color: transparent;")
        percentage_edit_layout = QHBoxLayout(self.percentage_edit_frame)
        percentage_edit_layout.setContentsMargins(0, 5, 0, 0)

        self.selected_owner_for_pct_label = QLabel("Edit % for:")
        self.selected_owner_for_pct_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY};"
        )

        self.edit_owner_percentage_spinbox = QDoubleSpinBox()
        self.edit_owner_percentage_spinbox.setRange(0.00, 100.00)
        self.edit_owner_percentage_spinbox.setDecimals(2)
        self.edit_owner_percentage_spinbox.setSuffix(" %")
        self.edit_owner_percentage_spinbox.setStyleSheet(self._get_input_style())

        self.save_owner_percentage_btn = QPushButton("💾 Save %")
        self.save_owner_percentage_btn.setStyleSheet(
            self._get_generic_button_style().replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
            )
        )

        percentage_edit_layout.addWidget(self.selected_owner_for_pct_label)
        percentage_edit_layout.addWidget(self.edit_owner_percentage_spinbox)
        percentage_edit_layout.addWidget(self.save_owner_percentage_btn)
        percentage_edit_layout.addStretch()
        main_layout.addWidget(self.percentage_edit_frame)
        self.percentage_edit_frame.hide()

    def _setup_connections(self):
        self.current_owners_list_widget.itemSelectionChanged.connect(
            self._on_horse_owner_selection_changed
        )
        self.create_link_owner_btn.clicked.connect(self._handle_create_and_link_owner)
        self.link_existing_owner_btn.clicked.connect(self._handle_link_existing_owner)
        self.remove_horse_owner_btn.clicked.connect(
            self._handle_remove_owner_from_horse
        )
        self.save_owner_percentage_btn.clicked.connect(
            self._handle_save_owner_percentage
        )

    def load_owners_for_horse(self, horse: Optional[Horse]):
        self.current_horse = horse
        self.current_owners_list_widget.clear()
        self.selected_horse_owner_id = None
        self.current_horse_owners = []

        if self.current_horse and self.current_horse.horse_id is not None:
            self.logger.debug(
                f"Populating owners for horse ID {self.current_horse.horse_id}"
            )
            self.current_horse_owners = self.horse_controller.get_horse_owners(
                self.current_horse.horse_id
            )
            for owner_assoc_data in self.current_horse_owners:
                item_text = f"{owner_assoc_data['display_name']} - {owner_assoc_data['percentage']:.2f}%"
                # --- CORRECTED LINE ---
                list_item = QListWidgetItem(item_text)
                # --- END CORRECTION ---
                list_item.setData(
                    Qt.ItemDataRole.UserRole, owner_assoc_data["owner_id"]
                )
                self.current_owners_list_widget.addItem(list_item)
        else:
            self.logger.debug("No current horse or horse ID to load owners for.")

        self.percentage_edit_frame.hide()
        self.update_buttons_state()

    def _on_horse_owner_selection_changed(self):
        selected_items = self.current_owners_list_widget.selectedItems()
        if selected_items:
            self.selected_horse_owner_id = selected_items[0].data(
                Qt.ItemDataRole.UserRole
            )
            self.logger.info(
                f"Horse-owner association selected: Owner ID {self.selected_horse_owner_id}"
            )
            assoc_data = next(
                (
                    ho
                    for ho in self.current_horse_owners
                    if ho["owner_id"] == self.selected_horse_owner_id
                ),
                None,
            )
            if assoc_data:
                self.edit_owner_percentage_spinbox.setValue(assoc_data["percentage"])
                self.selected_owner_for_pct_label.setText(
                    f"Edit % for: {assoc_data['owner_name']}"
                )
                self.percentage_edit_frame.show()
            else:
                self.percentage_edit_frame.hide()
        else:
            self.selected_horse_owner_id = None
            self.percentage_edit_frame.hide()
            self.logger.info("Horse-owner association selection cleared.")
        self.update_buttons_state()

    def _handle_create_and_link_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Add Owner", "Please select a horse first.")
            return

        current_user_login = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "UnknownUser"
        )
        dialog = CreateAndLinkOwnerDialog(
            self.parent_view, self.current_horse.horse_name, current_user_login
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if (
                data
                and data.get("new_owner_object")
                and data.get("percentage") is not None
            ):
                new_owner_obj = data["new_owner_object"]
                percentage = data["percentage"]

                self.logger.info(
                    f"Attempting to link newly created owner ID {new_owner_obj.owner_id} to horse ID {self.current_horse.horse_id}"
                )
                success_link, msg_link = self.horse_controller.add_owner_to_horse(
                    self.current_horse.horse_id,
                    new_owner_obj.owner_id,
                    percentage,
                    current_user_login,
                )
                if success_link:
                    self.parent_view.show_info("Owner Linked", msg_link)
                    self.load_owners_for_horse(self.current_horse)
                    self.owner_association_changed.emit(msg_link)
                else:
                    self.parent_view.show_error("Failed to Link Owner", msg_link)
            else:
                self.logger.info(
                    "Create and link owner dialog cancelled or no valid data returned."
                )
        else:
            self.logger.info(
                "Create and link owner dialog cancelled by user (rejected)."
            )

    def _handle_link_existing_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Link Owner", "Please select a horse first.")
            return

        dialog = LinkExistingOwnerDialog(
            self.parent_view, self.current_horse.horse_name
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if (
                data
                and data.get("owner_id") is not None
                and data.get("percentage") is not None
            ):
                current_user_login = (
                    self.parent_view.current_user
                    if hasattr(self.parent_view, "current_user")
                    else "UnknownUser"
                )
                self.logger.info(
                    f"Attempting to link existing owner ID {data['owner_id']} with {data['percentage']}% to horse ID {self.current_horse.horse_id}"
                )
                success_link, msg_link = self.horse_controller.add_owner_to_horse(
                    self.current_horse.horse_id,
                    data["owner_id"],
                    data["percentage"],
                    current_user_login,
                )
                if success_link:
                    self.parent_view.show_info("Owner Linked", msg_link)
                    self.load_owners_for_horse(self.current_horse)
                    self.owner_association_changed.emit(msg_link)
                else:
                    self.parent_view.show_error("Failed to Link Owner", msg_link)
            else:
                self.logger.warning(
                    "No data or invalid data received from link existing owner dialog."
                )
        else:
            self.logger.info("Link existing owner dialog cancelled by user (rejected).")

    def _handle_remove_owner_from_horse(self):
        if not self.current_horse or self.selected_horse_owner_id is None:
            self.parent_view.show_warning(
                "Remove Owner", "Please select a horse and an owner from its list."
            )
            return

        owner_display_name = "Selected Owner"
        for owner_assoc in self.current_horse_owners:
            if owner_assoc["owner_id"] == self.selected_horse_owner_id:
                owner_display_name = owner_assoc["display_name"]
                break
        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )

        if self.parent_view.show_question(
            "Confirm Removal",
            f"Are you sure you want to remove owner '{owner_display_name}' from horse '{horse_name_display}'?",
        ):
            current_user_login = (
                self.parent_view.current_user
                if hasattr(self.parent_view, "current_user")
                else "UnknownUser"
            )
            self.logger.info(
                f"Attempting to remove owner ID {self.selected_horse_owner_id} from horse ID {self.current_horse.horse_id}"
            )
            success, message = self.horse_controller.remove_owner_from_horse(
                self.current_horse.horse_id,
                self.selected_horse_owner_id,
                current_user_login,
            )
            if success:
                self.parent_view.show_info("Owner Removed", message)
                self.load_owners_for_horse(self.current_horse)
                self.owner_association_changed.emit(message)
            else:
                self.parent_view.show_error("Failed to Remove Owner", message)
        else:
            self.logger.info("Owner removal cancelled by user.")

    def _handle_save_owner_percentage(self):
        if not self.current_horse or self.selected_horse_owner_id is None:
            self.parent_view.show_warning(
                "Save Percentage",
                "Please select a horse and an owner to update their percentage.",
            )
            return

        new_percentage = self.edit_owner_percentage_spinbox.value()
        if not (0 <= new_percentage <= 100):
            self.parent_view.show_error(
                "Invalid Percentage", "Ownership percentage must be between 0 and 100."
            )
            return

        current_user_login = (
            self.parent_view.current_user
            if hasattr(self.parent_view, "current_user")
            else "UnknownUser"
        )
        self.logger.info(
            f"Attempting to update percentage for owner ID {self.selected_horse_owner_id} on horse ID {self.current_horse.horse_id} to {new_percentage}%"
        )
        success, message = self.horse_controller.update_horse_owner_percentage(
            self.current_horse.horse_id,
            self.selected_horse_owner_id,
            new_percentage,
            current_user_login,
        )
        if success:
            self.parent_view.show_info("Percentage Updated", message)
            self.load_owners_for_horse(self.current_horse)
            self.owner_association_changed.emit(message)
        else:
            self.parent_view.show_error("Failed to Update Percentage", message)

    def update_buttons_state(self):
        is_horse_selected = self.current_horse is not None
        is_owner_in_list_selected = self.selected_horse_owner_id is not None

        self.create_link_owner_btn.setEnabled(is_horse_selected)
        self.link_existing_owner_btn.setEnabled(is_horse_selected)
        self.remove_horse_owner_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )
        self.save_owner_percentage_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )

        if not (is_horse_selected and is_owner_in_list_selected):
            self.percentage_edit_frame.hide()
        elif (
            self.percentage_edit_frame.isHidden()
            and is_horse_selected
            and is_owner_in_list_selected
        ):
            pass
