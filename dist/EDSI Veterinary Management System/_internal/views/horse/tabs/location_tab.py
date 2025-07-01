# views/horse/tabs/location_tab.py
"""
EDSI Veterinary Management System - Horse Location Tab
Version: 1.0.1
Purpose: Manages the assignment of a single location to a horse.
         - Modified assign/remove location logic to call HorseController for
           database persistence BEFORE emitting location_assignment_changed signal,
           ensuring data integrity and proper UI updates in parent views.
Last Updated: May 25, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-05-25):
    - Refactored `_assign_location_to_horse`: Now calls
      `horse_controller.assign_horse_to_location` to save the assignment
      to the database. Emits `location_assignment_changed` only on successful save.
      Updates local UI based on controller success.
    - Refactored `_handle_remove_location_link`: Now calls
      `horse_controller.remove_horse_from_location` to update the database.
      Emits `location_assignment_changed` (with None for location) only on
      successful removal. Updates local UI based on controller success.
    - Ensured user feedback (info/error messages) is provided based on the
      outcome of controller operations.
- v1.0.0 (2025-05-20):
    - Initial implementation.
    - UI with current location display (QLabel).
    - Buttons: "Create New & Link Location", "Link Existing Location", "Remove Location Link".
    - Integrates AddEditLocationDialog and SelectExistingLocationDialog.
    - Emits location_assignment_changed(location_id: Optional[int], location_name: Optional[str]) signal.
"""

import logging
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QDialog,
    QMessageBox,  # Explicitly imported for clarity, though parent_view might handle
)
from PySide6.QtCore import Qt, Signal

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_BUTTON_BG,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_BORDER,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_SUCCESS_ACTION,
    DARK_PRIMARY_ACTION,
    DARK_DANGER_ACTION,
    DARK_BUTTON_HOVER,
    DARK_HEADER_FOOTER,
    DARK_TEXT_TERTIARY,
)
from models import (
    Horse,
)  # LocationModel not directly used here, controller returns names/ids
from controllers.horse_controller import HorseController
from controllers.location_controller import LocationController
from views.admin.dialogs.add_edit_location_dialog import AddEditLocationDialog
from views.horse.dialogs.select_existing_location_dialog import (
    SelectExistingLocationDialog,
)


class LocationTab(QWidget):
    """Tab widget for managing a horse's single assigned location."""

    location_assignment_changed = Signal(
        object
    )  # Emits a dict: {'id': Optional[int], 'name': Optional[str]}

    def __init__(
        self,
        parent_view,
        horse_controller: HorseController,
        location_controller: LocationController,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.location_controller = location_controller

        self.current_horse: Optional[Horse] = None
        self._current_location_id: Optional[int] = None
        self._current_location_name: str = "N/A"

        self.current_user_login = "UnknownUser"
        if hasattr(self.parent_view, "current_user") and self.parent_view.current_user:
            self.current_user_login = self.parent_view.current_user
        else:
            self.logger.warning(
                "Could not determine current_user for LocationTab auditing."
            )

        self.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self._setup_ui(main_layout)
        self._setup_connections()
        self.update_buttons_state()

    def _get_generic_button_style(self) -> str:
        if hasattr(self.parent_view, "get_generic_button_style"):
            return self.parent_view.get_generic_button_style()
        return (
            f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _setup_ui(self, main_layout: QVBoxLayout):
        location_display_frame = QFrame()
        location_display_frame.setStyleSheet("background-color: transparent;")
        location_display_layout = QHBoxLayout(location_display_frame)
        location_display_layout.setContentsMargins(0, 0, 0, 10)

        current_location_title_label = QLabel("Currently Assigned Location:")
        current_location_title_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-weight: bold; background: transparent;"
        )
        self.current_location_display_label = QLabel(self._current_location_name)
        self.current_location_display_label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-size: 14px; background-color: {DARK_INPUT_FIELD_BACKGROUND}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; min-height: 22px;"
        )
        self.current_location_display_label.setWordWrap(True)

        location_display_layout.addWidget(current_location_title_label)
        location_display_layout.addWidget(self.current_location_display_label, 1)
        main_layout.addWidget(location_display_frame)

        action_buttons_layout = QHBoxLayout()
        self.create_link_location_btn = QPushButton("➕ Create New & Assign Location")
        self.link_existing_location_btn = QPushButton("🔗 Assign Existing Location")
        self.remove_location_link_btn = QPushButton("➖ Clear Assigned Location")

        button_style = self._get_generic_button_style()
        self.create_link_location_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_SUCCESS_ACTION).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white;"
            )
        )
        self.link_existing_location_btn.setStyleSheet(
            button_style.replace(
                DARK_BUTTON_BG, DARK_PRIMARY_ACTION
            )  # Assuming default text color is fine
        )
        self.remove_location_link_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_DANGER_ACTION).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white;"
            )
        )

        action_buttons_layout.addWidget(self.create_link_location_btn)
        action_buttons_layout.addWidget(self.link_existing_location_btn)
        action_buttons_layout.addWidget(self.remove_location_link_btn)
        action_buttons_layout.addStretch()
        main_layout.addLayout(action_buttons_layout)
        main_layout.addStretch(1)

    def _setup_connections(self):
        self.create_link_location_btn.clicked.connect(
            self._handle_create_and_link_location
        )
        self.link_existing_location_btn.clicked.connect(
            self._handle_link_existing_location
        )
        self.remove_location_link_btn.clicked.connect(self._handle_remove_location_link)

    def load_location_for_horse(self, horse: Optional[Horse]):
        self.current_horse = horse
        self.logger.debug(
            f"LocationTab: Loading location for horse: {horse.horse_name if horse else 'None'}"
        )
        if self.current_horse and self.current_horse.horse_id is not None:
            # The horse object passed might already be eager-loaded by HorseUnifiedManagement
            # If not, self.horse_controller.get_horse_by_id() would re-fetch.
            # For consistency, let's use the passed horse object directly if its location is loaded.
            # If horse.location is not loaded, then a fresh fetch might be needed,
            # but this should ideally be handled by the caller providing a fully loaded horse.

            # Let's assume the passed 'horse' object has its .location eager-loaded
            # by HorseUnifiedManagement calling HorseController.get_horse_by_id().
            self._current_location_id = self.current_horse.current_location_id
            if self.current_horse.location and hasattr(
                self.current_horse.location, "location_name"
            ):
                self._current_location_name = (
                    self.current_horse.location.location_name or "N/A"
                )
            else:
                self._current_location_name = (
                    "N/A"  # If location object is None or no name
                )

            self.logger.debug(
                f"LocationTab: Horse ID {self.current_horse.horse_id}, "
                f"current_location_id: {self._current_location_id}, "
                f"current_location_name: '{self._current_location_name}'"
            )
        else:
            self._current_location_id = None
            self._current_location_name = "N/A (No horse selected)"
            self.logger.debug("LocationTab: No current horse, location set to N/A.")

        self.current_location_display_label.setText(self._current_location_name)
        self.update_buttons_state()

    def _handle_create_and_link_location(self):
        if not self.current_horse or self.current_horse.horse_id is None:
            self.parent_view.show_warning(
                "Assign Location", "Please select a horse first."
            )
            return
        self.logger.info(
            f"Initiating Create & Assign New Location for horse: {self.current_horse.horse_name}"
        )

        dialog = AddEditLocationDialog(
            self.parent_view,
            self.location_controller,
            self.current_user_login,
            location=None,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # IMPORTANT: AddEditLocationDialog must be modified to return the created location's ID and name
            # For example, by adding methods like dialog.get_created_location_id() and dialog.get_created_location_name()
            created_location_id = getattr(
                dialog, "created_location_id", None
            )  # Hypothetical
            created_location_name = getattr(
                dialog, "created_location_name", None
            )  # Hypothetical

            if created_location_id is not None and created_location_name is not None:
                self.logger.info(
                    f"New location created: ID {created_location_id}, Name '{created_location_name}'. Assigning to horse."
                )
                self._assign_location_to_horse(
                    created_location_id, created_location_name
                )
            else:
                self.logger.warning(
                    "AddEditLocationDialog did not return created location details. User may need to assign manually."
                )
                self.parent_view.show_info(
                    "Location Created",
                    "New location created. If not automatically assigned, please use 'Assign Existing Location' to link it.",
                )
        else:
            self.logger.info("Create & Assign New Location dialog cancelled.")

    def _handle_link_existing_location(self):
        if not self.current_horse or self.current_horse.horse_id is None:
            self.parent_view.show_warning(
                "Assign Location", "Please select a horse first."
            )
            return
        self.logger.info(
            f"Initiating Assign Existing Location for horse: {self.current_horse.horse_name}"
        )

        dialog = SelectExistingLocationDialog(
            self.parent_view, self.current_horse.horse_name or "Selected Horse"
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_id = dialog.get_selected_location_id()
            if selected_id is not None:
                # Fetch location details to get the name for UI update and signal
                loc_obj = self.location_controller.get_location_by_id(selected_id)
                if loc_obj and hasattr(loc_obj, "location_name"):
                    self._assign_location_to_horse(
                        loc_obj.location_id, loc_obj.location_name
                    )
                else:
                    self.parent_view.show_error(
                        "Error",
                        f"Could not retrieve details for Location ID {selected_id}.",
                    )
            else:
                self.parent_view.show_warning(
                    "Assign Location", "No location was selected."
                )
        else:
            self.logger.info("Assign Existing Location dialog cancelled.")

    def _assign_location_to_horse(self, location_id: int, location_name: str):
        if not self.current_horse or self.current_horse.horse_id is None:
            self.logger.error("No current horse to assign location to.")
            self.parent_view.show_error(
                "Error", "No horse selected to assign location."
            )
            return

        self.logger.info(
            f"Attempting to assign Location ID {location_id} ('{location_name}') to Horse ID {self.current_horse.horse_id}"
        )

        # Call controller to persist the change
        success, message = self.horse_controller.assign_horse_to_location(
            horse_id=self.current_horse.horse_id,
            location_id=location_id,
            notes=None,  # Or add a notes field to this tab/dialog if needed
            modified_by_user=self.current_user_login,
        )

        if success:
            self._current_location_id = location_id
            self._current_location_name = location_name
            self.current_location_display_label.setText(self._current_location_name)

            self.logger.info(
                f"Successfully assigned Location ID {location_id} to Horse ID {self.current_horse.horse_id}. Emitting signal."
            )
            self.location_assignment_changed.emit(
                {"id": location_id, "name": location_name}
            )
            self.parent_view.show_info(
                "Location Assigned", message
            )  # Use message from controller
        else:
            self.logger.error(f"Failed to assign location: {message}")
            self.parent_view.show_error("Assignment Failed", message)

        self.update_buttons_state()

    def _handle_remove_location_link(self):
        if not self.current_horse or self.current_horse.horse_id is None:
            self.parent_view.show_warning(
                "Clear Location", "Please select a horse first."
            )
            return
        if self._current_location_id is None:  # Check local state first
            self.parent_view.show_info(
                "Clear Location", "No location is currently assigned to this horse."
            )
            return

        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )
        if self.parent_view.show_question(
            "Confirm Clear Location",
            f"Are you sure you want to clear the location assignment for horse '{horse_name_display}'?",
        ):
            self.logger.info(
                f"Attempting to clear location for horse ID {self.current_horse.horse_id}, current loc ID: {self._current_location_id}"
            )

            success, message = self.horse_controller.remove_horse_from_location(
                horse_id=self.current_horse.horse_id,
                location_id=self._current_location_id,  # Pass current location ID to ensure correct history update
                modified_by_user=self.current_user_login,
            )

            if success:
                self._current_location_id = None
                self._current_location_name = "N/A"
                self.current_location_display_label.setText(self._current_location_name)

                self.logger.info(
                    f"Successfully cleared location for Horse ID {self.current_horse.horse_id}. Emitting signal."
                )
                self.location_assignment_changed.emit({"id": None, "name": "N/A"})
                self.parent_view.show_info(
                    "Location Cleared", message
                )  # Use message from controller
            else:
                self.logger.error(f"Failed to clear location: {message}")
                self.parent_view.show_error("Clear Location Failed", message)

            self.update_buttons_state()
        else:
            self.logger.info("Clear location assignment cancelled by user.")

    def update_buttons_state(self):
        is_horse_selected = (
            self.current_horse is not None and self.current_horse.horse_id is not None
        )
        is_location_assigned = self._current_location_id is not None

        self.create_link_location_btn.setEnabled(is_horse_selected)
        self.link_existing_location_btn.setEnabled(is_horse_selected)
        self.remove_location_link_btn.setEnabled(
            is_horse_selected and is_location_assigned
        )
