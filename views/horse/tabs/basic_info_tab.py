# views/horse/tabs/basic_info_tab.py
"""
EDSI Veterinary Management System - Horse Basic Info Tab
Version: 1.2.20
Purpose: UI for displaying and editing basic information of a horse.
         - Implemented robust owner name display logic in populate_form_data
           for the owner_display_label.
Last Updated: May 26, 2025
Author: Gemini

Changelog:
- v1.2.20 (2025-05-26):
    - Updated `populate_form_data` to use more robust logic for displaying the
      primary owner's name in `owner_display_label`. It now constructs the
      name from farm_name, first_name, and last_name attributes of the
      Owner model, similar to the logic in HorseUnifiedManagement's header.
- v1.2.19 (2025-05-26):
    - Added `owner_display_label` (QLabel) to show the primary owner's name.
    - Positioned "Owner" field in the grid layout below "Location".
    - Updated `populate_form_data` and `clear_fields`.
- v1.2.18 (2025-05-25):
    - Modified `get_data_from_form` to return Python `datetime.date` objects.
# ... (rest of previous changelog entries assumed present)
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
from PySide6.QtCore import Qt, Signal, QDate, QSize  # QSize for icon placeholder
from PySide6.QtGui import QDoubleValidator, QIcon  # QIcon for icon placeholder

from controllers.horse_controller import HorseController

# No direct import of OwnerModel here, assuming Horse object has it via relationship

if TYPE_CHECKING:
    from models import Horse, Owner as OwnerModel  # For type hinting horse_data.owners


class BasicInfoTab(QWidget):
    data_modified = Signal()
    save_requested = Signal()
    discard_requested = Signal()
    toggle_active_requested = Signal(bool)
    edit_mode_toggled = Signal(bool)

    SEX_OPTIONS = ["Unknown", "Stallion", "Mare", "Gelding", "Colt", "Filly"]

    INPUT_FIELD_STYLE = (
        "background-color: #3E3E3E; "
        "color: white; "
        "border: 1px solid #B0B0B0; "
        "border-radius: 3px; "
        "padding: 5px;"
    )
    TEXT_AREA_STYLE = INPUT_FIELD_STYLE
    COMBO_DATE_STYLE = INPUT_FIELD_STYLE
    DEACTIVATE_BUTTON_STYLE = (
        "QPushButton {"
        "background-color: #FFC107; color: black; border: 1px solid #707070; "
        "border-radius: 3px; padding: 6px 12px; }"
        "QPushButton:hover { background-color: #FFD54F; }"
        "QPushButton:pressed { background-color: #FFA000; }"
    )
    DISCARD_BUTTON_STYLE = (
        "QPushButton {"
        "background-color: #212121; color: white; border: 1px solid #707070; "
        "border-radius: 3px; padding: 6px 12px; }"
        "QPushButton:hover { background-color: #424242; }"
        "QPushButton:pressed { background-color: #000000; }"
    )
    SAVE_BUTTON_STYLE = (
        "QPushButton {"
        "background-color: #607D8B; color: white; border: 1px solid #707070; "
        "border-radius: 3px; padding: 6px 12px; }"
        "QPushButton:hover { background-color: #78909C; }"
        "QPushButton:pressed { background-color: #546E7A; }"
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

        # UI Elements
        self.horse_name_input: QLineEdit
        self.breed_input: QLineEdit
        self.sex_combo: QComboBox
        self.reg_number_input: QLineEdit
        self.tattoo_number_input: QLineEdit
        self.location_display_label: QLabel
        self.owner_display_label: QLabel  # Added in v1.2.19

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
        # (Setup for layout, scroll_area, content_widget, top_grid_layout same as v1.2.19)
        # (Rows 0-5 for Name to Band/Tag same as v1.2.19)
        # (NEW Row 6: Owner is already in v1.2.19 _setup_ui as per my last response)
        # (Coggins/Height layout, Description layout, Buttons layout same as v1.2.19)
        # For brevity, re-confirming the structure is as per previous response that added owner_display_label.
        # The only change is ensuring populate_form_data correctly fills owner_display_label.
        # All other UI setup code from v1.2.19 (which included adding the owner_display_label to the grid) remains.

        # --- Full _setup_ui from v1.2.19 (which included owner_display_label) ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        outer_layout = QVBoxLayout(content_widget)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.setSpacing(15)
        top_grid_layout = QGridLayout()
        top_grid_layout.setSpacing(10)
        top_grid_layout.setHorizontalSpacing(20)
        top_grid_layout.setColumnStretch(1, 1)
        top_grid_layout.setColumnStretch(3, 1)

        # Row 0
        top_grid_layout.addWidget(QLabel("Name*:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.horse_name_input = QLineEdit()
        self.horse_name_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.horse_name_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.horse_name_input, 0, 1)
        top_grid_layout.addWidget(
            QLabel("Account Number:"), 0, 2, Qt.AlignmentFlag.AlignRight
        )
        self.account_number_input = QLineEdit()
        self.account_number_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.account_number_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.account_number_input, 0, 3)
        # Row 1
        top_grid_layout.addWidget(QLabel("Breed:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.breed_input = QLineEdit()
        self.breed_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.breed_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.breed_input, 1, 1)
        top_grid_layout.addWidget(QLabel("Color:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        self.color_input = QLineEdit()
        self.color_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.color_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.color_input, 1, 3)
        # Row 2
        top_grid_layout.addWidget(QLabel("Sex:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(self.SEX_OPTIONS)
        self.sex_combo.setStyleSheet(self.COMBO_DATE_STYLE)
        self.sex_combo.currentIndexChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.sex_combo, 2, 1)
        top_grid_layout.addWidget(
            QLabel("Date of Birth:"), 2, 2, Qt.AlignmentFlag.AlignRight
        )
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate(2000, 1, 1))
        self.dob_input.setMaximumDate(QDate.currentDate())
        self.dob_input.setSpecialValueText(" ")
        self.dob_input.setStyleSheet(self.COMBO_DATE_STYLE)
        self.dob_input.dateChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.dob_input, 2, 3)
        # Row 3
        top_grid_layout.addWidget(
            QLabel("Reg. Number:"), 3, 0, Qt.AlignmentFlag.AlignRight
        )
        self.reg_number_input = QLineEdit()
        self.reg_number_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.reg_number_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.reg_number_input, 3, 1)
        top_grid_layout.addWidget(
            QLabel("Microchip ID:"), 3, 2, Qt.AlignmentFlag.AlignRight
        )
        self.microchip_id_input = QLineEdit()
        self.microchip_id_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.microchip_id_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.microchip_id_input, 3, 3)
        # Row 4
        top_grid_layout.addWidget(QLabel("Tattoo:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        self.tattoo_number_input = QLineEdit()
        self.tattoo_number_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.tattoo_number_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.tattoo_number_input, 4, 1)
        top_grid_layout.addWidget(QLabel("Brand:"), 4, 2, Qt.AlignmentFlag.AlignRight)
        self.brand_input = QLineEdit()
        self.brand_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.brand_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.brand_input, 4, 3)
        # Row 5
        top_grid_layout.addWidget(
            QLabel("Location:"), 5, 0, Qt.AlignmentFlag.AlignRight
        )
        self.location_display_label = QLabel("N/A")
        self.location_display_label.setStyleSheet(self.INPUT_FIELD_STYLE)
        if self.horse_name_input.sizeHint().isValid():
            self.location_display_label.setMinimumHeight(
                self.horse_name_input.sizeHint().height()
            )
        else:
            font_metrics = self.location_display_label.fontMetrics()
            padding = 5
            self.location_display_label.setMinimumHeight(
                font_metrics.height() + 2 * padding + 2
            )
        top_grid_layout.addWidget(self.location_display_label, 5, 1)
        top_grid_layout.addWidget(
            QLabel("Band/Tag:"), 5, 2, Qt.AlignmentFlag.AlignRight
        )
        self.band_tag_input = QLineEdit()
        self.band_tag_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.band_tag_input.textChanged.connect(self._on_data_modified)
        top_grid_layout.addWidget(self.band_tag_input, 5, 3)
        # Row 6 (Owner Display)
        top_grid_layout.addWidget(QLabel("Owner:"), 6, 0, Qt.AlignmentFlag.AlignRight)
        self.owner_display_label = QLabel("N/A")
        self.owner_display_label.setStyleSheet(self.INPUT_FIELD_STYLE)
        if self.horse_name_input.sizeHint().isValid():
            self.owner_display_label.setMinimumHeight(
                self.horse_name_input.sizeHint().height()
            )
        else:
            font_metrics = self.owner_display_label.fontMetrics()
            padding = 5
            self.owner_display_label.setMinimumHeight(
                font_metrics.height() + 2 * padding + 2
            )
        top_grid_layout.addWidget(
            self.owner_display_label, 6, 1
        )  # Spans one column for now

        outer_layout.addLayout(top_grid_layout)

        coggins_height_layout = QGridLayout()
        coggins_height_layout.setSpacing(10)
        coggins_height_layout.setHorizontalSpacing(20)
        coggins_height_layout.setColumnStretch(1, 1)
        coggins_height_layout.setColumnStretch(3, 1)
        coggins_height_layout.addWidget(
            QLabel("Coggins Date:"), 0, 0, Qt.AlignmentFlag.AlignRight
        )
        self.coggins_date_input = QDateEdit()
        self.coggins_date_input.setCalendarPopup(True)
        self.coggins_date_input.setDisplayFormat("yyyy-MM-dd")
        self.coggins_date_input.setDate(QDate(2000, 1, 1))
        self.coggins_date_input.setSpecialValueText(" ")
        self.coggins_date_input.setStyleSheet(self.COMBO_DATE_STYLE)
        self.coggins_date_input.dateChanged.connect(self._on_data_modified)
        coggins_height_layout.addWidget(self.coggins_date_input, 0, 1)
        coggins_height_layout.addWidget(
            QLabel("Height (Hands):"), 0, 2, Qt.AlignmentFlag.AlignRight
        )
        self.height_input = QLineEdit()
        double_validator = QDoubleValidator(0.00, 99.99, 2)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.height_input.setValidator(double_validator)
        self.height_input.setStyleSheet(self.INPUT_FIELD_STYLE)
        self.height_input.textChanged.connect(self._on_data_modified)
        coggins_height_layout.addWidget(self.height_input, 0, 3)
        outer_layout.addLayout(coggins_height_layout)

        description_form_layout = QFormLayout()
        description_form_layout.setContentsMargins(0, 0, 0, 0)
        description_form_layout.setSpacing(10)
        description_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        self.description_input.setStyleSheet(self.TEXT_AREA_STYLE)
        self.description_input.textChanged.connect(self._on_data_modified)
        description_form_layout.addRow(
            QLabel("Description/Markings:"), self.description_input
        )
        outer_layout.addLayout(description_form_layout)

        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)
        self.toggle_active_btn = QPushButton("Deactivate Horse")
        self.toggle_active_btn.setStyleSheet(self.DEACTIVATE_BUTTON_STYLE)
        self.toggle_active_btn.clicked.connect(self._request_toggle_active)
        self.toggle_active_btn.setObjectName("ToggleActiveButton")
        self.discard_btn = QPushButton("Discard Changes")
        self.discard_btn.setStyleSheet(self.DISCARD_BUTTON_STYLE)
        self.discard_btn.clicked.connect(self.discard_requested.emit)
        self.discard_btn.setObjectName("DiscardButton")
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet(self.SAVE_BUTTON_STYLE)
        self.save_btn.clicked.connect(self.save_requested.emit)
        self.save_btn.setObjectName("SaveButton")
        button_layout.addWidget(self.toggle_active_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.discard_btn)
        button_layout.addWidget(self.save_btn)
        outer_layout.addWidget(button_frame)
        outer_layout.addStretch(1)
        scroll_area.setWidget(content_widget)
        self.main_layout.addWidget(scroll_area)

    def _request_toggle_active(self):
        # (Same as v1.2.19)
        if self._current_horse_is_active:
            self.toggle_active_requested.emit(False)
        else:
            self.toggle_active_requested.emit(True)

    def update_toggle_active_button_text(self, is_active: bool):
        # (Same as v1.2.19)
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
                horse_data.location.location_name
                if horse_data.location and hasattr(horse_data.location, "location_name")
                else "N/A"
            )

            # Populate NEW owner field using robust name construction
            owner_name_display = "N/A"
            if (
                hasattr(horse_data, "owners")
                and horse_data.owners
                and len(horse_data.owners) > 0
            ):
                first_owner_model = horse_data.owners[
                    0
                ]  # This is an OwnerModel instance
                if first_owner_model:
                    name_parts = []
                    if (
                        hasattr(first_owner_model, "farm_name")
                        and first_owner_model.farm_name
                    ):
                        name_parts.append(first_owner_model.farm_name)

                    person_name_parts = []
                    if (
                        hasattr(first_owner_model, "first_name")
                        and first_owner_model.first_name
                    ):
                        person_name_parts.append(first_owner_model.first_name)
                    if (
                        hasattr(first_owner_model, "last_name")
                        and first_owner_model.last_name
                    ):
                        person_name_parts.append(first_owner_model.last_name)

                    person_name_str = " ".join(person_name_parts).strip()
                    if person_name_str:
                        if name_parts:
                            name_parts.append(f"({person_name_str})")
                        else:
                            name_parts.append(person_name_str)

                    if name_parts:
                        owner_name_display = " ".join(name_parts)
                    elif hasattr(first_owner_model, "owner_id"):
                        owner_name_display = f"Owner ID: {first_owner_model.owner_id}"
                    else:
                        owner_name_display = "Owner Data Incomplete"
                else:
                    owner_name_display = "Owner Data Missing"
            else:  # No owners associated
                owner_name_display = "No Owner Associated"
            self.owner_display_label.setText(owner_name_display)

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
        # (Same as v1.2.19)
        if self._suppress_data_changed_signal:
            return
        if not self.horse_name_input.isReadOnly():
            if not self._has_unsaved_changes:
                self._has_unsaved_changes = True
                self.logger.debug("Data modified.")
                self.data_modified.emit()
            self.update_buttons_state(
                is_editing_or_new=(self._is_new_mode or self._is_editing),
                has_selection=(self.current_horse_id is not None),
                has_changes=True,
            )

    def get_data_from_form(self) -> Dict[str, Any]:
        # (Same as v1.2.19 - owner is display only, not collected here)
        def get_date_object(date_edit_widget: QDateEdit) -> Optional[date]:
            q_date = date_edit_widget.date()
            if (
                date_edit_widget.text().strip() == ""
                or (
                    q_date == QDate(2000, 1, 1)
                    and date_edit_widget.text() == date_edit_widget.specialValueText()
                )
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
        for key in [
            "account_number",
            "breed",
            "color",
            "chip_number",
            "tattoo_number",
            "reg_number",
            "brand",
            "band_tag",
            "description",
        ]:
            if data[key] == "":
                data[key] = None
        if data["sex"] == "Unknown":
            data["sex"] = None
        self.logger.debug(f"Data extracted: {data}")
        return data

    def set_form_read_only(self, read_only: bool):
        # (Same as v1.2.19)
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
            style_suffix = "background-color: #2E2E2E;" if read_only else ""
            field.setStyleSheet(self.INPUT_FIELD_STYLE + style_suffix)
        interactive_widgets = [self.sex_combo, self.dob_input, self.coggins_date_input]
        for widget in interactive_widgets:
            widget.setEnabled(not read_only)
            style_suffix_interactive = (
                "background-color: #2E2E2E; color: #AAAAAA;" if read_only else ""
            )
            widget.setStyleSheet(self.COMBO_DATE_STYLE + style_suffix_interactive)
        self.description_input.setReadOnly(read_only)
        style_suffix_desc = "background-color: #2E2E2E;" if read_only else ""
        self.description_input.setStyleSheet(self.TEXT_AREA_STYLE + style_suffix_desc)
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
        self.owner_display_label.setText("N/A")  # Clear owner display
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

    # (set_new_mode, set_edit_mode, update_buttons_state, has_unsaved_changes,
    #  mark_as_saved, update_displayed_location methods remain the same as in v1.2.19)
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
        can_save_discard = (is_editing_or_new or self._is_editing) and has_changes
        self.save_btn.setEnabled(can_save_discard)
        self.discard_btn.setEnabled(can_save_discard)
        can_toggle_active = (
            has_selection
            and (is_editing_or_new or self._is_editing)
            and not self._is_new_mode
        )
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

    def update_displayed_location(
        self, location_id: Optional[int], location_name: Optional[str]
    ):
        if hasattr(self, "location_display_label"):
            self.location_display_label.setText(location_name or "N/A")
