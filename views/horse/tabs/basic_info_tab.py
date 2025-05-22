# views/horse/tabs/basic_info_tab.py

"""
EDSI Veterinary Management System - Horse Basic Info Tab
Version: 1.2.5
Purpose: Tab for displaying and editing basic horse information.
         Corrected all missing color constant imports for styling.
Last Updated: May 21, 2025
Author: Gemini

Changelog:
- v1.2.5 (2025-05-21):
    - Ensured all color constants used in `get_tab_input_style` are imported
      from `config.app_config` (DARK_TEXT_SECONDARY, DARK_HEADER_FOOTER,
      DARK_WIDGET_BACKGROUND, DARK_HIGHLIGHT_BG, DARK_HIGHLIGHT_TEXT,
      DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_TEXT_TERTIARY).
- v1.2.4 (2025-05-21):
    - Re-verified and ensured all necessary color constants used in
      `get_tab_input_style` (DARK_TEXT_SECONDARY, DARK_HEADER_FOOTER, etc.)
      are imported from `config.app_config`.
- v1.2.3 (2025-05-21):
    - Added missing imports for color constants (DARK_TEXT_SECONDARY, etc.)
      from `config.app_config` to resolve NameError in `get_tab_input_style`.
- v1.2.2 (2025-05-21):
    - Added unconditional print statements in `set_new_mode` and
      `set_form_read_only` to trace execution and check widget states.
- v1.2.1 (2025-05-21):
    - Adjusted UI for location display width (initial attempt, may need more).
    - Added logging for location updates and data modifications.
- v1.2.0 (2025-05-18):
    - Initial implementation of the Basic Info Tab.
    - Connections for save, discard, data modification.
"""

import logging
from datetime import date, datetime
from typing import Optional, Dict, Union

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QTextEdit,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from controllers.horse_controller import HorseController
from models import Horse, Species, Location as LocationModel
from config.app_config import (
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_BORDER,
    DARK_PRIMARY_ACTION,
    DEFAULT_FONT_FAMILY,
    DARK_TEXT_SECONDARY,
    DARK_WIDGET_BACKGROUND,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_HEADER_FOOTER,
    DARK_BUTTON_BG,  # Added for completeness
    DARK_BUTTON_HOVER,  # Added for completeness
    DARK_TEXT_TERTIARY,  # Added for completeness
    DARK_ITEM_HOVER,  # Added as it's used in BaseView and good for consistency
)


class BasicInfoTab(QWidget):
    data_modified = Signal()
    save_requested = Signal()
    discard_requested = Signal()
    toggle_active_requested = Signal(bool)
    select_location_requested = Signal()

    def __init__(
        self, parent_view: QWidget, horse_controller: HorseController, parent=None
    ):
        super().__init__(parent)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_horse: Optional[Horse] = None
        self._has_modifications = False
        self.species_list: list[Species] = []
        self._setup_ui()
        self._connect_signals()
        self.set_form_read_only(True)
        self.update_buttons_state(False, False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.horse_name_input = QLineEdit()
        form_layout.addRow("Horse Name:", self.horse_name_input)
        self.account_number_input = QLineEdit()
        form_layout.addRow("Account #:", self.account_number_input)
        self.species_combo = QComboBox()
        self.load_species_data()
        form_layout.addRow("Species:", self.species_combo)
        self.breed_input = QLineEdit()
        form_layout.addRow("Breed:", self.breed_input)
        self.color_input = QLineEdit()
        form_layout.addRow("Color:", self.color_input)
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["", "Stallion", "Gelding", "Mare", "Colt", "Filly"])
        form_layout.addRow("Sex:", self.sex_combo)
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDisplayFormat("MM/dd/yyyy")
        self.dob_edit.setDate(QDate.currentDate().addYears(-5))
        form_layout.addRow("Date of Birth:", self.dob_edit)

        location_display_layout = QHBoxLayout()
        self.location_display = QLineEdit()
        self.location_display.setReadOnly(True)
        self.location_display.setPlaceholderText("N/A - Manage in Location Tab")
        self.location_display.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.change_location_btn = QPushButton("Change Location...")
        self.change_location_btn.setToolTip("Open location management for this horse")
        self.change_location_btn.clicked.connect(self._on_change_location_clicked)
        self.change_location_btn.setFixedWidth(150)
        location_display_layout.addWidget(self.location_display, 1)
        location_display_layout.addWidget(self.change_location_btn, 0)
        form_layout.addRow("Current Location:", location_display_layout)

        self.coggins_date_edit = QDateEdit()
        self.coggins_date_edit.setCalendarPopup(True)
        self.coggins_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.coggins_date_edit.setSpecialValueText("N/A")
        self.coggins_date_edit.setDate(QDate())
        form_layout.addRow("Coggins Date:", self.coggins_date_edit)
        self.microchip_input = QLineEdit()
        form_layout.addRow("Microchip #:", self.microchip_input)
        self.active_checkbox = QCheckBox("Horse is Active")
        self.active_checkbox.setChecked(True)
        form_layout.addRow(self.active_checkbox)
        notes_label = QLabel("Notes:")
        notes_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(80)
        form_layout.addRow(notes_label, self.notes_edit)

        layout.addLayout(form_layout)
        layout.addStretch(1)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.save_btn = QPushButton("💾 Save Changes")
        self.discard_btn = QPushButton("↩️ Discard Changes")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.discard_btn)
        layout.addLayout(button_layout)
        self.setStyleSheet(self.get_tab_input_style())

    def _on_change_location_clicked(self):
        self.logger.debug("Change Location button clicked on BasicInfoTab.")
        if (
            self.parent_view
            and hasattr(self.parent_view, "tab_widget")
            and self.parent_view.tab_widget
            and hasattr(self.parent_view, "location_tab")
            and self.parent_view.location_tab
        ):
            self.parent_view.tab_widget.setCurrentWidget(self.parent_view.location_tab)
        else:
            self.logger.warning(
                "Cannot switch to location tab: parent_view or its tabs not found."
            )

    def get_tab_input_style(self):
        return f"""
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                font-family: "{DEFAULT_FONT_FAMILY}";
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QTextEdit:disabled {{
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: transparent;
                width: 15px;
            }}
            QComboBox::down-arrow {{
                color: {DARK_TEXT_SECONDARY};
            }}
            QDateEdit::up-button, QDateEdit::down-button {{
                width: 18px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }}
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; /* Using theme variable */
                color: {DARK_TEXT_PRIMARY};    /* Using theme variable */
                border: 1px solid {DARK_BORDER}; /* Using theme variable */
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: 500;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {DARK_BUTTON_HOVER}; /* Using theme variable */
            }}
            QPushButton:disabled {{
                background-color: {DARK_HEADER_FOOTER}; /* Using theme variable */
                color: {DARK_TEXT_TERTIARY};    /* Using theme variable */
            }}
            QCheckBox {{
                color: {DARK_TEXT_PRIMARY};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
            }}
            QLabel {{
                color: {DARK_TEXT_SECONDARY};
                font-size: 13px;
                padding-top: 6px;
            }}
        """

    def _connect_signals(self):
        self.horse_name_input.textChanged.connect(self._on_data_modified)
        self.account_number_input.textChanged.connect(self._on_data_modified)
        self.species_combo.currentIndexChanged.connect(self._on_data_modified)
        self.breed_input.textChanged.connect(self._on_data_modified)
        self.color_input.textChanged.connect(self._on_data_modified)
        self.sex_combo.currentIndexChanged.connect(self._on_data_modified)
        self.dob_edit.dateChanged.connect(self._on_data_modified)
        self.coggins_date_edit.dateChanged.connect(self._on_data_modified)
        self.microchip_input.textChanged.connect(self._on_data_modified)
        self.notes_edit.textChanged.connect(self._on_data_modified)
        self.active_checkbox.stateChanged.connect(self._on_active_state_changed_handler)
        self.save_btn.clicked.connect(self.save_requested.emit)
        self.discard_btn.clicked.connect(self.discard_requested.emit)

    def _on_active_state_changed_handler(self, state: int):
        self.logger.debug(
            f"Active checkbox state changed to: {state == Qt.CheckState.Checked.value}"
        )
        self._on_data_modified()

    def _on_data_modified(self):
        if not self._has_modifications:
            self._has_modifications = True
            self.data_modified.emit()
            self.update_buttons_state(True, self.current_horse is not None)

    def load_species_data(self):
        self.species_list = self.horse_controller.get_all_species()
        self.species_combo.clear()
        self.species_combo.addItem("", None)
        for species_obj in self.species_list:
            self.species_combo.addItem(species_obj.name, species_obj.species_id)
        self.logger.info(f"Loaded {len(self.species_list)} species into combobox.")

    def populate_fields(self, horse: Horse):
        self.current_horse = horse
        self.logger.info(
            f"Populating BasicInfoTab for horse: {horse.horse_name if horse else 'None'}"
        )
        if horse:
            self.horse_name_input.setText(horse.horse_name or "")
            self.account_number_input.setText(horse.account_number or "")
            if horse.species_id:
                for i in range(self.species_combo.count()):
                    if self.species_combo.itemData(i) == horse.species_id:
                        self.species_combo.setCurrentIndex(i)
                        break
            else:
                self.species_combo.setCurrentIndex(0)
            self.breed_input.setText(horse.breed or "")
            self.color_input.setText(horse.color or "")
            sex_index = self.sex_combo.findText(horse.sex or "")
            self.sex_combo.setCurrentIndex(sex_index if sex_index != -1 else 0)
            self.dob_edit.setDate(
                QDate.fromString(str(horse.date_of_birth), "yyyy-MM-dd")
                if horse.date_of_birth
                else QDate()
            )
            self.coggins_date_edit.setDate(
                QDate.fromString(str(horse.coggins_date), "yyyy-MM-dd")
                if horse.coggins_date
                else QDate()
            )
            self.microchip_input.setText(horse.microchip_number or "")
            self.notes_edit.setPlainText(horse.notes or "")
            self.active_checkbox.setChecked(horse.is_active)
            location_name = (
                horse.location.location_name
                if horse.location
                else "N/A - Manage in Location Tab"
            )
            self.update_displayed_location(horse.current_location_id, location_name)
            self.set_form_read_only(True)
            self.update_buttons_state(False, True)
            self._has_modifications = False
        else:
            self.clear_fields()
            self.set_form_read_only(True)
            self.update_buttons_state(False, False)

    def update_displayed_location(
        self, location_id: Optional[int], location_name: Optional[str]
    ):
        self.logger.debug(
            f"BasicInfoTab.update_displayed_location: ID={location_id}, Name='{location_name}'"
        )
        new_display_text = (
            location_name if location_name else "N/A - Manage in Location Tab"
        )
        if self.location_display.text() != new_display_text:
            self.location_display.setText(new_display_text)
            if not self.horse_name_input.isReadOnly():
                self.logger.debug(
                    "Location display changed while form is editable, marking as modified."
                )
                self._on_data_modified()

    def clear_fields(self):
        self.current_horse = None
        self.horse_name_input.clear()
        self.account_number_input.clear()
        self.species_combo.setCurrentIndex(0)
        self.breed_input.clear()
        self.color_input.clear()
        self.sex_combo.setCurrentIndex(0)
        self.dob_edit.setDate(QDate.currentDate().addYears(-5))
        self.coggins_date_edit.setDate(QDate())
        self.microchip_input.clear()
        self.notes_edit.clear()
        self.active_checkbox.setChecked(True)
        self.location_display.setText("N/A - Manage in Location Tab")
        self._has_modifications = False
        self.update_buttons_state(False, False)

    def set_new_mode(self):
        print("--- BASICINFOTAB.SET_NEW_MODE CALLED (UNCONDITIONAL PRINT) ---")
        self.logger.info("BasicInfoTab set to new mode.")
        self.clear_fields()
        self.set_form_read_only(False)
        self.update_buttons_state(True, False)
        self._has_modifications = True
        self.horse_name_input.setFocus()

    def set_form_read_only(self, read_only: bool):
        print(
            f"--- BASICINFOTAB.SET_FORM_READ_ONLY({read_only}) CALLED (UNCONDITIONAL PRINT) ---"
        )
        self.logger.debug(f"BasicInfoTab.set_form_read_only called with: {read_only}")
        self.horse_name_input.setReadOnly(read_only)
        self.account_number_input.setReadOnly(read_only)
        self.species_combo.setEnabled(not read_only)
        self.breed_input.setReadOnly(read_only)
        self.color_input.setReadOnly(read_only)
        self.sex_combo.setEnabled(not read_only)
        self.dob_edit.setReadOnly(read_only)
        self.dob_edit.setEnabled(not read_only)
        self.coggins_date_edit.setReadOnly(read_only)
        self.coggins_date_edit.setEnabled(not read_only)
        self.microchip_input.setReadOnly(read_only)
        self.notes_edit.setReadOnly(read_only)
        print(
            f"--- BASICINFOTAB.SET_FORM_READ_ONLY: horse_name_input.isReadOnly() = {self.horse_name_input.isReadOnly()} ---"
        )
        print(
            f"--- BASICINFOTAB.SET_FORM_READ_ONLY: horse_name_input.isEnabled() = {self.horse_name_input.isEnabled()} ---"
        )

    def update_buttons_state(self, has_modifications: bool, is_existing_record: bool):
        self.save_btn.setEnabled(has_modifications)
        self.discard_btn.setEnabled(has_modifications)

    def get_data(self) -> Optional[Dict[str, Union[str, int, bool, date, None]]]:
        if not self._has_modifications and self.current_horse:
            if not self.current_horse:
                pass
        species_id_data = self.species_combo.currentData()
        dob_qdate = self.dob_edit.date()
        dob_iso = (
            dob_qdate.toString("yyyy-MM-dd")
            if dob_qdate.isValid() and not dob_qdate.isNull()
            else None
        )
        coggins_qdate = self.coggins_date_edit.date()
        coggins_iso = (
            coggins_qdate.toString("yyyy-MM-dd")
            if coggins_qdate.isValid() and not coggins_qdate.isNull()
            else None
        )
        data = {
            "horse_name": self.horse_name_input.text().strip() or None,
            "account_number": self.account_number_input.text().strip() or None,
            "species_id": species_id_data,
            "breed": self.breed_input.text().strip() or None,
            "color": self.color_input.text().strip() or None,
            "sex": (
                self.sex_combo.currentText()
                if self.sex_combo.currentIndex() > 0
                else None
            ),
            "date_of_birth": dob_iso,
            "coggins_date": coggins_iso,
            "microchip_number": self.microchip_input.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "is_active": self.active_checkbox.isChecked(),
            "current_location_id": (
                self.current_horse.current_location_id if self.current_horse else None
            ),
        }
        if self.current_horse and hasattr(self.current_horse, "current_location_id"):
            data["current_location_id"] = self.current_horse.current_location_id
        self.logger.debug(f"Data gathered from BasicInfoTab: {data}")
        return data
