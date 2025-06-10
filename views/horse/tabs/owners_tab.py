# views/horse/tabs/owners_tab.py
"""
EDSI Veterinary Management System - Horse Owners Tab
Version: 1.3.0
Purpose: Manages the association of owners with a specific horse.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.3.0 (2025-06-09):
    - Added double-click functionality to the owners list. Users can now
      double-click a linked owner to open the AddEditOwnerDialog and edit
      their details directly.
    - Implemented the _handle_edit_owner method to manage this workflow.
- v1.2.5 (2025-05-26):
    - Modified `_handle_create_and_link_owner` and `_handle_link_existing_owner`
      to pass a new method `_validate_total_ownership_for_dialog` as a callback
      to `CreateAndLinkOwnerDialog` and `LinkExistingOwnerDialog` respectively.
    - The dialogs will now call this callback to perform total ownership
      validation before closing. If validation fails, the dialog remains open.
- v1.2.4 (2025-05-26):
    - Added `_validate_total_ownership` helper method for client-side validation.
    - Integrated this validation into relevant handler methods.
"""

import logging
from typing import Optional, List, Dict
from decimal import Decimal

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
    DARK_BUTTON_HOVER,
    DARK_HEADER_FOOTER,
    DARK_TEXT_TERTIARY,
)
from models import Horse, Owner as OwnerModel
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController

from ..dialogs.create_link_owner_dialog import CreateAndLinkOwnerDialog
from ..dialogs.link_existing_owner_dialog import LinkExistingOwnerDialog
from ...admin.dialogs.add_edit_owner_dialog import AddEditOwnerDialog
from ..widgets.horse_owner_list_widget import HorseOwnerListWidget


class OwnersTab(QWidget):
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
        self.current_horse_owners_assoc: List[Dict] = []
        self.selected_horse_owner_assoc_id: Optional[int] = None
        self.current_user_login = "UnknownUser"
        if hasattr(self.parent_view, "current_user") and self.parent_view.current_user:
            self.current_user_login = self.parent_view.current_user
        else:
            self.logger.warning(
                "Could not determine current_user for OwnersTab auditing."
            )
        self.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        self._setup_ui(main_layout)
        self._setup_connections()
        self.update_buttons_state()

    def _get_generic_button_style(self) -> str:
        if hasattr(self.parent_view, "get_generic_button_style"):
            return self.parent_view.get_generic_button_style()
        return f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;}} QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"

    def _get_input_style(self) -> str:
        return f"QDoubleSpinBox {{ background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; padding: 5px; border-radius: 4px; }}"

    def _setup_ui(self, main_layout: QVBoxLayout):
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
        self.current_owners_list_widget = HorseOwnerListWidget()
        owners_list_label = QLabel(
            "Current Owners & Percentages (Double-click to Edit):"
        )
        owners_list_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; margin-bottom: 5px; font-weight: bold;"
        )
        main_layout.addWidget(owners_list_label)
        main_layout.addWidget(self.current_owners_list_widget, 1)
        self.percentage_edit_frame = QFrame()
        self.percentage_edit_frame.setStyleSheet("background-color: transparent;")
        percentage_edit_layout = QHBoxLayout(self.percentage_edit_frame)
        percentage_edit_layout.setContentsMargins(0, 5, 0, 0)
        self.selected_owner_for_pct_label = QLabel("Edit % for:")
        self.selected_owner_for_pct_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-right: 5px;"
        )
        self.edit_owner_percentage_spinbox = QDoubleSpinBox()
        self.edit_owner_percentage_spinbox.setRange(0.00, 100.00)
        self.edit_owner_percentage_spinbox.setDecimals(2)
        self.edit_owner_percentage_spinbox.setSuffix(" %")
        self.edit_owner_percentage_spinbox.setStyleSheet(self._get_input_style())
        self.edit_owner_percentage_spinbox.setFixedWidth(100)
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
        self.current_owners_list_widget.itemDoubleClicked.connect(
            self._handle_edit_owner
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
        self.selected_horse_owner_assoc_id = None
        self.current_horse_owners_assoc = []
        if self.current_horse and self.current_horse.horse_id is not None:
            self.logger.debug(
                f"Populating owners for horse ID {self.current_horse.horse_id}"
            )
            self.current_horse_owners_assoc = self.horse_controller.get_horse_owners(
                self.current_horse.horse_id
            )
            for owner_assoc_data in self.current_horse_owners_assoc:
                item_text = f"{owner_assoc_data.get('owner_name', 'N/A')} - {owner_assoc_data.get('percentage_ownership', 0.0):.2f}%"
                list_item = QListWidgetItem(item_text)
                list_item.setData(
                    Qt.ItemDataRole.UserRole, owner_assoc_data.get("owner_id")
                )
                self.current_owners_list_widget.addItem(list_item)
        else:
            self.logger.debug("No current horse or horse ID to load owners for.")
        self.percentage_edit_frame.hide()
        self.update_buttons_state()

    def _on_horse_owner_selection_changed(self):
        selected_items = self.current_owners_list_widget.selectedItems()
        if selected_items:
            list_item = selected_items[0]
            self.selected_horse_owner_assoc_id = list_item.data(
                Qt.ItemDataRole.UserRole
            )
            self.logger.info(f"Owner ID {self.selected_horse_owner_assoc_id} selected.")
            assoc_data = next(
                (
                    ho
                    for ho in self.current_horse_owners_assoc
                    if ho["owner_id"] == self.selected_horse_owner_assoc_id
                ),
                None,
            )
            if assoc_data:
                self.edit_owner_percentage_spinbox.setValue(
                    assoc_data.get("percentage_ownership", 0.0)
                )
                self.selected_owner_for_pct_label.setText(
                    f"Edit % for: {assoc_data.get('owner_name','N/A')}"
                )
                self.percentage_edit_frame.show()
            else:
                self.logger.warning(
                    f"No data for selected owner ID {self.selected_horse_owner_assoc_id}"
                )
                self.percentage_edit_frame.hide()
        else:
            self.selected_horse_owner_assoc_id = None
            self.percentage_edit_frame.hide()
            self.logger.info("Owner selection cleared.")
        self.update_buttons_state()

    def _handle_edit_owner(self, item: QListWidgetItem):
        """Opens the AddEditOwnerDialog for the double-clicked owner."""
        owner_id = item.data(Qt.ItemDataRole.UserRole)
        if owner_id is None:
            return

        self.logger.info(f"Edit requested for owner ID: {owner_id}")
        owner_to_edit = self.owner_controller.get_owner_by_id(owner_id)

        if owner_to_edit:
            dialog = AddEditOwnerDialog(
                parent_view=self.parent_view,
                owner_controller=self.owner_controller,
                owner_object=owner_to_edit,
                current_user_id=self.current_user_login,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.logger.info(f"Owner ID {owner_id} was updated. Refreshing list.")
                # After saving, reload the owners for the current horse
                self.load_owners_for_horse(self.current_horse)
                # Notify the main screen that data has changed
                self.owner_association_changed.emit(
                    f"Details updated for owner '{owner_to_edit.last_name}'."
                )
        else:
            self.parent_view.show_error(
                "Error", f"Could not retrieve details for owner ID {owner_id}."
            )

    def _validate_total_ownership_for_dialog(
        self,
        owner_id_being_changed: Optional[int],
        new_percentage_for_this_owner: float,
    ) -> bool:
        """Called by dialogs to validate total ownership before they accept."""
        if not self.current_horse:
            return False
        current_total_other_owners = Decimal("0.00")
        for assoc in self.current_horse_owners_assoc:
            if (
                owner_id_being_changed is not None
                and assoc.get("owner_id") == owner_id_being_changed
            ):
                continue
            current_total_other_owners += Decimal(
                str(assoc.get("percentage_ownership", 0.0))
            )

        prospective_total = current_total_other_owners + Decimal(
            str(new_percentage_for_this_owner)
        )
        self.logger.debug(
            f"Dialog validation: Others total={current_total_other_owners}, New%={new_percentage_for_this_owner}, Prospective={prospective_total}"
        )
        if prospective_total > Decimal("100.00"):
            msg = (
                f"Total ownership cannot exceed 100%.\n"
                f"Other owners: {current_total_other_owners:.2f}%\n"
                f"This owner: {new_percentage_for_this_owner:.2f}%\n"
                f"Resulting total: {prospective_total:.2f}%"
            )
            QMessageBox.warning(
                self.parent_view, "Ownership Error", msg
            )  # Show error via parent_view
            return False
        return True

    def _handle_create_and_link_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Add Owner", "Select horse first.")
            return
        self.logger.info(
            f"Initiating Create & Link Owner for: {self.current_horse.horse_name}"
        )

        # Pass the validation method to the dialog
        dialog = CreateAndLinkOwnerDialog(
            self,
            self.current_horse.horse_name or "Selected Horse",
            self.current_user_login,
            total_ownership_validator=self._validate_total_ownership_for_dialog,  # Pass callback
        )
        if (
            dialog.exec() == QDialog.DialogCode.Accepted
        ):  # Dialog only accepts if ALL validation (incl. total %) passed
            data = dialog.get_data()
            if (
                data
                and data.get("owner_details")
                and data.get("percentage") is not None
            ):
                owner_details, percentage = data["owner_details"], data["percentage"]
                self.logger.info(
                    f"Dialog OK. Owner: {owner_details}, Percentage: {percentage}"
                )
                # Total ownership validation already done by the dialog via callback
                success_create, msg_create, new_owner_obj = (
                    self.owner_controller.create_master_owner(
                        owner_details, self.current_user_login
                    )
                )
                if (
                    success_create
                    and new_owner_obj
                    and self.current_horse
                    and self.current_horse.horse_id is not None
                ):
                    success_link, msg_link = self.horse_controller.add_owner_to_horse(
                        self.current_horse.horse_id,
                        new_owner_obj.owner_id,
                        percentage,
                        self.current_user_login,
                    )
                    if success_link:
                        self.parent_view.show_info("Owner Linked", msg_link)
                        self.load_owners_for_horse(self.current_horse)
                        self.owner_association_changed.emit(msg_link)
                    else:
                        self.parent_view.show_error("Link Error", msg_link)
                else:
                    self.parent_view.show_error(
                        "Create Error", msg_create or "Could not create owner."
                    )
            else:
                self.logger.warning("Create dialog accepted, but no valid data.")
                self.parent_view.show_warning("Data Error", "No data from form.")
        else:
            self.logger.info("Create & link owner dialog cancelled.")

    def _handle_link_existing_owner(self):
        if not self.current_horse:
            self.parent_view.show_warning("Link Owner", "Select horse first.")
            return
        self.logger.info(
            f"Initiating Link Existing Owner for: {self.current_horse.horse_name}"
        )

        # LinkExistingOwnerDialog needs similar modification to accept validator
        # For now, we'll keep its internal validation and add OwnersTab validation after it closes.
        # This means if total % validation fails, user has to re-open LinkExistingOwnerDialog.
        # Ideal solution: Modify LinkExistingOwnerDialog to also take the callback.

        dialog = LinkExistingOwnerDialog(
            self, self.current_horse.horse_name or "Selected Horse"
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if (
                data
                and data.get("owner_id") is not None
                and data.get("percentage") is not None
                and self.current_horse
                and self.current_horse.horse_id is not None
            ):
                owner_id, percentage = data["owner_id"], data["percentage"]
                self.logger.info(
                    f"Linking owner ID {owner_id} with {percentage}% to horse ID {self.current_horse.horse_id}"
                )

                # Perform total ownership validation AFTER dialog closes for this dialog type (can be improved)
                if not self._validate_total_ownership_for_dialog(None, percentage):
                    # User has to click "Link Existing Owner" again if this fails.
                    return

                success_link, msg_link = self.horse_controller.add_owner_to_horse(
                    self.current_horse.horse_id,
                    owner_id,
                    percentage,
                    self.current_user_login,
                )
                if success_link:
                    self.parent_view.show_info("Owner Linked", msg_link)
                    self.load_owners_for_horse(self.current_horse)
                    self.owner_association_changed.emit(msg_link)
                else:
                    self.parent_view.show_error("Link Error", msg_link)
            else:
                self.logger.warning("No data from link dialog.")
                self.parent_view.show_warning("Data Error", "No selection from form.")
        else:
            self.logger.info("Link existing owner dialog cancelled.")

    def _handle_save_owner_percentage(self):
        if (
            not self.current_horse
            or self.current_horse.horse_id is None
            or self.selected_horse_owner_assoc_id is None
        ):
            self.parent_view.show_warning(
                "Save %", "Select horse and owner to update %."
            )
            return
        new_percentage = self.edit_owner_percentage_spinbox.value()

        # VALIDATION using the dialog-focused validator
        if not self._validate_total_ownership_for_dialog(
            self.selected_horse_owner_assoc_id, new_percentage
        ):
            return  # Error message already shown by validator

        self.logger.info(
            f"Updating % for owner ID {self.selected_horse_owner_assoc_id} on horse ID {self.current_horse.horse_id} to {new_percentage}%"
        )
        success, message = self.horse_controller.update_horse_owner_percentage(
            self.current_horse.horse_id,
            self.selected_horse_owner_assoc_id,
            new_percentage,
            self.current_user_login,
        )
        if success:
            self.parent_view.show_info("Percentage Updated", message)
            self.load_owners_for_horse(self.current_horse)
            self.owner_association_changed.emit(message)
        else:
            self.parent_view.show_error("Update % Error", message)

    def _handle_remove_owner_from_horse(self):
        if (
            not self.current_horse
            or self.current_horse.horse_id is None
            or self.selected_horse_owner_assoc_id is None
        ):
            warn_msg = "Select horse and owner from list."
            if hasattr(self.parent_view, "show_warning"):
                self.parent_view.show_warning("Remove Owner", warn_msg)
            else:
                QMessageBox.warning(self, "Remove Owner", warn_msg)
                return
        owner_id_to_remove = self.selected_horse_owner_assoc_id
        owner_display_name = f"Owner ID {owner_id_to_remove}"
        for oa in self.current_horse_owners_assoc:
            if oa.get("owner_id") == owner_id_to_remove:
                owner_display_name = oa.get("owner_name", owner_display_name)
                break
        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )
        confirm_msg = (
            f"Remove owner '{owner_display_name}' from horse '{horse_name_display}'?"
        )
        proceed = False
        if hasattr(self.parent_view, "show_question"):
            proceed = self.parent_view.show_question("Confirm Removal", confirm_msg)
        else:
            proceed = (
                QMessageBox.question(
                    self,
                    "Confirm Removal",
                    confirm_msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            )
        if proceed:
            self.logger.info(
                f"Confirmed removal of owner ID {owner_id_to_remove} from horse ID {self.current_horse.horse_id}"
            )
            success, message = self.horse_controller.remove_owner_from_horse(
                self.current_horse.horse_id, owner_id_to_remove, self.current_user_login
            )
            if success:
                if hasattr(self.parent_view, "show_info"):
                    self.parent_view.show_info("Owner Removed", message)
                else:
                    QMessageBox.information(self, "Owner Removed", message)
                self.load_owners_for_horse(self.current_horse)
                self.owner_association_changed.emit(message)
            else:
                if hasattr(self.parent_view, "show_error"):
                    self.parent_view.show_error("Remove Error", message)
                else:
                    QMessageBox.critical(self, "Remove Error", message)
        else:
            self.logger.info("Owner removal cancelled.")

    def update_buttons_state(self):
        is_horse_selected = (
            self.current_horse is not None and self.current_horse.horse_id is not None
        )
        is_owner_in_list_selected = self.selected_horse_owner_assoc_id is not None
        self.create_link_owner_btn.setEnabled(is_horse_selected)
        self.link_existing_owner_btn.setEnabled(is_horse_selected)
        self.remove_horse_owner_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )
        self.save_owner_percentage_btn.setEnabled(
            is_horse_selected and is_owner_in_list_selected
        )
        self.percentage_edit_frame.setVisible(
            is_horse_selected and is_owner_in_list_selected
        )
