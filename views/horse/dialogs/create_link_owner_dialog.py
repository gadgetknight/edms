# views/horse/dialogs/create_link_owner_dialog.py

"""
EDSI Veterinary Management System - Create and Link Owner Dialog
Version: 1.1.2
Purpose: Dialog to create a new owner and link them to a horse.
         Corrects order of initialization for country_input.
Last Updated: May 17, 2025
Author: Claude Assistant

Changelog:
- v1.1.2 (2025-05-17):
    - Fixed AttributeError by defining `self.country_input` before calling `populate_states_combo`.
- v1.1.1 (2025-05-17):
    - Set default text for `country_input` to "USA".
    - `country_name` collected from form but not passed to Owner constructor.
- v1.1.0 (2025-05-17):
    - Added Mobile Phone input field.
    - Phone fields are no longer client-side validated as required.
    - Owner creation (controller call) moved into `validate_and_accept`.
    - Dialog remains open if owner creation fails at controller level.
    - `get_data` returns the created Owner object and percentage for linking.
- v1.0.0 (2025-05-16): Initial extraction from horse_unified_management.py.
"""

import logging
from typing import Optional, Dict, List  # Added List for type hinting

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from config.app_config import AppConfig
from controllers.owner_controller import OwnerController
from models import Owner


class CreateAndLinkOwnerDialog(QDialog):
    """Dialog to create a new owner and link them to a horse with an ownership percentage."""

    def __init__(self, parent_horse_screen, horse_name: str, current_user_id: str):
        super().__init__(parent_horse_screen)
        self.horse_name = horse_name
        self.current_user_id = current_user_id
        self.setWindowTitle(f"Create New Owner & Link to {self.horse_name}")
        self.setMinimumWidth(750)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.owner_controller = OwnerController()
        self.parent_screen = parent_horse_screen
        self.newly_created_owner: Optional[Owner] = None

        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)

        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setSpacing(15)
        main_dialog_layout.setContentsMargins(15, 15, 15, 15)

        form_fields_grid_layout = QGridLayout()
        form_fields_grid_layout.setSpacing(25)
        form_layout_left = QFormLayout()
        form_layout_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout_left.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout_left.setSpacing(10)
        form_layout_right = QFormLayout()
        form_layout_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout_right.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout_right.setSpacing(10)

        self.setStyleSheet(
            f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color:transparent; padding-top:3px;}}"
        )
        input_style = self.parent_screen.get_form_input_style()

        # Column 1 Fields
        self.account_number_input = QLineEdit()
        self.account_number_input.setPlaceholderText("Account Number (Optional)")
        self.account_number_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("Account Number:"), self.account_number_input)
        self.farm_name_input = QLineEdit()
        self.farm_name_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("Farm Name:"), self.farm_name_input)
        self.first_name_input = QLineEdit()
        self.first_name_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("First Name:"), self.first_name_input)
        self.last_name_input = QLineEdit()
        self.last_name_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("Last Name:"), self.last_name_input)
        self.address1_input = QLineEdit()
        self.address1_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("Street Address*:"), self.address1_input)
        self.address2_input = QLineEdit()
        self.address2_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("Address Line 2:"), self.address2_input)
        self.city_input = QLineEdit()
        self.city_input.setStyleSheet(input_style)
        form_layout_left.addRow(QLabel("City*:"), self.city_input)

        # Column 2 Fields
        self.state_combo = QComboBox()
        self.state_combo.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("State/Province*:"), self.state_combo)

        self.zip_code_input = QLineEdit()
        self.zip_code_input.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("Zip/Postal Code*:"), self.zip_code_input)

        # --- Define country_input BEFORE populate_states_combo ---
        self.country_input = QLineEdit()
        self.country_input.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("Country:"), self.country_input)
        # --- End define country_input ---

        self.populate_states_combo()  # Now it's safe to call this

        self.phone1_input = QLineEdit()
        self.phone1_input.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("Primary Phone:"), self.phone1_input)
        self.mobile_phone_input = QLineEdit()
        self.mobile_phone_input.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("Mobile Phone:"), self.mobile_phone_input)
        self.email_input = QLineEdit()
        self.email_input.setStyleSheet(input_style)
        form_layout_right.addRow(QLabel("Email:"), self.email_input)
        self.is_active_checkbox = QCheckBox("Owner is Active")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.setStyleSheet(
            f"QCheckBox {{ color: {AppConfig.DARK_TEXT_SECONDARY}; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        form_layout_right.addRow("", self.is_active_checkbox)

        form_fields_grid_layout.addLayout(form_layout_left, 0, 0)
        form_fields_grid_layout.addLayout(form_layout_right, 0, 1)
        main_dialog_layout.addLayout(form_fields_grid_layout)

        percentage_frame = QFrame()
        percentage_layout = QHBoxLayout(percentage_frame)
        percentage_label = QLabel(f"Ownership % for {self.horse_name}:*")
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setRange(0.00, 100.00)
        self.percentage_spinbox.setDecimals(2)
        self.percentage_spinbox.setValue(100.00)
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setStyleSheet(input_style)
        percentage_layout.addWidget(percentage_label)
        percentage_layout.addStretch()
        percentage_layout.addWidget(self.percentage_spinbox)
        main_dialog_layout.addWidget(percentage_frame)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Save Owner & Link"
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        generic_button_style = self.parent_screen.get_generic_button_style()
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(generic_button_style)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = AppConfig.DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    .replace(AppConfig.DARK_BUTTON_BG, ok_bg_color)
                    .replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white;")
                )
        main_dialog_layout.addWidget(self.button_box)

    def populate_states_combo(self):
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states: List[Dict[str, any]] = ref_data.get(
                "states", []
            )  # Ensure type hint for states
            self.state_combo.addItem("", None)

            default_country_set_from_state = False
            # Iterate through states to populate combo and potentially derive country
            for state_data in states:
                self.state_combo.addItem(state_data["name"], state_data["id"])
                # If a state is selected AND it has a country_code AND country field is empty, set it.
                # This part of logic might be better tied to state_combo.currentIndexChanged signal
                # For now, we'll just try to set it if the *first* state with country_code is added
                # and country_input is still blank.
                if not default_country_set_from_state and state_data.get(
                    "country_code"
                ):
                    if (
                        not self.country_input.text().strip()
                    ):  # Check if country_input is actually empty
                        self.country_input.setText(state_data["country_code"])
                        default_country_set_from_state = True

            # If after populating states, country field is still empty, default to USA
            if not self.country_input.text().strip():
                self.country_input.setText("USA")

        except Exception as e:
            self.logger.error(f"Error populating states combo: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", "Could not load states for the form.")

    def _collect_owner_data_from_form(self) -> Dict:
        # ... (rest of the method is the same)
        return {
            "account_number": self.account_number_input.text().strip(),
            "farm_name": self.farm_name_input.text().strip(),
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "address_line1": self.address1_input.text().strip(),
            "address_line2": self.address2_input.text().strip(),
            "city": self.city_input.text().strip(),
            "state_code": self.state_combo.currentData(),
            "zip_code": self.zip_code_input.text().strip(),
            "country_name": self.country_input.text().strip(),
            "phone": self.phone1_input.text().strip(),
            "mobile_phone": self.mobile_phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "is_active": self.is_active_checkbox.isChecked(),
        }

    def validate_and_accept(self):
        # ... (rest of the method is the same)
        client_errors = []
        owner_details_for_validation = self._collect_owner_data_from_form()

        if (
            not owner_details_for_validation["first_name"]
            and not owner_details_for_validation["farm_name"]
            and not owner_details_for_validation["last_name"]
        ):
            client_errors.append(
                "At least First Name, Last Name, or Farm Name is required."
            )
        if not owner_details_for_validation["address_line1"]:
            client_errors.append("Street Address is required.")
        if not owner_details_for_validation["city"]:
            client_errors.append("City is required.")
        if not owner_details_for_validation["state_code"]:
            client_errors.append("State/Province is required.")
        if not owner_details_for_validation["zip_code"]:
            client_errors.append("Zip/Postal Code is required.")

        percentage = self.percentage_spinbox.value()
        if not (0 <= percentage <= 100):
            client_errors.append("Ownership percentage must be between 0 and 100.")

        if client_errors:
            QMessageBox.warning(
                self,
                "Input Error",
                "\n- ".join(["Please correct the following:"] + client_errors),
            )
            return

        self.logger.debug(
            f"Attempting to create owner with data: {owner_details_for_validation}"
        )
        success, message, new_owner_obj = self.owner_controller.create_master_owner(
            owner_details_for_validation, self.current_user_id
        )

        if success and new_owner_obj:
            self.newly_created_owner = new_owner_obj
            self.logger.info(
                f"Owner successfully created by controller (ID: {new_owner_obj.owner_id}). Dialog will accept."
            )
            super().accept()
        else:
            self.logger.warning(f"Owner creation failed via controller: {message}")
            QMessageBox.critical(
                self,
                "Owner Creation Failed",
                f"Could not create owner:\n{message}\nPlease correct the data and try again.",
            )

    def get_data(self) -> Optional[dict]:
        # ... (rest of the method is the same)
        if self.result() == QDialog.DialogCode.Accepted and self.newly_created_owner:
            return {
                "new_owner_object": self.newly_created_owner,
                "percentage": self.percentage_spinbox.value(),
            }
        return None
