# views/horse/tabs/basic_info_tab.py
"""
EDSI Veterinary Management System - Horse Basic Info Tab
Version: 1.2.10
Purpose: UI for displaying and editing basic information of a horse.
         - Removed Species-related UI elements and logic.
Last Updated: May 23, 2025
Author: Gemini (based on user's v1.2.9)

Changelog:
- v1.2.10 (2025-05-23):
    - Removed `species_combo` QComboBox and its label.
    - Removed `load_species_data` method and its call, resolving AttributeError
      for `horse_controller.get_all_species`.
    - Removed `species_id` from data dictionary in `_get_data_from_form` and
      when populating the form in `populate_form_data`.
    - Adjusted layout due to removal of species field.
- v1.2.9 (User Stated Version - Assuming similar to GitHub v1.1.0 with minor changes):
    - User's current version.
"""
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QCheckBox,
    QTextEdit,
    QLabel,
    QComboBox,
    QSizePolicy,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QDoubleValidator

from controllers.horse_controller import HorseController

if TYPE_CHECKING:
    from models import Horse


class BasicInfoTab(QWidget):
    data_changed = Signal()
    edit_mode_toggled = Signal(bool)

    SEX_OPTIONS = ["Unknown", "Mare", "Stallion", "Gelding", "Colt", "Filly"]

    def __init__(
        self,
        horse_controller: Optional[HorseController] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse_controller = (
            horse_controller if horse_controller else HorseController()
        )
        self.current_horse_id: Optional[int] = None
        self._is_new_mode: bool = False
        self._has_modifications: bool = False
        self._suppress_data_changed_signal = False

        self._setup_ui()
        self.set_form_read_only(True)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        self.form_layout = QFormLayout(content_widget)
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        self.form_layout.setSpacing(10)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.horse_name_input = QLineEdit()
        self.horse_name_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Horse Name:", self.horse_name_input)

        self.account_number_input = QLineEdit()
        self.account_number_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Account Number:", self.account_number_input)

        # Species field and its logic REMOVED
        # self.species_combo = QComboBox() ...
        # self.form_layout.addRow("Species:", self.species_combo)
        # self.load_species_data()

        self.breed_input = QLineEdit()
        self.breed_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Breed:", self.breed_input)

        self.color_input = QLineEdit()
        self.color_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Color:", self.color_input)

        self.sex_combo = QComboBox()
        self.sex_combo.addItems(self.SEX_OPTIONS)
        self.sex_combo.currentIndexChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Sex:", self.sex_combo)

        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-5))
        self.dob_input.setMaximumDate(QDate.currentDate())
        self.dob_input.dateChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Date of Birth:", self.dob_input)

        self.height_input = QLineEdit()
        double_validator = QDoubleValidator(0.00, 99.99, 2)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.height_input.setValidator(double_validator)
        self.height_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Height (Hands):", self.height_input)

        self.chip_number_input = QLineEdit()
        self.chip_number_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Chip Number:", self.chip_number_input)

        self.tattoo_number_input = QLineEdit()
        self.tattoo_number_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Tattoo Number:", self.tattoo_number_input)

        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        self.description_input.textChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Description/Markings:", self.description_input)

        self.coggins_date_input = QDateEdit()
        self.coggins_date_input.setCalendarPopup(True)
        self.coggins_date_input.setDisplayFormat("yyyy-MM-dd")
        self.coggins_date_input.setSpecialValueText("N/A")
        self.coggins_date_input.setDate(QDate(2000, 1, 1))
        self.coggins_date_input.dateChanged.connect(self._on_data_changed)
        self.form_layout.addRow("Coggins Date:", self.coggins_date_input)

        self.is_active_checkbox = QCheckBox("Active")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.stateChanged.connect(self._on_data_changed)
        self.is_active_checkbox.stateChanged.connect(
            self._toggle_date_deceased_visibility
        )

        self.date_deceased_input = QDateEdit()
        self.date_deceased_input.setCalendarPopup(True)
        self.date_deceased_input.setDisplayFormat("yyyy-MM-dd")
        self.date_deceased_input.setMaximumDate(QDate.currentDate())
        self.date_deceased_input.setSpecialValueText(" ")
        self.date_deceased_input.setDate(QDate(2000, 1, 1))
        self.date_deceased_input.setVisible(False)
        self.date_deceased_input.dateChanged.connect(self._on_data_changed)

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.is_active_checkbox)
        status_layout.addWidget(QLabel("Date Deceased (if inactive):"))
        status_layout.addWidget(self.date_deceased_input)
        status_layout.addStretch()
        self.form_layout.addRow("Status:", status_layout)

        scroll_area.setWidget(content_widget)
        self.main_layout.addWidget(scroll_area)

        self._toggle_date_deceased_visibility()

    def _toggle_date_deceased_visibility(self):
        is_inactive = not self.is_active_checkbox.isChecked()
        self.date_deceased_input.setVisible(is_inactive)
        if not is_inactive:
            self._suppress_data_changed_signal = True
            self.date_deceased_input.setDate(QDate(2000, 1, 1))
            self._suppress_data_changed_signal = False

    # REMOVED: load_species_data method entirely as it's no longer needed.
    # The original `load_species_data` method was calling self.horse_controller.get_all_species()
    # which caused the AttributeError. Since Species is removed, this method is obsolete.

    def populate_form_data(self, horse_data: Optional["Horse"]):
        self._suppress_data_changed_signal = True
        if horse_data:
            self.current_horse_id = horse_data.horse_id
            self.horse_name_input.setText(horse_data.horse_name or "")
            self.account_number_input.setText(horse_data.account_number or "")

            # Species related logic REMOVED
            # self.species_combo.setCurrentIndex(...)

            self.breed_input.setText(horse_data.breed or "")
            self.color_input.setText(horse_data.color or "")

            sex_index = self.sex_combo.findText(
                horse_data.sex or "Unknown", Qt.MatchFlag.MatchFixedString
            )
            self.sex_combo.setCurrentIndex(sex_index if sex_index >= 0 else 0)

            self.dob_input.setDate(
                QDate.fromString(str(horse_data.date_of_birth), "yyyy-MM-dd")
                if horse_data.date_of_birth
                else QDate(2000, 1, 1)
            )
            self.height_input.setText(
                str(horse_data.height_hands)
                if horse_data.height_hands is not None
                else ""
            )
            self.chip_number_input.setText(horse_data.chip_number or "")
            self.tattoo_number_input.setText(horse_data.tattoo_number or "")
            self.description_input.setPlainText(horse_data.description or "")

            self.is_active_checkbox.setChecked(horse_data.is_active)
            if horse_data.date_deceased:
                self.date_deceased_input.setDate(
                    QDate.fromString(str(horse_data.date_deceased), "yyyy-MM-dd")
                )
            else:
                self.date_deceased_input.setDate(QDate(2000, 1, 1))
            self.date_deceased_input.setVisible(
                not horse_data.is_active
            )  # Ensure visibility matches active state

            if horse_data.coggins_date:
                self.coggins_date_input.setDate(
                    QDate.fromString(str(horse_data.coggins_date), "yyyy-MM-dd")
                )
            else:
                self.coggins_date_input.setDate(QDate(2000, 1, 1))

            self.set_form_read_only(True)
            self._is_new_mode = False
        else:
            self.clear_fields(suppress_signal=True)
            self.set_form_read_only(True)
            self._is_new_mode = False

        self._has_modifications = False
        self._suppress_data_changed_signal = False

    def _on_data_changed(self, *args):
        if self._suppress_data_changed_signal:
            return

        if not self._is_new_mode and self.current_horse_id is None:
            if self.horse_name_input.isReadOnly():
                return

        self._has_modifications = True
        self.data_changed.emit()
        self.logger.debug("BasicInfoTab: Data changed signal emitted.")

    def get_data_from_form(self) -> Dict[str, Any]:
        data = {
            "horse_name": self.horse_name_input.text().strip() or None,
            "account_number": self.account_number_input.text().strip() or None,
            # "species_id": REMOVED,
            "breed": self.breed_input.text().strip() or None,
            "color": self.color_input.text().strip() or None,
            "sex": (
                self.sex_combo.currentText()
                if self.sex_combo.currentText() != "Unknown"
                else None
            ),
            "date_of_birth": (
                self.dob_input.date().toString("yyyy-MM-dd")
                if self.dob_input.date() != QDate(2000, 1, 1)
                else None
            ),
            "height_hands": (
                float(self.height_input.text())
                if self.height_input.text().strip()
                else None
            ),
            "chip_number": self.chip_number_input.text().strip() or None,
            "tattoo_number": self.tattoo_number_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            "is_active": self.is_active_checkbox.isChecked(),
            "date_deceased": None,
            "coggins_date": (
                self.coggins_date_input.date().toString("yyyy-MM-dd")
                if self.coggins_date_input.date() != QDate(2000, 1, 1)
                and self.coggins_date_input.text().strip() != ""
                and self.coggins_date_input.specialValueText()
                != self.coggins_date_input.text()
                else None
            ),
        }

        if not data["is_active"]:
            if (
                self.date_deceased_input.date() != QDate(2000, 1, 1)
                and self.date_deceased_input.text().strip() != ""
            ):
                data["date_deceased"] = self.date_deceased_input.date().toString(
                    "yyyy-MM-dd"
                )

        for key in [
            "account_number",
            "breed",
            "color",
            "sex",
            "chip_number",
            "tattoo_number",
            "description",
        ]:
            if data[key] == "":
                data[key] = None
        if data["sex"] == "Unknown":
            data["sex"] = None

        self.logger.debug(f"Data extracted from form: {data}")
        return data

    def set_form_read_only(self, read_only: bool):
        self.logger.debug(f"BasicInfoTab.set_form_read_only({read_only}) called.")
        self.horse_name_input.setReadOnly(read_only)
        self.account_number_input.setReadOnly(read_only)
        # self.species_combo.setEnabled(not read_only) # REMOVED
        self.breed_input.setReadOnly(read_only)
        self.color_input.setReadOnly(read_only)
        self.sex_combo.setEnabled(not read_only)
        self.dob_input.setReadOnly(read_only)
        self.height_input.setReadOnly(read_only)
        self.chip_number_input.setReadOnly(read_only)
        self.tattoo_number_input.setReadOnly(read_only)
        self.description_input.setReadOnly(read_only)
        self.is_active_checkbox.setEnabled(not read_only)
        # date_deceased_input's read-only state is tied to is_active, but enable/disable with form
        self.date_deceased_input.setReadOnly(read_only)
        self.date_deceased_input.setEnabled(
            not read_only and not self.is_active_checkbox.isChecked()
        )  # Only enable if inactive and form editable
        self.coggins_date_input.setReadOnly(read_only)
        self.logger.debug(
            f"BasicInfoTab.set_form_read_only: horse_name_input.isReadOnly() = {self.horse_name_input.isReadOnly()}"
        )

    def clear_fields(self, suppress_signal: bool = False):
        self.logger.info(
            f"BasicInfoTab clear_fields called. Suppress signal: {suppress_signal}"
        )
        if suppress_signal:
            self._suppress_data_changed_signal = True

        self.current_horse_id = None
        self.horse_name_input.clear()
        self.account_number_input.clear()
        # self.species_combo.setCurrentIndex(0) # REMOVED
        self.breed_input.clear()
        self.color_input.clear()
        self.sex_combo.setCurrentIndex(0)
        self.dob_input.setDate(QDate.currentDate().addYears(-5))
        self.height_input.clear()
        self.chip_number_input.clear()
        self.tattoo_number_input.clear()
        self.description_input.clear()
        self.is_active_checkbox.setChecked(True)
        self.date_deceased_input.setDate(QDate(2000, 1, 1))
        self.date_deceased_input.setVisible(False)
        self.coggins_date_input.setDate(QDate(2000, 1, 1))

        if suppress_signal:
            self._suppress_data_changed_signal = False
        self._has_modifications = False
        if not suppress_signal:
            self._on_data_changed()
        self.logger.info("BasicInfoTab.clear_fields: END")

    def set_new_mode(self, is_new: bool):
        self.logger.info(f"BasicInfoTab set to new mode.")
        self._is_new_mode = is_new
        self.current_horse_id = None
        self.clear_fields(suppress_signal=True)
        self.set_form_read_only(False)
        self._has_modifications = False
        self.horse_name_input.setFocus()
        self.edit_mode_toggled.emit(True)

    def set_edit_mode(self, editable: bool):
        self.logger.info(f"BasicInfoTab set_edit_mode called with editable={editable}")
        self._is_new_mode = False
        self.set_form_read_only(not editable)
        if editable:
            self._has_modifications = False
            self.horse_name_input.setFocus()
        self.edit_mode_toggled.emit(editable)

    def has_unsaved_changes(self) -> bool:
        return self._has_modifications

    def mark_as_saved(self):
        self._has_modifications = False
