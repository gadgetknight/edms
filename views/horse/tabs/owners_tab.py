# views/horse/tabs/owners_tab.py
"""
EDSI Veterinary Management System - Horse Owners Tab
Version: 1.2.1
Purpose: Manages the association of owners with a specific horse, including
         linking existing owners, creating new owners and linking them,
         updating ownership percentages, and removing associations.
         Added detailed logging to _handle_create_and_link_owner.
Last Updated: May 19, 2025
Author: Claude Assistant (based on user's v1.2.0)

Changelog:
- v1.2.1 (2025-05-19):
    - Added detailed logging in `_handle_create_and_link_owner` to debug
      dialog execution result and data retrieval.
- v1.2.0 (2025-05-17) (User's Base Version):
    - Implemented full CRUD for horse-owner links.
    - Integrated CreateAndLinkOwnerDialog and LinkExistingOwnerDialog.
    - Handled ownership percentage updates and total validation.
- v1.1.0 (2025-05-16): Initial refactor of owner management into tab.
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
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_BUTTON_BG,
    DARK_TEXT_PRIMARY,
    DARK_BORDER,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_SUCCESS_ACTION,
    DARK_PRIMARY_ACTION,
    DARK_DANGER_ACTION,
    DARK_TEXT_SECONDARY,
    DARK_ITEM_HOVER,
)
from models import Horse, Owner as OwnerModel  # Added OwnerModel alias
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController

from ..dialogs.create_link_owner_dialog import CreateAndLinkOwnerDialog
from ..dialogs.link_existing_owner_dialog import LinkExistingOwnerDialog
from ..widgets.horse_owner_list_widget import HorseOwnerListWidget


class OwnersTab(QWidget):
    """Tab widget for managing horse-owner associations."""

    owner_association_changed = Signal(str)  # Emits a status message

    def __init__(
        self,
        parent_view,  # This is HorseUnifiedManagement
        horse_controller: HorseController,
        owner_controller: OwnerController,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.owner_controller = owner_controller

        self.current_horse: Optional[Horse] = None
        self.current_horse_owners_assoc: List[Dict] = (
            []
        )  # Stores dicts with owner_id, display_name, percentage
        self.selected_horse_owner_assoc_id: Optional[int] = (
            None  # owner_id from the association
        )

        # Get current_user_id from parent_view for auditing
        self.current_user_login = "UnknownUser"
        if (
            hasattr(self.parent_view, "current_user_id")
            and self.parent_view.current_user_id
        ):
            self.current_user_login = self.parent_view.current_user_id
        elif (
            hasattr(self.parent_view, "current_user") and self.parent_view.current_user
        ):  # Fallback if current_user is the ID string
            self.current_user_login = self.parent_view.current_user
        else:
            self.logger.warning(
                "Could not determine current_user_id from parent_view for OwnersTab auditing."
            )

        self.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self._setup_ui(main_layout)
        self._setup_connections()
        self.update_buttons_state()  # Initial state

    def _get_generic_button_style(self) -> str:
        """Returns a generic button style string using app config constants."""
        if hasattr(self.parent_view, "get_generic_button_style"):
            return self.parent_view.get_generic_button_style()
        # Fallback if parent_view doesn't have it (should not happen if BaseView is consistent)
        return (
            f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _get_input_style(self) -> str:
        """Returns an input field style string using app config constants."""
        if hasattr(self.parent_view, "get_form_input_style"):
            # Assuming parent_view's get_form_input_style is suitable for QDoubleSpinBox
            return self.parent_view.get_form_input_style()
        # Fallback
        return (
            f"QDoubleSpinBox {{ background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; padding: 5px; border-radius: 4px; }}"
        )

    def _setup_ui(self, main_layout: QVBoxLayout):
        # --- Action Buttons ---
        owners_action_layout = QHBoxLayout()
        self.create_link_owner_btn = QPushButton("➕ Create New & Link Owner")
        self.link_existing_owner_btn = QPushButton("🔗 Link Existing Owner")
        self.remove_horse_owner_btn = QPushButton("➖ Remove Selected Owner Link")

        button_style = self._get_generic_button_style()
        self.create_link_owner_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_SUCCESS_ACTION).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white;"
            )
        )
        self.link_existing_owner_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_PRIMARY_ACTION)
            # .replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;") # Primary action might not need white text
        )
        self.remove_horse_owner_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_DANGER_ACTION).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white;"
            )
        )

        owners_action_layout.addWidget(self.create_link_owner_btn)
        owners_action_layout.addWidget(self.link_existing_owner_btn)
        owners_action_layout.addWidget(self.remove_horse_owner_btn)
        owners_action_layout.addStretch()
        main_layout.addLayout(owners_action_layout)

        # --- Current Owners List ---
        self.current_owners_list_widget = HorseOwnerListWidget()  # Styled QListWidget

        owners_list_label = QLabel("Current Owners & Percentages:")
        owners_list_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; margin-bottom: 5px; font-weight: bold;"
        )
        main_layout.addWidget(owners_list_label)
        main_layout.addWidget(
            self.current_owners_list_widget, 1
        )  # Give it stretch factor

        # --- Percentage Edit Frame (initially hidden) ---
        self.percentage_edit_frame = QFrame()
        self.percentage_edit_frame.setStyleSheet(
            "background-color: transparent;"
        )  # No border needed
        percentage_edit_layout = QHBoxLayout(self.percentage_edit_frame)
        percentage_edit_layout.setContentsMargins(0, 5, 0, 0)  # Top margin only

        self.selected_owner_for_pct_label = QLabel(
            "Edit % for:"
        )  # Text will be set dynamically
        self.selected_owner_for_pct_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-right: 5px;"
        )

        self.edit_owner_percentage_spinbox = QDoubleSpinBox()
        self.edit_owner_percentage_spinbox.setRange(
            0.00, 100.00
        )  # Allow 0% as per v1.2.3 changelog for controller
        self.edit_owner_percentage_spinbox.setDecimals(2)
        self.edit_owner_percentage_spinbox.setSuffix(" %")
        self.edit_owner_percentage_spinbox.setStyleSheet(self._get_input_style())
        self.edit_owner_percentage_spinbox.setFixedWidth(100)  # Consistent width

        self.save_owner_percentage_btn = QPushButton("💾 Save %")
        self.save_owner_percentage_btn.setStyleSheet(
            self._get_generic_button_style().replace(
                DARK_BUTTON_BG, DARK_SUCCESS_ACTION
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
        self.selected_horse_owner_assoc_id = None  # Clear selection
        self.current_horse_owners_assoc = []

        if self.current_horse and self.current_horse.horse_id is not None:
            self.logger.debug(
                f"Populating owners for horse ID {self.current_horse.horse_id}"
            )
            # This method in HorseController returns a list of dicts
            # [{'owner_id': id, 'display_name': name_with_account, 'percentage': float}]
            self.current_horse_owners_assoc = self.horse_controller.get_horse_owners(
                self.current_horse.horse_id
            )

            for owner_assoc_data in self.current_horse_owners_assoc:
                item_text = f"{owner_assoc_data['display_name']} - {owner_assoc_data['percentage']:.2f}%"
                list_item = QListWidgetItem(item_text)
                # Store the owner_id of the associated owner for identification
                list_item.setData(
                    Qt.ItemDataRole.UserRole, owner_assoc_data["owner_id"]
                )
                self.current_owners_list_widget.addItem(list_item)
        else:
            self.logger.debug("No current horse or horse ID to load owners for.")

        self.percentage_edit_frame.hide()  # Hide edit frame when reloading
        self.update_buttons_state()

    def _on_horse_owner_selection_changed(self):
        selected_items = self.current_owners_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]
            self.selected_horse_owner_assoc_id = list_item.data(
                Qt.ItemDataRole.UserRole
            )  # This is owner_id
            self.logger.info(
                f"Horse-owner association selected: Owner ID {self.selected_horse_owner_assoc_id}"
            )

            # Find the corresponding association data to get percentage and name
            assoc_data = next(
                (
                    ho
                    for ho in self.current_horse_owners_assoc
                    if ho["owner_id"] == self.selected_horse_owner_assoc_id
                ),
                None,
            )
            if assoc_data:
                self.edit_owner_percentage_spinbox.setValue(assoc_data["percentage"])
                # Use the more complete display_name from the association data if available
                self.selected_owner_for_pct_label.setText(
                    f"Edit % for: {assoc_data['display_name']}"
                )
                self.percentage_edit_frame.show()
            else:
                self.logger.warning(
                    f"Could not find association data for selected owner ID {self.selected_horse_owner_assoc_id}"
                )
                self.percentage_edit_frame.hide()
        else:
            self.selected_horse_owner_assoc_id = None
            self.percentage_edit_frame.hide()
            self.logger.info("Horse-owner association selection cleared.")
        self.update_buttons_state()

    def _handle_create_and_link_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Add Owner", "Please select a horse first.")
            return
        self.logger.info(
            f"Initiating Create & Link Owner for horse: {self.current_horse.horse_name}"
        )

        # current_user_login is set in __init__
        dialog = CreateAndLinkOwnerDialog(
            self.parent_view, self.current_horse.horse_name, self.current_user_login
        )

        dialog_result = dialog.exec()
        self.logger.debug(
            f"CreateAndLinkOwnerDialog.exec() result: {dialog_result} (Accepted is {QDialog.DialogCode.Accepted})"
        )  # ADDED LOGGING

        if dialog_result == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.logger.debug(
                f"Data from CreateAndLinkOwnerDialog: {data}"
            )  # ADDED LOGGING

            if (
                data
                and data.get("owner_details")
                and data.get("percentage") is not None
            ):
                owner_details_from_dialog = data["owner_details"]
                percentage_from_dialog = data["percentage"]
                self.logger.info(
                    f"Dialog accepted. Owner details: {owner_details_from_dialog}, Percentage: {percentage_from_dialog}"
                )

                # Create the master owner first
                success_create, msg_create, new_owner_obj = (
                    self.owner_controller.create_master_owner(
                        owner_details_from_dialog, self.current_user_login
                    )
                )
                self.logger.debug(
                    f"OwnerController.create_master_owner result: success={success_create}, msg='{msg_create}', new_owner_obj={new_owner_obj}"
                )  # ADDED LOGGING

                if success_create and new_owner_obj:
                    self.logger.info(
                        f"Newly created owner ID {new_owner_obj.owner_id}, now linking to horse ID {self.current_horse.horse_id}"
                    )
                    # Now link this new owner to the horse
                    success_link, msg_link = self.horse_controller.add_owner_to_horse(
                        self.current_horse.horse_id,
                        new_owner_obj.owner_id,
                        percentage_from_dialog,
                        self.current_user_login,
                    )
                    self.logger.debug(
                        f"HorseController.add_owner_to_horse result: success={success_link}, msg='{msg_link}'"
                    )  # ADDED LOGGING

                    if success_link:
                        self.parent_view.show_info("Owner Linked", msg_link)
                        self.load_owners_for_horse(self.current_horse)  # Refresh list
                        self.owner_association_changed.emit(msg_link)
                    else:
                        self.parent_view.show_error("Failed to Link Owner", msg_link)
                        # Potentially delete the just-created owner if linking fails to avoid orphaned owner?
                        # For now, it matches existing behavior.
                else:
                    # This 'else' means owner creation failed
                    self.parent_view.show_error(
                        "Failed to Create Owner",
                        msg_create or "Could not create the new owner.",
                    )
                    self.logger.error(
                        f"Failed to create new owner via dialog, controller message: {msg_create}"
                    )
            else:
                # This 'else' means dialog was accepted, but get_data() didn't return expected structure
                self.logger.warning(
                    "Create and link owner dialog accepted, but no valid data (owner_details/percentage) retrieved from dialog."
                )
                self.parent_view.show_warning(
                    "Data Error",
                    "Could not retrieve valid data from the new owner form.",
                )
        else:
            # This 'else' means dialog was rejected (Cancel, X, or Esc pressed)
            self.logger.info(
                "Create and link owner dialog cancelled by user (dialog result was not 'Accepted')."
            )

    def _handle_link_existing_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Link Owner", "Please select a horse first.")
            return
        self.logger.info(
            f"Initiating Link Existing Owner for horse: {self.current_horse.horse_name}"
        )

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
                self.logger.info(
                    f"Attempting to link existing owner ID {data['owner_id']} with {data['percentage']}% to horse ID {self.current_horse.horse_id}"
                )
                # current_user_login is available as self.current_user_login
                success_link, msg_link = self.horse_controller.add_owner_to_horse(
                    self.current_horse.horse_id,
                    data["owner_id"],
                    data["percentage"],
                    self.current_user_login,
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
                self.parent_view.show_warning(
                    "Data Error",
                    "Could not retrieve valid selection from the link owner form.",
                )
        else:
            self.logger.info("Link existing owner dialog cancelled by user (rejected).")

    def _handle_remove_owner_from_horse(self):
        if not self.current_horse or self.selected_horse_owner_assoc_id is None:
            self.parent_view.show_warning(
                "Remove Owner Link", "Please select a horse and an owner from its list."
            )
            return

        owner_id_to_remove = self.selected_horse_owner_assoc_id
        # Find display name for confirmation
        owner_display_name = f"Owner ID {owner_id_to_remove}"  # Fallback
        for owner_assoc in self.current_horse_owners_assoc:
            if owner_assoc["owner_id"] == owner_id_to_remove:
                owner_display_name = owner_assoc["display_name"]
                break
        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )

        if self.parent_view.show_question(
            "Confirm Removal",
            f"Are you sure you want to remove owner '{owner_display_name}' from horse '{horse_name_display}'?",
        ):
            self.logger.info(
                f"User confirmed removal of owner ID {owner_id_to_remove} from horse ID {self.current_horse.horse_id}"
            )
            success, message = self.horse_controller.remove_owner_from_horse(
                self.current_horse.horse_id, owner_id_to_remove, self.current_user_login
            )
            if success:
                self.parent_view.show_info("Owner Link Removed", message)
                self.load_owners_for_horse(self.current_horse)  # Refresh list
                self.owner_association_changed.emit(message)
            else:
                self.parent_view.show_error("Failed to Remove Owner Link", message)
        else:
            self.logger.info("Owner link removal cancelled by user.")

    def _handle_save_owner_percentage(self):
        if not self.current_horse or self.selected_horse_owner_assoc_id is None:
            self.parent_view.show_warning(
                "Save Percentage",
                "Please select a horse and an owner to update their percentage.",
            )
            return

        new_percentage = self.edit_owner_percentage_spinbox.value()
        # Controller's update method already validates 0-100 range, so UI check is more for immediate feedback
        if not (0.00 <= new_percentage <= 100.00):
            self.parent_view.show_error(
                "Invalid Percentage",
                "Ownership percentage must be between 0.00 and 100.00.",
            )
            return

        self.logger.info(
            f"Attempting to update percentage for owner ID {self.selected_horse_owner_assoc_id} "
            f"on horse ID {self.current_horse.horse_id} to {new_percentage}%"
        )
        success, message = self.horse_controller.update_horse_owner_percentage(
            self.current_horse.horse_id,
            self.selected_horse_owner_assoc_id,
            new_percentage,
            self.current_user_login,
        )
        if success:
            self.parent_view.show_info("Percentage Updated", message)
            self.load_owners_for_horse(
                self.current_horse
            )  # Refresh list and percentages
            self.owner_association_changed.emit(message)
        else:
            self.parent_view.show_error("Failed to Update Percentage", message)

    def update_buttons_state(self):
        is_horse_selected = self.current_horse is not None
        is_owner_in_list_selected = self.selected_horse_owner_assoc_id is not None

        self.create_link_owner_btn.setEnabled(is_horse_selected)
        self.link_existing_owner_btn.setEnabled(is_horse_selected)
        self.remove_horse_owner_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )
        self.save_owner_percentage_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )

        # Show/hide percentage edit frame based on selection only
        self.percentage_edit_frame.setVisible(
            is_horse_selected and is_owner_in_list_selected
        )
