# views/horse/tabs/basic_info_tab.py
"""
EDSI Veterinary Management System - Horse Basic Info Tab
Version: 1.6.0
Purpose: UI for displaying and editing basic information of a horse.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v1.6.0 (2025-06-10):
    - Updated all input field and button styles to conform to EDMS_STYLE_GUIDE.MD.
      This includes the "boxed-in" look with white borders and standard colors
      for save, discard, and deactivate actions.
- v1.5.2 (2025-06-10):
    - Refactored the UI to use a single grid layout for all input fields,
      which enforces correct vertical alignment for all widgets, including
      the previously misaligned date fields.
- v1.5.1 (2025-06-10):
    - Increased vertical spacing in form layouts to make them less dense.
    - Set an explicit minimum height on input fields in the stylesheet to
      prevent text from being clipped, especially in date fields.
- v1.5.0 (2025-06-10):
    - Rearranged fields to improve layout and readability.
- v1.4.2 (2025-06-10):
    - Adjusted padding in the input field stylesheet to prevent text in
      QDateEdit widgets from being vertically cut off.
- v1.4.1 (2025-06-09):
    - Bug Fix: Corrected logic in `update_buttons_state` to enable Save/Discard
      buttons immediately when entering Add or Edit mode.
- v1.4.0 (2025-06-08):
    - Bug Fix: Corrected the logic in `update_buttons_state` to ensure the
      "Deactivate/Activate Horse" button is enabled whenever a horse is
      selected, not only when the form is in edit mode.
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import date

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QDateEdit,
    QLabel,
    QComboBox,
    QFrame,
    QScrollArea,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtGui import QDoubleValidator, QIcon, QColor, QFont

from controllers.horse_controller import HorseController
from config.app_config import AppConfig


if TYPE_CHECKING:
    from models import Horse, Owner as OwnerModel


class BasicInfoTab(QWidget):
    data_modified = Signal()
    save_requested = Signal()
    discard_requested = Signal()
    toggle_active_requested = Signal(bool)
    edit_mode_toggled = Signal(bool)

    SEX_OPTIONS = ["Unknown", "Stallion", "Mare", "Gelding", "Colt", "Filly"]

    # MODIFIED: Styles updated to conform to EDMS_STYLE_GUIDE.MD
    INPUT_FIELD_STYLE = (
        f"background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; "
        "color: white; "
        "border: 1px solid white; "
        "border-radius: 3px; "
        "padding: 6px 5px; "
        "min-height: 22px;"
    )
    TEXT_AREA_STYLE = INPUT_FIELD_STYLE
    COMBO_DATE_STYLE = INPUT_FIELD_STYLE
    DEACTIVATE_BUTTON_STYLE = (
        f"QPushButton {{"
        f"background-color: {AppConfig.DARK_DANGER_ACTION}; color: white; border: 1px solid white; "
        f"border-radius: 3px; padding: 6px 12px; }}"
        f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_DANGER_ACTION).lighter(115).name()}; }}"
    )
    DISCARD_BUTTON_STYLE = (
        f"QPushButton {{"
        f"background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid white; "
        f"border-radius: 3px; padding: 6px 12px; }}"
        f"QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}"
    )
    SAVE_BUTTON_STYLE = (
        f"QPushButton {{"
        f"background-color: {AppConfig.DARK_SUCCESS_ACTION}; color: white; border: 1px solid white; "
        f"border-radius: 3px; padding: 6px 12px; }}"
        f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}"
        f"QPushButton:pressed {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).darker(110).name()}; }}"
    )

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
        self.parent_view: Optional[QWidget] = parent

        self.current_horse_id: Optional[int] = None
        self._is_new_mode: bool = False
        self._is_editing: bool = False
        self._has_unsaved_changes: bool = False
        self._current_horse_is_active: bool = True

        self.horse_name_input: QLineEdit
        self.breed_input: QLineEdit
        self.sex_combo: QComboBox
        self.reg_number_input: QLineEdit
        self.tattoo_number_input: QLineEdit
        self.location_display_label: QLabel
        self.owner_display_label: QLabel
        self.account_number_input: QLineEdit
        self.color_input: QLineEdit
        self.dob_input: QDateEdit
        self.microchip_id_input: QLineEdit
        self.brand_input: QLineEdit
        self.band_tag_input: QLineEdit
        self.coggins_date_input: QDateEdit
        self.height_input: QLineEdit
        self.description_input: QTextEdit
        self.save_btn: QPushButton
        self.discard_btn: QPushButton
        self.toggle_active_btn: QPushButton

        self._suppress_data_changed_signal = False
        self._setup_ui()
        self.set_form_read_only(True)
        self.update_buttons_state(
            is_editing_or_new=False, has_selection=False, has_changes=False
        )

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        outer_layout = QVBoxLayout(content_widget)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.setSpacing(15)

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(12)
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)

        # --- Create Widgets ---
        self.horse_name_input = QLineEdit()
        self.account_number_input = QLineEdit()
        self.breed_input = QLineEdit()
        self.color_input = QLineEdit()
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(self.SEX_OPTIONS)
        self.reg_number_input = QLineEdit()
        self.microchip_id_input = QLineEdit()
        self.tattoo_number_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.band_tag_input = QLineEdit()
        self.location_display_label = QLabel("N/A")
        self.owner_display_label = QLabel("N/A")
        self.coggins_date_input = QDateEdit()
        self.coggins_date_input.setCalendarPopup(True)
        self.coggins_date_input.setDisplayFormat("yyyy-MM-dd")
        self.coggins_date_input.setDate(QDate(2000, 1, 1))
        self.coggins_date_input.setSpecialValueText(" ")
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate(2000, 1, 1))
        self.dob_input.setMaximumDate(QDate.currentDate())
        self.dob_input.setSpecialValueText(" ")
        self.height_input = QLineEdit()
        double_validator = QDoubleValidator(0.00, 99.99, 2)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.height_input.setValidator(double_validator)

        # --- Add Widgets to Grid ---
        grid_layout.addWidget(QLabel("Name*:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.horse_name_input, 0, 1)
        grid_layout.addWidget(
            QLabel("Account Number:"), 0, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.account_number_input, 0, 3)

        grid_layout.addWidget(QLabel("Breed:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.breed_input, 1, 1)
        grid_layout.addWidget(QLabel("Color:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.color_input, 1, 3)

        grid_layout.addWidget(QLabel("Sex:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.sex_combo, 2, 1)
        grid_layout.addWidget(QLabel("Reg. Number:"), 2, 2, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.reg_number_input, 2, 3)

        grid_layout.addWidget(
            QLabel("Microchip ID:"), 3, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.microchip_id_input, 3, 1)
        grid_layout.addWidget(QLabel("Tattoo:"), 3, 2, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.tattoo_number_input, 3, 3)

        grid_layout.addWidget(QLabel("Brand:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.brand_input, 4, 1)
        grid_layout.addWidget(QLabel("Band/Tag:"), 4, 2, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.band_tag_input, 4, 3)

        grid_layout.addWidget(
            QLabel("Height (Hands):"), 5, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.height_input, 5, 1)

        grid_layout.addWidget(
            QLabel("Coggins Date:"),
            6,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
        )
        grid_layout.addWidget(self.coggins_date_input, 6, 1)
        grid_layout.addWidget(
            QLabel("Date of Birth:"),
            6,
            2,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
        )
        grid_layout.addWidget(self.dob_input, 6, 3)

        grid_layout.addWidget(QLabel("Location:"), 7, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.location_display_label, 7, 1)
        grid_layout.addWidget(QLabel("Owner:"), 7, 2, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.owner_display_label, 7, 3)

        outer_layout.addLayout(grid_layout)

        outer_layout.addSpacing(20)

        description_form_layout = QFormLayout()
        description_form_layout.setContentsMargins(0, 0, 0, 0)
        description_form_layout.setSpacing(10)
        description_form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        description_form_layout.addRow(
            QLabel("Description/Markings:"), self.description_input
        )
        outer_layout.addLayout(description_form_layout)

        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)
        self.toggle_active_btn = QPushButton("Deactivate Horse")
        self.toggle_active_btn.clicked.connect(self._request_toggle_active)
        self.discard_btn = QPushButton("Discard Changes")
        self.discard_btn.clicked.connect(self.discard_requested.emit)
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_requested.emit)
        button_layout.addWidget(self.toggle_active_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.discard_btn)
        button_layout.addWidget(self.save_btn)
        outer_layout.addWidget(button_frame)

        outer_layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        self.main_layout.addWidget(scroll_area)

        # Apply Styles
        for widget in content_widget.findChildren(QLineEdit):
            widget.setStyleSheet(self.INPUT_FIELD_STYLE)
            widget.textChanged.connect(self._on_data_modified)
        for widget in content_widget.findChildren(QDateEdit):
            widget.setStyleSheet(self.COMBO_DATE_STYLE)
            widget.dateChanged.connect(self._on_data_modified)
        for widget in content_widget.findChildren(QComboBox):
            widget.setStyleSheet(self.COMBO_DATE_STYLE)
            widget.currentIndexChanged.connect(self._on_data_modified)
        for widget in content_widget.findChildren(QTextEdit):
            widget.setStyleSheet(self.TEXT_AREA_STYLE)
            widget.textChanged.connect(self._on_data_modified)
        for widget in [self.owner_display_label, self.location_display_label]:
            widget.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.save_btn.setStyleSheet(self.SAVE_BUTTON_STYLE)
        self.discard_btn.setStyleSheet(self.DISCARD_BUTTON_STYLE)
        self.toggle_active_btn.setStyleSheet(self.DEACTIVATE_BUTTON_STYLE)

    def _request_toggle_active(self):
        self.toggle_active_requested.emit(self._current_horse_is_active)

    def update_toggle_active_button_text(self, is_active: bool):
        self.toggle_active_btn.setText(
            "Deactivate Horse" if is_active else "Activate Horse"
        )
        self._current_horse_is_active = is_active

    def populate_form_data(self, horse_data: Optional["Horse"]):
        self.logger.debug(
            f"Populating BasicInfoTab with horse_data: {horse_data.horse_name if horse_data else 'None'}"
        )
        self._suppress_data_changed_signal = True
        if horse_data:
            self.current_horse_id = horse_data.horse_id
            self.horse_name_input.setText(horse_data.horse_name or "")
            self.account_number_input.setText(horse_data.account_number or "")
            self.breed_input.setText(horse_data.breed or "")
            self.color_input.setText(horse_data.color or "")
            sex_idx = self.sex_combo.findText(
                horse_data.sex or "Unknown", Qt.MatchFlag.MatchFixedString
            )
            self.sex_combo.setCurrentIndex(sex_idx if sex_idx >= 0 else 0)
            if horse_data.date_of_birth:
                self.dob_input.setDate(
                    QDate.fromString(str(horse_data.date_of_birth), "yyyy-MM-dd")
                )
            else:
                self.dob_input.setDate(self.dob_input.minimumDate().addDays(-1))
                self.dob_input.setDate(QDate(2000, 1, 1))
            self.reg_number_input.setText(getattr(horse_data, "reg_number", "") or "")
            self.microchip_id_input.setText(horse_data.chip_number or "")
            self.tattoo_number_input.setText(horse_data.tattoo_number or "")
            self.brand_input.setText(getattr(horse_data, "brand", "") or "")
            self.band_tag_input.setText(getattr(horse_data, "band_tag", "") or "")
            self.location_display_label.setText(
                horse_data.location.location_name if horse_data.location else "N/A"
            )
            self.owner_display_label.setText(self._get_display_owner_name(horse_data))
            if horse_data.coggins_date:
                self.coggins_date_input.setDate(
                    QDate.fromString(str(horse_data.coggins_date), "yyyy-MM-dd")
                )
            else:
                self.coggins_date_input.setDate(
                    self.coggins_date_input.minimumDate().addDays(-1)
                )
                self.coggins_date_input.setDate(QDate(2000, 1, 1))
            self.height_input.setText(
                f"{horse_data.height_hands:.2f}"
                if horse_data.height_hands is not None
                else ""
            )
            self.description_input.setPlainText(horse_data.description or "")
            self.update_toggle_active_button_text(horse_data.is_active)
            self.set_form_read_only(True)
            self._is_new_mode = False
            self._is_editing = False
            self.update_buttons_state(
                is_editing_or_new=False, has_selection=True, has_changes=False
            )
        else:
            self.clear_fields(suppress_signal=True)
            self.set_form_read_only(True)
            self._is_new_mode = False
            self._is_editing = False
            self.update_buttons_state(
                is_editing_or_new=False, has_selection=False, has_changes=False
            )
        self._has_unsaved_changes = False
        self._suppress_data_changed_signal = False

    def _on_data_modified(self, *args):
        if self._suppress_data_changed_signal:
            return
        if not self.horse_name_input.isReadOnly():
            if not self._has_unsaved_changes:
                self._has_unsaved_changes = True
                self.logger.debug("Data modified. Flag set.")
                self.data_modified.emit()
            self.update_buttons_state(
                is_editing_or_new=(self._is_new_mode or self._is_editing),
                has_selection=(self.current_horse_id is not None),
                has_changes=True,
            )

    def get_data_from_form(self) -> Dict[str, Any]:
        def get_date_object(date_edit_widget: QDateEdit) -> Optional[date]:
            q_date = date_edit_widget.date()
            if (
                date_edit_widget.text().strip() == ""
                or q_date < date_edit_widget.minimumDate()
                or not q_date.isValid()
                or q_date == date_edit_widget.minimumDate().addDays(-1)
            ):
                return None
            return date(q_date.year(), q_date.month(), q_date.day())

        data = {
            "horse_name": self.horse_name_input.text().strip() or None,
            "account_number": self.account_number_input.text().strip() or None,
            "breed": self.breed_input.text().strip() or None,
            "color": self.color_input.text().strip() or None,
            "sex": (
                self.sex_combo.currentText()
                if self.sex_combo.currentText() != "Unknown"
                else None
            ),
            "date_of_birth": get_date_object(self.dob_input),
            "chip_number": self.microchip_id_input.text().strip() or None,
            "tattoo_number": self.tattoo_number_input.text().strip() or None,
            "is_active": self._current_horse_is_active,
            "reg_number": self.reg_number_input.text().strip() or None,
            "brand": self.brand_input.text().strip() or None,
            "band_tag": self.band_tag_input.text().strip() or None,
            "coggins_date": get_date_object(self.coggins_date_input),
            "height_hands": (
                float(self.height_input.text())
                if self.height_input.text().strip()
                else None
            ),
            "description": self.description_input.toPlainText().strip() or None,
            "date_deceased": None,
        }
        return data

    def set_form_read_only(self, read_only: bool):
        self.logger.debug(f"BasicInfoTab.set_form_read_only: {read_only}")
        self._suppress_data_changed_signal = True
        line_edit_fields = [
            self.horse_name_input,
            self.account_number_input,
            self.breed_input,
            self.color_input,
            self.reg_number_input,
            self.microchip_id_input,
            self.tattoo_number_input,
            self.brand_input,
            self.band_tag_input,
            self.height_input,
        ]
        for field in line_edit_fields:
            field.setReadOnly(read_only)
        interactive_widgets = [self.sex_combo, self.dob_input, self.coggins_date_input]
        for widget in interactive_widgets:
            widget.setEnabled(not read_only)
        self.description_input.setReadOnly(read_only)
        self._is_editing = not read_only
        if read_only:
            self._has_unsaved_changes = False
        self._suppress_data_changed_signal = False

    def clear_fields(self, suppress_signal: bool = False):
        if suppress_signal:
            self._suppress_data_changed_signal = True
        self.current_horse_id = None
        self.horse_name_input.clear()
        self.account_number_input.clear()
        self.breed_input.clear()
        self.color_input.clear()
        self.sex_combo.setCurrentIndex(0)
        self.dob_input.setDate(self.dob_input.minimumDate().addDays(-1))
        self.dob_input.setDate(QDate(2000, 1, 1))
        self.reg_number_input.clear()
        self.microchip_id_input.clear()
        self.tattoo_number_input.clear()
        self.brand_input.clear()
        self.band_tag_input.clear()
        self.location_display_label.setText("N/A")
        self.owner_display_label.setText("N/A")
        self.coggins_date_input.setDate(
            self.coggins_date_input.minimumDate().addDays(-1)
        )
        self.coggins_date_input.setDate(QDate(2000, 1, 1))
        self.height_input.clear()
        self.description_input.clear()
        self.update_toggle_active_button_text(True)
        if suppress_signal:
            self._suppress_data_changed_signal = False
        self._has_unsaved_changes = False
        if not suppress_signal:
            self.data_modified.emit()

    def set_new_mode(self, is_new: bool):
        self.logger.info(f"BasicInfoTab set_new_mode: {is_new}")
        self._is_new_mode = is_new
        self._is_editing = True
        self.current_horse_id = None
        self.clear_fields(suppress_signal=True)
        self.set_form_read_only(False)
        self._has_unsaved_changes = False
        self.update_buttons_state(
            is_editing_or_new=True, has_selection=False, has_changes=False
        )
        self.edit_mode_toggled.emit(True)
        self.horse_name_input.setFocus()

    def set_edit_mode(self, editable: bool):
        self.logger.info(f"BasicInfoTab set_edit_mode: {editable}")
        self._is_new_mode = False
        self._is_editing = editable
        self.set_form_read_only(not editable)
        if editable:
            self._has_unsaved_changes = False
            self.horse_name_input.setFocus()
        self.update_buttons_state(
            is_editing_or_new=editable,
            has_selection=(self.current_horse_id is not None),
            has_changes=self._has_unsaved_changes,
        )
        self.edit_mode_toggled.emit(editable)

    def update_buttons_state(
        self, is_editing_or_new: bool, has_selection: bool, has_changes: bool
    ):
        can_save = (is_editing_or_new or self._is_editing) and has_changes
        can_discard = is_editing_or_new or self._is_editing
        can_toggle_active = has_selection and not self._is_new_mode

        self.save_btn.setEnabled(
            can_save or is_editing_or_new
        )  # Enable Save immediately in new/edit mode
        self.discard_btn.setEnabled(can_discard)
        self.toggle_active_btn.setEnabled(can_toggle_active)

        if not has_selection and not self._is_new_mode:
            self.update_toggle_active_button_text(True)
            self.toggle_active_btn.setEnabled(False)
        elif self._is_new_mode:
            self.update_toggle_active_button_text(True)
            self.toggle_active_btn.setEnabled(False)

    def has_unsaved_changes(self) -> bool:
        return self._has_unsaved_changes

    def mark_as_saved(self):
        self.logger.debug("BasicInfoTab.mark_as_saved.")
        self._has_unsaved_changes = False
        self._is_editing = False
        self.set_form_read_only(True)
        self.update_buttons_state(False, (self.current_horse_id is not None), False)

    def _calculate_age(self, birth_date_obj: Optional[date]) -> str:
        if not birth_date_obj or not isinstance(birth_date_obj, date):
            return "Age N/A"
        try:
            today = date.today()
            age_val = (
                today.year
                - birth_date_obj.year
                - (
                    (today.month, today.day)
                    < (birth_date_obj.month, birth_date_obj.day)
                )
            )
            return f"{age_val} yr" if age_val == 1 else f"{age_val} yrs"
        except Exception as e:
            self.logger.error(
                f"Error calculating age for date {birth_date_obj}: {e}", exc_info=True
            )
            return "Age Error"

    def _get_display_owner_name(self, horse: "Horse") -> str:
        if not horse.owners:
            return "No Owner Associated"
        first_owner = horse.owners[0]
        name_parts = []
        if first_owner.farm_name:
            name_parts.append(first_owner.farm_name)
        person_name_parts = []
        if first_owner.first_name:
            person_name_parts.append(first_owner.first_name)
        if first_owner.last_name:
            person_name_parts.append(first_owner.last_name)
        person_name_str = " ".join(person_name_parts).strip()
        if person_name_str:
            if name_parts:
                name_parts.append(f"({person_name_str})")
            else:
                name_parts.append(person_name_str)
        return (
            " ".join(name_parts) if name_parts else f"Owner ID: {first_owner.owner_id}"
        )

    def _get_display_location_name(self, horse: "Horse") -> str:
        return horse.location.location_name if horse.location else "N/A"
