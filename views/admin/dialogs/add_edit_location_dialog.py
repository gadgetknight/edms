# views/admin/dialogs/add_edit_location_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Location Dialog
Version: 1.1.6
Purpose: Dialog for creating and editing practice locations with detailed address fields,
         phone, email, contact person, and auto-populating country code.
Last Updated: June 5, 2025
Author: Gemini

Changelog:
- v1.1.6 (2025-06-05):
    - In `validate_and_accept`, corrected the tuple unpacking for the `update_location`
      call to expect two return values (success, message) instead of three,
      resolving a ValueError.
- v1.1.5 (2025-06-02):
    - Added QLineEdit fields for Phone, Email, and Contact Person.
    - Updated QGridLayout in _setup_ui to include new fields.
    - Updated _populate_fields to load data for new fields.
    - Updated get_data to collect data from new fields.
    - Implemented _on_state_changed slot to auto-populate Country Code.
    - Modified _load_states_into_combobox to store country_code with state_code.
"""

import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QComboBox,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt

from controllers.location_controller import LocationController
from models import Location as LocationModel
from models import StateProvince as StateProvinceModel

from config.app_config import AppConfig
from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_HEADER_FOOTER,
    DARK_ITEM_HOVER,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_PRIMARY_ACTION,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_TEXT_TERTIARY,
    DARK_TEXT_SECONDARY,
    DARK_SUCCESS_ACTION,
    DARK_BORDER,
    DEFAULT_FONT_FAMILY,
)


class AddEditLocationDialog(QDialog):
    def __init__(
        self,
        parent_view,
        controller: LocationController,
        current_user_id: str,
        location: Optional[LocationModel] = None,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.controller = controller
        self.current_user_id = current_user_id
        self.location = location
        self.is_edit_mode = location is not None

        self.location_name_input: Optional[QLineEdit] = None
        self.contact_person_input: Optional[QLineEdit] = None
        self.address_line1_input: Optional[QLineEdit] = None
        self.address_line2_input: Optional[QLineEdit] = None
        self.city_input: Optional[QLineEdit] = None
        self.state_combo: Optional[QComboBox] = None
        self.zip_code_input: Optional[QLineEdit] = None
        self.country_code_input: Optional[QLineEdit] = None
        self.phone_input: Optional[QLineEdit] = None
        self.email_input: Optional[QLineEdit] = None
        self.is_active_checkbox: Optional[QCheckBox] = None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Location")
        self.setMinimumWidth(650)

        self._setup_palette()
        self._setup_ui()
        self._load_states_into_combobox()
        if self.is_edit_mode and self.location:
            self._populate_fields()

    def _get_form_input_style(self, base_bg=DARK_INPUT_FIELD_BACKGROUND) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background-color: {base_bg};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; 
                border-radius: 4px;
                padding: 6px 10px; 
                font-size: 13px; 
                min-height: 20px; 
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled, QComboBox:disabled {{ 
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QComboBox::drop-down {{ 
                border: none;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{ 
                color: {DARK_TEXT_SECONDARY}; 
            }}
            QComboBox QAbstractItemView {{ 
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }}
        """

    def _get_dialog_generic_button_style(self) -> str:
        return (
            f"QPushButton {{background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _setup_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_INPUT_FIELD_BACKGROUND))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK_ITEM_HOVER))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(Qt.GlobalColor.red))
        palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_HIGHLIGHT_BG))
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(DARK_HIGHLIGHT_TEXT)
        )
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background-color: transparent; padding-top: 3px; font-size: 13px;"
        )
        font_size = (
            AppConfig.DEFAULT_FONT_SIZE
            if hasattr(AppConfig, "DEFAULT_FONT_SIZE")
            else 10
        )
        label.setFont(QFont(DEFAULT_FONT_FAMILY, font_size))
        return label

    def _setup_ui(self):
        overall_layout = QVBoxLayout(self)
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(20, 20, 20, 15)
        grid_layout.setSpacing(10)
        grid_layout.setVerticalSpacing(15)

        self.location_name_input = QLineEdit()
        self.location_name_input.setPlaceholderText("e.g., Main Barn, Paddock A")

        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("Name of contact person")

        self.address_line1_input = QLineEdit()
        self.address_line1_input.setPlaceholderText("Street Address")

        self.address_line2_input = QLineEdit()
        self.address_line2_input.setPlaceholderText("Apartment, Suite, etc. (Optional)")

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City/Town")

        self.state_combo = QComboBox()
        self.state_combo.setPlaceholderText("Select State/Province")
        self.state_combo.currentIndexChanged.connect(self._on_state_changed)

        self.zip_code_input = QLineEdit()
        self.zip_code_input.setPlaceholderText("Zip/Postal Code")

        self.country_code_input = QLineEdit()
        self.country_code_input.setPlaceholderText("e.g., USA, CAN")
        self.country_code_input.setMaxLength(10)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Primary phone number")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Contact email address")

        self.is_active_checkbox = QCheckBox("Location is Active")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-size: 13px;"
        )

        grid_layout.addWidget(
            self._create_label("Location Name*:"), 0, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.location_name_input, 0, 1, 1, 3)
        grid_layout.addWidget(
            self._create_label("Contact Person:"), 1, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.contact_person_input, 1, 1, 1, 3)
        grid_layout.addWidget(
            self._create_label("Address Line 1:"), 2, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.address_line1_input, 2, 1, 1, 3)
        grid_layout.addWidget(
            self._create_label("Address Line 2:"), 3, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.address_line2_input, 3, 1, 1, 3)
        grid_layout.addWidget(
            self._create_label("City:"), 4, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.city_input, 4, 1)
        grid_layout.addWidget(
            self._create_label("State/Province:"), 4, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.state_combo, 4, 3)
        grid_layout.addWidget(
            self._create_label("Zip/Postal Code:"), 5, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.zip_code_input, 5, 1)
        grid_layout.addWidget(
            self._create_label("Country Code:"), 5, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.country_code_input, 5, 3)
        grid_layout.addWidget(
            self._create_label("Phone:"), 6, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.phone_input, 6, 1)
        grid_layout.addWidget(
            self._create_label("Email:"), 6, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.email_input, 6, 3)
        grid_layout.addWidget(
            self.is_active_checkbox, 7, 1, 1, 1, Qt.AlignmentFlag.AlignLeft
        )

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        grid_layout.setColumnMinimumWidth(0, 110)
        grid_layout.setColumnMinimumWidth(2, 110)

        form_style = self._get_form_input_style()
        for field in [
            self.location_name_input,
            self.contact_person_input,
            self.address_line1_input,
            self.address_line2_input,
            self.city_input,
            self.state_combo,
            self.zip_code_input,
            self.country_code_input,
            self.phone_input,
            self.email_input,
        ]:
            if field:
                field.setStyleSheet(form_style)

        overall_layout.addLayout(grid_layout)
        overall_layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        generic_button_style = self._get_dialog_generic_button_style()
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(generic_button_style)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_button_specific_style = (
                    f"background-color: {DARK_SUCCESS_ACTION}; color: white;"
                )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ {ok_button_specific_style} }}"
                )

        overall_layout.addWidget(self.button_box)

    def _load_states_into_combobox(self):
        if not self.state_combo:
            return
        self.state_combo.addItem("", None)
        session = None
        try:
            from config.database_config import db_manager

            session = db_manager.get_session()
            states: List[StateProvinceModel] = (
                session.query(StateProvinceModel)
                .filter(StateProvinceModel.is_active == True)
                .order_by(
                    StateProvinceModel.country_code, StateProvinceModel.state_name
                )
                .all()
            )
            for state in states:
                display_name = f"{state.state_name} ({state.state_code})"
                self.state_combo.addItem(
                    display_name,
                    {
                        "state_code": state.state_code,
                        "country_code": state.country_code,
                    },
                )
            self.logger.info(f"Loaded {len(states)} states into combobox.")
        except Exception as e:
            self.logger.error(f"Error loading states into combobox: {e}", exc_info=True)
            QMessageBox.warning(
                self, "Data Load Error", "Could not load states for selection."
            )
        finally:
            if session:
                session.close()

    def _on_state_changed(self, index: int):
        if not self.state_combo or not self.country_code_input:
            return
        selected_data = self.state_combo.itemData(index)
        if selected_data and isinstance(selected_data, dict):
            country_code = selected_data.get("country_code", "")
            self.country_code_input.setText(country_code)
        else:
            self.country_code_input.clear()

    def _populate_fields(self):
        if self.location:
            self.location_name_input.setText(self.location.location_name or "")
            self.contact_person_input.setText(self.location.contact_person or "")
            self.address_line1_input.setText(self.location.address_line1 or "")
            self.address_line2_input.setText(self.location.address_line2 or "")
            self.city_input.setText(self.location.city or "")
            if self.location.state_code:
                for i in range(self.state_combo.count()):
                    item_data = self.state_combo.itemData(i)
                    if (
                        item_data
                        and isinstance(item_data, dict)
                        and item_data.get("state_code") == self.location.state_code
                    ):
                        self.state_combo.setCurrentIndex(i)
                        break
                else:
                    self.logger.warning(
                        f"State code '{self.location.state_code}' not found in combobox. Location: {self.location.location_name}"
                    )
            else:
                self.state_combo.setCurrentIndex(0)
            self.zip_code_input.setText(self.location.zip_code or "")
            self.country_code_input.setText(self.location.country_code or "")
            self.phone_input.setText(self.location.phone or "")
            self.email_input.setText(self.location.email or "")
            self.is_active_checkbox.setChecked(self.location.is_active)

    def get_data(self) -> Dict[str, Any]:
        selected_state_code = None
        if self.state_combo.currentIndex() > 0:
            item_data = self.state_combo.currentData()
            if item_data and isinstance(item_data, dict):
                selected_state_code = item_data.get("state_code")

        return {
            "location_name": self.location_name_input.text(),
            "contact_person": self.contact_person_input.text(),
            "address_line1": self.address_line1_input.text(),
            "address_line2": self.address_line2_input.text(),
            "city": self.city_input.text(),
            "state_code": selected_state_code,
            "zip_code": self.zip_code_input.text(),
            "country_code": self.country_code_input.text(),
            "phone": self.phone_input.text(),
            "email": self.email_input.text(),
            "is_active": self.is_active_checkbox.isChecked(),
        }

    def validate_and_accept(self):
        data = self.get_data()
        is_valid, errors = self.controller.validate_location_data(
            data,
            is_new=(not self.is_edit_mode),
            location_id_to_check_for_unique=(
                self.location.location_id
                if self.is_edit_mode and self.location
                else None
            ),
        )
        if not is_valid:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct the following errors:\n- " + "\n- ".join(errors),
            )
            return

        try:
            if self.is_edit_mode and self.location:
                # MODIFIED: Correctly unpack the two return values from update_location
                success, message = self.controller.update_location(
                    self.location.location_id, data, self.current_user_id
                )
            else:
                # create_location returns three values
                success, message, _ = self.controller.create_location(
                    data, self.current_user_id
                )

            if success:
                if hasattr(self.parent_view, "show_info") and callable(
                    getattr(self.parent_view, "show_info")
                ):
                    self.parent_view.show_info("Success", message)
                else:
                    self.logger.warning(
                        "parent_view does not have show_info method. Using local QMessageBox."
                    )
                    QMessageBox.information(self, "Success", message)
                super().accept()
            else:
                QMessageBox.critical(
                    self, "Error", message or "An unknown error occurred."
                )
        except Exception as e:
            self.logger.error(f"Error during location save/update: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Operation Failed", f"An unexpected error occurred: {e}"
            )
