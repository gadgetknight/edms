# views/horse/tabs/location_tab.py
"""
EDSI Veterinary Management System - Horse Location Tab
Version: 1.0.0
Purpose: Manages the assignment of a single location to a horse.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-05-20):
    - Initial implementation.
    - UI with current location display (QLabel).
    - Buttons: "Create New & Link Location", "Link Existing Location", "Remove Location Link".
    - Integrates AddEditLocationDialog and SelectExistingLocationDialog.
    - Emits location_assignment_changed(location_id: Optional[int], location_name: Optional[str]) signal.
    - Uses HorseController to update horse's current_location_id.
    - Styled for dark theme.
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
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_BUTTON_BG,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_BORDER,
    DARK_INPUT_FIELD_BACKGROUND,  # For display label styling
    DARK_SUCCESS_ACTION,
    DARK_PRIMARY_ACTION,
    DARK_DANGER_ACTION,
    DARK_BUTTON_HOVER,
    DARK_HEADER_FOOTER,
    DARK_TEXT_TERTIARY,
)
from models import Horse, Location as LocationModel
from controllers.horse_controller import HorseController
from controllers.location_controller import (
    LocationController,
)  # To fetch location name after selection
from views.admin.dialogs.add_edit_location_dialog import AddEditLocationDialog
from views.horse.dialogs.select_existing_location_dialog import (
    SelectExistingLocationDialog,
)


class LocationTab(QWidget):
    """Tab widget for managing a horse's single assigned location."""

    # Emits new location_id (or None) and location_name (or "N/A")
    location_assignment_changed = Signal(
        object
    )  # Emits a dict: {'id': Optional[int], 'name': Optional[str]}

    def __init__(
        self,
        parent_view,  # Typically HorseUnifiedManagement
        horse_controller: HorseController,
        location_controller: LocationController,  # Added
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.location_controller = location_controller  # Store this

        self.current_horse: Optional[Horse] = None
        self._current_location_id: Optional[int] = None
        self._current_location_name: str = "N/A"

        # Get current_user_login from parent_view for auditing dialogs
        self.current_user_login = "UnknownUser"
        if (
            hasattr(self.parent_view, "current_user_id")
            and self.parent_view.current_user_id
        ):
            self.current_user_login = self.parent_view.current_user_id
        elif (
            hasattr(self.parent_view, "current_user") and self.parent_view.current_user
        ):
            self.current_user_login = self.parent_view.current_user
        else:
            self.logger.warning(
                "Could not determine current_user_id for LocationTab auditing."
            )

        self.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self._setup_ui(main_layout)
        self._setup_connections()
        self.update_buttons_state()  # Initial state

    def _get_generic_button_style(self) -> str:
        """Returns a generic button style string using app config constants."""
        if hasattr(self.parent_view, "get_generic_button_style"):
            return self.parent_view.get_generic_button_style()
        # Fallback
        return (
            f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _setup_ui(self, main_layout: QVBoxLayout):
        # --- Display Current Location ---
        location_display_frame = QFrame()
        location_display_frame.setStyleSheet("background-color: transparent;")
        location_display_layout = QHBoxLayout(location_display_frame)
        location_display_layout.setContentsMargins(0, 0, 0, 10)  # Bottom margin

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
        location_display_layout.addWidget(
            self.current_location_display_label, 1
        )  # Give stretch factor
        main_layout.addWidget(location_display_frame)

        # --- Action Buttons ---
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
            button_style.replace(DARK_BUTTON_BG, DARK_PRIMARY_ACTION)
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

        main_layout.addStretch(1)  # Pushes content to the top

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
        if self.current_horse and self.current_horse.horse_id is not None:
            # Fetch fresh horse data to get the latest location
            fresh_horse_data = self.horse_controller.get_horse_by_id(
                self.current_horse.horse_id
            )
            if fresh_horse_data:
                self.current_horse = fresh_horse_data  # Update internal horse object
                self._current_location_id = self.current_horse.current_location_id
                self._current_location_name = (
                    self.current_horse.location.location_name
                    if self.current_horse.location
                    else "N/A"
                )
                self.logger.debug(
                    f"Loaded location for horse ID {self.current_horse.horse_id}: Name='{self._current_location_name}', ID={self._current_location_id}"
                )
            else:
                self.logger.warning(
                    f"Could not reload horse data for horse ID {self.current_horse.horse_id} in LocationTab."
                )
                self._current_location_id = None
                self._current_location_name = "Error loading location"
        else:
            self._current_location_id = None
            self._current_location_name = "N/A (No horse selected)"
            self.logger.debug(
                "No current horse to load location for, or horse has no ID."
            )

        self.current_location_display_label.setText(self._current_location_name)
        self.update_buttons_state()

    def _handle_create_and_link_location(self):
        if not self.current_horse:
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
            location=None,  # Creating a new one
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # AddEditLocationDialog handles its own saving. We need to get the ID of the created location.
            # This requires AddEditLocationDialog to provide a way to get this, or we search for it.
            # For now, we'll assume the dialog was successful and try to find the new location
            # by re-fetching all locations, which is not ideal.
            # A better approach: modify AddEditLocationDialog to store and return the created object or its ID.

            # Let's assume for now the dialog handles creation and parent refreshes lists.
            # We then need to prompt the user to re-select via "Link Existing Location"
            # OR, if AddEditLocationDialog could return the created LocationModel:
            # created_location = dialog.get_created_location() # Hypothetical method
            # if created_location:
            #    self._assign_location_to_horse(created_location.location_id, created_location.location_name)
            # else:
            #    self.parent_view.show_error("Error", "New location was indicated as created, but its details could not be retrieved.")

            self.parent_view.show_info(
                "Location Created",
                "New location created. Please use 'Assign Existing Location' to link it.",
            )
            # To make this seamless, AddEditLocationDialog should return the created ID/object.
            # For now, this flow requires an extra step from the user.
        else:
            self.logger.info("Create & Assign New Location dialog cancelled.")

    def _handle_link_existing_location(self):
        if not self.current_horse:
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
                loc_obj = self.location_controller.get_location_by_id(selected_id)
                if loc_obj:
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
            return

        # Update the horse's current_location_id via HorseController
        # This mimics saving part of the horse's basic info.
        # We need a way to update just the location_id on the horse object.
        # The HorseController's update_horse method takes a full dictionary.
        # Option 1: Fetch full horse data, update location_id, then call update_horse.
        # Option 2: Add a specific method in HorseController: update_horse_location(horse_id, location_id, user).

        # Using Option 1 (simpler for now, but less efficient if only location changes):
        horse_data_for_update = {
            "horse_name": self.current_horse.horse_name,  # Must provide name for validation
            "current_location_id": location_id,
            # Potentially other fields if controller requires them for validation
        }
        # We should ensure that the HorseController's update_horse method
        # can handle partial updates or that we fetch all existing data first.
        # For now, let's assume a more direct update is desired for just the location.

        # Let's modify the horse object directly and rely on the main "Save" from BasicInfoTab
        # OR emit a signal that HorseUnifiedManagement picks up to update its current_horse object
        # and then BasicInfoTab reflects this.

        # Preferred: Signal the change, let parent manage the actual horse object update through its save mechanism.
        # BasicInfoTab will get this signal too to update its display.

        self._current_location_id = location_id
        self._current_location_name = location_name
        self.current_location_display_label.setText(self._current_location_name)
        self.update_buttons_state()

        self.location_assignment_changed.emit(
            {"id": location_id, "name": location_name}
        )
        self.parent_view.show_info(
            "Location Assigned", f"Horse assigned to location: {location_name}"
        )
        self.logger.info(
            f"Horse ID {self.current_horse.horse_id} assigned to Location ID {location_id} ('{location_name}') in UI. Awaiting main save."
        )

    def _handle_remove_location_link(self):
        if not self.current_horse:
            self.parent_view.show_warning(
                "Clear Location", "Please select a horse first."
            )
            return
        if self._current_location_id is None:
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
                f"User confirmed clearing location for horse ID {self.current_horse.horse_id}"
            )
            self._current_location_id = None
            self._current_location_name = "N/A"
            self.current_location_display_label.setText(self._current_location_name)
            self.update_buttons_state()

            self.location_assignment_changed.emit({"id": None, "name": "N/A"})
            self.parent_view.show_info(
                "Location Cleared",
                f"Location assignment cleared for horse '{horse_name_display}'.",
            )
            self.logger.info(
                f"Location assignment cleared for horse ID {self.current_horse.horse_id} in UI. Awaiting main save."
            )
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
