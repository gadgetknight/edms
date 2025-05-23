# views/horse/tabs/basic_info_tab.py
"""
EDSI Veterinary Management System - Basic Info Tab for Horse Management
Version: 1.2.9
Purpose: Displays and manages basic information for a horse.
         - Added Coggins Date field.
Last Updated: May 22, 2025
Author: Gemini

Changelog:
- v1.2.9 (2025-05-22):
    - Added `coggins_date_input` (QDateEdit) to the UI.
    - Updated `fields_config`, `_create_horse_attributes_form`, `populate_fields`,
      `get_data`, `clear_fields`, and `set_form_read_only` to handle Coggins Date.
- v1.2.8 (2025-05-22):
    - Corrected `spec_obj.species_name` to `spec_obj.name` in `load_species_data`.
    - Modified `set_form_read_only` to use `setDisabled(read_only)` for QComboBox.
    - Added `blockSignals(True/False)` around `species_input` population.
- v1.2.7 (2025-05-22):
    - Added missing import: `from typing import Optional, Dict, List`.
"""
import logging
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QSizePolicy,
    QTextEdit,
    QCheckBox,
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QFont, QDoubleValidator

from controllers.horse_controller import HorseController

from config.app_config import (
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DARK_BORDER,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_PRIMARY_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_SUCCESS_ACTION,
    DARK_DANGER_ACTION,
    DEFAULT_FONT_FAMILY,
    DARK_WIDGET_BACKGROUND,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_HEADER_FOOTER,
)


class BasicInfoTab(QWidget):
    data_modified = Signal()
    save_requested = Signal()
    discard_requested = Signal()
    toggle_active_requested = Signal(bool)

    def __init__(
        self, parent_view: QWidget, horse_controller: HorseController, parent=None
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller
        self.current_horse_id: Optional[int] = None
        self._has_modifications: bool = False

        self.fields_config = [
            ("horse_name_input", "Horse Name:"),
            ("account_number_input", "Account Number:"),
            ("species_input", "Species:"),
            ("breed_input", "Breed:"),
            ("color_input", "Color:"),
            ("sex_input", "Sex:"),
            ("date_of_birth_input", "Date of Birth:"),
            ("coggins_date_input", "Coggins Date:"),  # New Field
            ("height_input", "Height (Hands):"),
            ("chip_number_input", "Chip Number:"),
            ("tattoo_number_input", "Tattoo Number:"),
            ("description_input", "Description/Notes:"),
            ("active_status_checkbox", "Active Status:"),
            ("date_deceased_input", "Date Deceased:"),
        ]
        self.input_widgets: Dict[str, QWidget] = {}

        self._setup_ui()
        self.set_form_read_only(True)

    def get_tab_input_style(self):
        # ... (unchanged from v1.2.8) ...
        return f"""
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 10px; font-size: 13px;
            }}
            QTextEdit {{ padding: 10px; }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QDateEdit:disabled, QDoubleSpinBox:disabled {{
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QComboBox:disabled {{ /* Specific style for disabled QComboBox */
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QComboBox::drop-down {{ border: none; background-color: transparent; width: 15px; }}
            QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY}; }}
            QDateEdit::up-button, QDateEdit::down-button {{ width: 18px; }}
            QComboBox QAbstractItemView {{ 
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }}
        """

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        form_style = self.get_tab_input_style()
        self.setStyleSheet(form_style)

        (
            details_form_layout,
            self.horse_name_input,
            self.account_number_input,
            self.chip_number_input,
            self.tattoo_number_input,
            self.description_input,
        ) = self._create_horse_details_form()
        main_layout.addLayout(details_form_layout)

        # Added coggins_date_input to the return tuple and assignment
        (
            attributes_form_layout,
            self.species_input,
            self.breed_input,
            self.color_input,
            self.sex_input,
            self.date_of_birth_input,
            self.coggins_date_input,
            self.height_input,
        ) = self._create_horse_attributes_form()  # Added coggins_date_input here
        main_layout.addLayout(attributes_form_layout)

        (
            status_location_layout,
            self.location_display_value,
            self.active_status_checkbox,
            self.active_status_label,
            self.date_deceased_label,
            self.date_deceased_input,
        ) = self._create_status_location_form()
        main_layout.addLayout(status_location_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QPushButton("💾 Save Changes")
        self.discard_btn = QPushButton("↩️ Discard Changes")

        if hasattr(self.parent_view, "get_generic_button_style"):
            button_style = self.parent_view.get_generic_button_style()
            self.save_btn.setStyleSheet(
                button_style.replace(DARK_BUTTON_BG, DARK_SUCCESS_ACTION)
            )
            self.discard_btn.setStyleSheet(
                button_style.replace(DARK_BUTTON_BG, DARK_DANGER_ACTION)
            )

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.discard_btn)
        main_layout.addLayout(button_layout)

        self.update_buttons_state(False, False)

        for widget_name, _ in self.fields_config:
            widget = getattr(self, widget_name, None)
            if widget:
                if isinstance(widget, QLineEdit):
                    widget.textChanged.connect(self._mark_modified)
                elif isinstance(widget, QTextEdit):
                    widget.textChanged.connect(self._mark_modified)
                elif isinstance(widget, QComboBox):
                    widget.currentIndexChanged.connect(self._mark_modified)
                elif isinstance(widget, QDateEdit):
                    widget.dateChanged.connect(self._mark_modified)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.valueChanged.connect(self._mark_modified)
                elif (
                    isinstance(widget, QCheckBox)
                    and widget_name == "active_status_checkbox"
                ):
                    widget.stateChanged.connect(self._on_active_status_changed)

        self.save_btn.clicked.connect(self.save_requested.emit)
        self.discard_btn.clicked.connect(self._confirm_discard)

        self.load_species_data()
        main_layout.addStretch()

    def _create_form_row(
        self, label_text: str, widget: QWidget, layout: QGridLayout, row: int
    ):
        label = QLabel(label_text)
        label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-top: 8px;"
        )
        label.setFixedWidth(
            130
        )  # Adjusted for potentially longer labels like "Coggins Date:"
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(widget, row, 1)

    def _create_horse_details_form(self):
        # ... (unchanged) ...
        layout = QGridLayout()
        layout.setSpacing(10)
        horse_name_input = QLineEdit()
        self._create_form_row("Horse Name:", horse_name_input, layout, 0)
        account_number_input = QLineEdit()
        self._create_form_row("Account Number:", account_number_input, layout, 1)
        chip_number_input = QLineEdit()
        self._create_form_row("Chip Number:", chip_number_input, layout, 2)
        tattoo_number_input = QLineEdit()
        self._create_form_row("Tattoo Number:", tattoo_number_input, layout, 3)
        description_input = QTextEdit()
        description_input.setFixedHeight(80)
        description_input.setPlaceholderText(
            "Enter any relevant notes or description..."
        )
        self._create_form_row("Description:", description_input, layout, 4)
        return (
            layout,
            horse_name_input,
            account_number_input,
            chip_number_input,
            tattoo_number_input,
            description_input,
        )

    def _create_horse_attributes_form(self):
        layout = QGridLayout()
        layout.setSpacing(10)

        species_input = QComboBox()
        self._create_form_row("Species:", species_input, layout, 0)

        breed_input = QLineEdit()
        self._create_form_row("Breed:", breed_input, layout, 1)

        color_input = QLineEdit()
        self._create_form_row("Color:", color_input, layout, 2)

        sex_input = QComboBox()
        sex_input.addItems(
            ["", "Mare", "Gelding", "Stallion", "Colt", "Filly", "Other"]
        )
        self._create_form_row("Sex:", sex_input, layout, 3)

        date_of_birth_input = QDateEdit(calendarPopup=True)
        date_of_birth_input.setDate(QDate(2000, 1, 1))  # Default to a non-current date
        date_of_birth_input.setSpecialValueText(" ")  # Display as blank
        date_of_birth_input.setDisplayFormat("MM/dd/yyyy")
        self._create_form_row("Date of Birth:", date_of_birth_input, layout, 4)

        # New Coggins Date Field
        coggins_date_input = QDateEdit(calendarPopup=True)
        coggins_date_input.setDate(QDate(2000, 1, 1))  # Default to a non-current date
        coggins_date_input.setSpecialValueText(" ")  # Display as blank
        coggins_date_input.setDisplayFormat("MM/dd/yyyy")
        self._create_form_row(
            "Coggins Date:", coggins_date_input, layout, 5
        )  # Added row

        height_input = QDoubleSpinBox()
        height_input.setDecimals(1)
        height_input.setMinimum(0.0)
        height_input.setMaximum(30.0)
        height_input.setSuffix(" hh")
        self._create_form_row("Height (Hands):", height_input, layout, 6)  # Shifted row

        return (
            layout,
            species_input,
            breed_input,
            color_input,
            sex_input,
            date_of_birth_input,
            coggins_date_input,
            height_input,
        )

    def _create_status_location_form(self):
        # ... (unchanged, but ensure active_status_label placement is good) ...
        layout = QGridLayout()
        layout.setSpacing(10)

        location_label = QLabel("Current Location:")
        location_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-top: 8px;"
        )
        location_label.setFixedWidth(130)
        location_display_value = QLabel("N/A")
        location_display_value.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent; padding: 6px 0px; font-weight: bold;"
        )
        location_display_value.setToolTip("Managed on the Location tab.")
        layout.addWidget(location_label, 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(location_display_value, 0, 1)

        active_status_label_title = QLabel("Active Status:")  # This is the field label
        active_status_label_title.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-top: 8px;"
        )
        active_status_label_title.setFixedWidth(130)
        layout.addWidget(active_status_label_title, 1, 0, Qt.AlignmentFlag.AlignTop)

        active_status_checkbox = QCheckBox("Horse is Active")
        active_status_checkbox.setChecked(True)
        active_status_checkbox.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )

        active_status_label = QLabel(
            "Status: Active"
        )  # This label shows the textual status
        active_status_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; padding-left:10px; padding-top: 8px;"
        )

        active_status_checkbox.toggled.connect(
            lambda checked, label=active_status_label: label.setText(
                f"Status: {'Active' if checked else 'Inactive'}"
            )
        )
        active_status_checkbox.toggled.connect(
            lambda: self.toggle_active_requested.emit(
                self.active_status_checkbox.isChecked()
            )
        )

        status_layout_h = QHBoxLayout()  # To put checkbox and status label side-by-side
        status_layout_h.addWidget(active_status_checkbox)
        status_layout_h.addWidget(active_status_label)
        status_layout_h.addStretch()
        layout.addLayout(status_layout_h, 1, 1)

        date_deceased_label = QLabel("Date Deceased:")
        date_deceased_label.setStyleSheet(
            f"color: {DARK_TEXT_TERTIARY}; background: transparent; padding-top: 8px;"
        )
        date_deceased_label.setFixedWidth(130)
        date_deceased_input = QDateEdit(calendarPopup=True)
        date_deceased_input.setDisplayFormat("MM/dd/yyyy")
        date_deceased_input.setDate(QDate(2000, 1, 1))
        date_deceased_input.setSpecialValueText(" ")
        date_deceased_input.setVisible(False)
        date_deceased_label.setVisible(False)

        layout.addWidget(date_deceased_label, 2, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(date_deceased_input, 2, 1)
        return (
            layout,
            location_display_value,
            active_status_checkbox,
            active_status_label,
            date_deceased_label,
            date_deceased_input,
        )

    def load_species_data(self):
        # ... (unchanged from v1.2.8 - uses .name, blocks signals) ...
        try:
            species_list_objects = self.horse_controller.get_all_species()

            self.species_input.blockSignals(True)
            self.species_input.clear()
            self.species_input.addItem("", None)
            if species_list_objects:
                for spec_obj in species_list_objects:
                    self.species_input.addItem(spec_obj.name, spec_obj.species_id)
            self.species_input.blockSignals(False)

            self.logger.info(
                f"Loaded {len(species_list_objects) if species_list_objects else 0} species into combobox."
            )
        except Exception as e:
            self.logger.error(f"Error loading species data: {e}", exc_info=True)
            if hasattr(self.parent_view, "show_error"):
                self.parent_view.show_error(
                    "Species Load Error", f"Could not load species: {e}"
                )

    def populate_fields(self, horse_data: dict | object):
        self.logger.info(
            f"Populating BasicInfoTab for horse_id: {getattr(horse_data, 'horse_id', 'N/A')}"
        )
        self.current_horse_id = getattr(horse_data, "horse_id", None)

        def get_val(data, key, default=""):
            if isinstance(data, dict):
                return data.get(key, default)
            return getattr(data, key, default)

        self.horse_name_input.setText(str(get_val(horse_data, "horse_name", "")))
        # ... (other fields) ...
        self.account_number_input.setText(
            str(get_val(horse_data, "account_number", ""))
        )
        self.chip_number_input.setText(str(get_val(horse_data, "chip_number", "")))
        self.tattoo_number_input.setText(str(get_val(horse_data, "tattoo_number", "")))
        self.description_input.setPlainText(str(get_val(horse_data, "description", "")))

        species_id = get_val(horse_data, "species_id", None)
        species_obj_on_horse = getattr(horse_data, "species", None)
        self.species_input.blockSignals(True)
        species_id_to_match = (
            species_obj_on_horse.species_id
            if species_obj_on_horse and hasattr(species_obj_on_horse, "species_id")
            else species_id
        )
        if species_id_to_match is not None:
            found = False
            for i in range(self.species_input.count()):
                if self.species_input.itemData(i) == species_id_to_match:
                    self.species_input.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self.species_input.setCurrentIndex(0)
        else:
            self.species_input.setCurrentIndex(0)
        self.species_input.blockSignals(False)

        self.breed_input.setText(str(get_val(horse_data, "breed", "")))
        self.color_input.setText(str(get_val(horse_data, "color", "")))
        sex_value = str(get_val(horse_data, "sex", ""))
        sex_index = self.sex_input.findText(sex_value, Qt.MatchFlag.MatchFixedString)
        self.sex_input.setCurrentIndex(sex_index if sex_index >= 0 else 0)

        # Date of Birth
        dob_val = get_val(horse_data, "date_of_birth", None)
        if isinstance(dob_val, str):
            dob_val = QDate.fromString(dob_val, Qt.DateFormat.ISODate)
        elif isinstance(dob_val, date):
            dob_val = QDate(dob_val.year, dob_val.month, dob_val.day)
        if not isinstance(dob_val, QDate) or not dob_val.isValid():
            dob_val = QDate(2000, 1, 1)
        self.date_of_birth_input.setDate(dob_val)
        self.date_of_birth_input.setSpecialValueText(
            " " if dob_val == QDate(2000, 1, 1) else ""
        )

        # Coggins Date - NEW FIELD
        coggins_val = get_val(horse_data, "coggins_date", None)
        if isinstance(coggins_val, str):
            coggins_val = QDate.fromString(coggins_val, Qt.DateFormat.ISODate)
        elif isinstance(coggins_val, date):
            coggins_val = QDate(coggins_val.year, coggins_val.month, coggins_val.day)
        if not isinstance(coggins_val, QDate) or not coggins_val.isValid():
            coggins_val = QDate(2000, 1, 1)  # sentinel
        self.coggins_date_input.setDate(coggins_val)
        self.coggins_date_input.setSpecialValueText(
            " " if coggins_val == QDate(2000, 1, 1) else ""
        )

        height_val = get_val(horse_data, "height_hands", None)
        self.height_input.setValue(float(height_val) if height_val is not None else 0.0)
        is_active = bool(get_val(horse_data, "is_active", True))
        self.active_status_checkbox.setChecked(is_active)

        date_deceased_val = get_val(horse_data, "date_deceased", None)
        # ... (rest of populate_fields unchanged from v1.2.8) ...
        if date_deceased_val:
            if isinstance(date_deceased_val, str):
                parsed_date_deceased = QDate.fromString(
                    date_deceased_val, Qt.DateFormat.ISODate
                )
                if not parsed_date_deceased.isValid():
                    parsed_date_deceased = QDate.fromString(
                        date_deceased_val, "yyyy-MM-dd"
                    )
                date_deceased_val = parsed_date_deceased
            elif isinstance(date_deceased_val, date):
                date_deceased_val = QDate(
                    date_deceased_val.year,
                    date_deceased_val.month,
                    date_deceased_val.day,
                )

            if (
                isinstance(date_deceased_val, QDate)
                and date_deceased_val.isValid()
                and date_deceased_val != QDate(2000, 1, 1)
            ):
                self.date_deceased_input.setDate(date_deceased_val)
                self.date_deceased_input.setSpecialValueText("")
                self.date_deceased_input.setVisible(not is_active)
                self.date_deceased_label.setVisible(not is_active)
            else:
                self.date_deceased_input.setDate(QDate(2000, 1, 1))
                self.date_deceased_input.setSpecialValueText(" ")
                self.date_deceased_input.setVisible(False)
                self.date_deceased_label.setVisible(False)
        else:
            self.date_deceased_input.setDate(QDate(2000, 1, 1))
            self.date_deceased_input.setSpecialValueText(" ")
            self.date_deceased_input.setVisible(False)
            self.date_deceased_label.setVisible(False)

        location_obj = getattr(horse_data, "location", None)
        location_name_on_horse = getattr(horse_data, "current_location_name", None)
        if location_obj and hasattr(location_obj, "location_name"):
            self.location_display_value.setText(location_obj.location_name)
        elif location_name_on_horse:
            self.location_display_value.setText(location_name_on_horse)
        else:
            self.location_display_value.setText("N/A")

        self.set_form_read_only(True)
        self._has_modifications = False
        self.update_buttons_state(False, True)

    def get_data(self) -> Dict:
        def get_widget_data(widget_name, data_type="text"):
            # ... (unchanged) ...
            widget = getattr(self, widget_name, None)
            if not widget:
                self.logger.warning(f"Widget '{widget_name}' not found in get_data.")
                return None
            if data_type == "text":
                return widget.text().strip()
            if data_type == "plain_text":
                return widget.toPlainText().strip()
            if data_type == "combo_data":
                return widget.currentData()
            if data_type == "combo_text":
                return widget.currentText().strip()
            if data_type == "date":
                q_date = widget.date()
                if widget.specialValueText() == " " or q_date == QDate(2000, 1, 1):
                    return None
                return q_date.toString(Qt.DateFormat.ISODate)
            if data_type == "double":
                return widget.value()
            if data_type == "bool":
                return widget.isChecked()
            return None

        data = {
            "horse_id": self.current_horse_id,
            "horse_name": get_widget_data("horse_name_input"),
            "account_number": get_widget_data("account_number_input"),
            "species_id": get_widget_data("species_input", "combo_data"),
            "breed": get_widget_data("breed_input"),
            "color": get_widget_data("color_input"),
            "sex": (
                get_widget_data("sex_input", "combo_text")
                if get_widget_data("sex_input", "combo_text")
                else None
            ),
            "date_of_birth": get_widget_data("date_of_birth_input", "date"),
            "coggins_date": get_widget_data("coggins_date_input", "date"),  # New Field
            "height_hands": get_widget_data("height_input", "double"),
            "chip_number": get_widget_data("chip_number_input"),
            "tattoo_number": get_widget_data("tattoo_number_input"),
            "description": get_widget_data("description_input", "plain_text"),
            "is_active": get_widget_data("active_status_checkbox", "bool"),
            "date_deceased": get_widget_data("date_deceased_input", "date"),
        }
        return data

    def update_displayed_location(
        self, location_id: Optional[int], location_name: Optional[str]
    ):
        # ... (unchanged from v1.2.8) ...
        print("--- BASICINFOTAB.UPDATE_DISPLAYED_LOCATION CALLED ---")
        self.logger.debug(
            f"BasicInfoTab: update_displayed_location called with ID={location_id}, Name='{location_name}'"
        )
        current_display = self.location_display_value.text()
        new_display = location_name or "N/A"
        print(
            f"--- BASICINFOTAB.UPDATE_DISPLAYED_LOCATION: Current='{current_display}', New='{new_display}' ---"
        )
        if current_display != new_display:
            self.location_display_value.setText(new_display)
            print(
                f"--- BASICINFOTAB.UPDATE_DISPLAYED_LOCATION: Display updated to '{new_display}' ---"
            )
        else:
            print(
                f"--- BASICINFOTAB.UPDATE_DISPLAYED_LOCATION: Display not changed. ---"
            )

    def clear_fields(self, suppress_signal=False):
        # ... (Diagnostic prints retained) ...
        print("--- BASICINFOTAB.CLEAR_FIELDS: START ---")
        self.logger.info(
            f"BasicInfoTab clear_fields called. Suppress signal: {suppress_signal}"
        )

        # ... (clearing of other fields) ...
        if hasattr(self, "horse_name_input"):
            self.horse_name_input.clear()
        if hasattr(self, "account_number_input"):
            self.account_number_input.clear()
        if hasattr(self, "chip_number_input"):
            self.chip_number_input.clear()
        if hasattr(self, "tattoo_number_input"):
            self.tattoo_number_input.clear()
        if hasattr(self, "description_input"):
            self.description_input.clear()

        if hasattr(self, "species_input"):
            self.species_input.blockSignals(True)
            self.species_input.setCurrentIndex(0)
            self.species_input.blockSignals(False)

        if hasattr(self, "breed_input"):
            self.breed_input.clear()
        if hasattr(self, "color_input"):
            self.color_input.clear()

        if hasattr(self, "sex_input"):
            self.sex_input.blockSignals(True)
            self.sex_input.setCurrentIndex(0)
            self.sex_input.blockSignals(False)

        if hasattr(self, "date_of_birth_input"):
            self.date_of_birth_input.setDate(QDate(2000, 1, 1))
            self.date_of_birth_input.setSpecialValueText(" ")

        # Clear Coggins Date - NEW FIELD
        print("--- BASICINFOTAB.CLEAR_FIELDS: Setting coggins_date_input ---")
        if hasattr(self, "coggins_date_input"):
            self.coggins_date_input.setDate(QDate(2000, 1, 1))  # sentinel
            self.coggins_date_input.setSpecialValueText(" ")

        if hasattr(self, "height_input"):
            self.height_input.setValue(0.0)
        if hasattr(self, "location_display_value"):
            self.location_display_value.setText("N/A")
        if hasattr(self, "active_status_checkbox"):
            self.active_status_checkbox.setChecked(True)
        # ... (rest of clear_fields unchanged from v1.2.8) ...
        if hasattr(self, "date_deceased_input"):
            self.date_deceased_input.setDate(QDate(2000, 1, 1))
            self.date_deceased_input.setSpecialValueText(" ")
            self.date_deceased_input.setVisible(False)
        if hasattr(self, "date_deceased_label"):
            self.date_deceased_label.setVisible(False)

        self.current_horse_id = None
        self.set_form_read_only(True)

        if not suppress_signal:
            # ... (logging and signal emission unchanged) ...
            print(
                "--- BASICINFOTAB.CLEAR_FIELDS: Emitting data_modified (suppress_signal=False) ---"
            )
            self.logger.debug(
                "clear_fields: _has_modifications set to False, emitting data_modified."
            )
            self._has_modifications = False
            self.update_buttons_state(False, False)
            self.data_modified.emit()
        else:
            # ... (logging unchanged) ...
            print(
                "--- BASICINFOTAB.CLEAR_FIELDS: Signal suppressed, _has_modifications set to False ---"
            )
            self.logger.debug(
                "clear_fields: _has_modifications set to False (signal suppressed)."
            )
            self._has_modifications = False
            self.update_buttons_state(False, False)
        print("--- BASICINFOTAB.CLEAR_FIELDS: END ---")

    def set_form_read_only(self, read_only):
        # ... (Diagnostic prints retained, logic for QComboBox already corrected in v1.2.8) ...
        # Ensure coggins_date_input is handled.
        print(
            f"--- BASICINFOTAB.SET_FORM_READ_ONLY({read_only}) CALLED (UNCONDITIONAL PRINT) ---"
        )
        for (
            widget_attr_name,
            _,
        ) in (
            self.fields_config
        ):  # Iterates over all fields including coggins_date_input
            widget = getattr(self, widget_attr_name, None)
            if widget:
                if isinstance(
                    widget, (QLineEdit, QTextEdit, QDateEdit, QDoubleSpinBox)
                ):
                    widget.setReadOnly(read_only)
                    widget.setEnabled(True)
                elif isinstance(widget, QComboBox):
                    widget.setDisabled(read_only)
                    widget.setEnabled(True)
                elif isinstance(widget, QPushButton):
                    widget.setEnabled(not read_only)

        if hasattr(self, "active_status_checkbox"):
            self.active_status_checkbox.setEnabled(not read_only)

        if (
            hasattr(self, "active_status_checkbox")
            and hasattr(self, "date_deceased_input")
            and hasattr(self, "date_deceased_label")
        ):
            is_active = self.active_status_checkbox.isChecked()
            can_edit_deceased_date = not read_only and not is_active

            self.date_deceased_input.setVisible(not is_active)
            self.date_deceased_label.setVisible(not is_active)

            if isinstance(self.date_deceased_input, QDateEdit):
                self.date_deceased_input.setReadOnly(not can_edit_deceased_date)

        if hasattr(self, "horse_name_input"):
            print(
                f"--- BASICINFOTAB.SET_FORM_READ_ONLY: horse_name_input.isReadOnly() = {self.horse_name_input.isReadOnly()} ---"
            )
            print(
                f"--- BASICINFOTAB.SET_FORM_READ_ONLY: horse_name_input.isEnabled() = {self.horse_name_input.isEnabled()} ---"
            )

    def update_buttons_state(self, has_modifications: bool, is_existing_horse: bool):
        # ... (unchanged) ...
        self.save_btn.setEnabled(has_modifications)
        self.discard_btn.setEnabled(has_modifications)

    def _mark_modified(self, *args):
        # ... (unchanged from v1.2.8 - relies on signal blocking for programmatic changes) ...
        if hasattr(self, "horse_name_input") and self.horse_name_input.isReadOnly():
            if not self._has_modifications:
                self.logger.debug(
                    "_mark_modified: Change occurred while form is read-only or modification already flagged."
                )
            return

        if not self._has_modifications:
            self.logger.info("Form data modified by user.")
            self._has_modifications = True
            self.update_buttons_state(True, self.current_horse_id is not None)
            self.data_modified.emit()

    def _confirm_discard(self):
        # ... (unchanged) ...
        if self._has_modifications:
            if self.parent_view and hasattr(self.parent_view, "show_question"):
                if self.parent_view.show_question(
                    "Confirm Discard", "Discard unsaved changes to basic info?"
                ):
                    self.discard_requested.emit()
                else:
                    return
            else:
                self.discard_requested.emit()
        else:
            self.discard_requested.emit()

    def _on_active_status_changed(self, state_value):
        # ... (unchanged from v1.2.8) ...
        is_active = self.active_status_checkbox.isChecked()
        if hasattr(self, "date_deceased_input") and hasattr(
            self, "date_deceased_label"
        ):
            self.date_deceased_input.setVisible(not is_active)
            self.date_deceased_label.setVisible(not is_active)
            if is_active:
                self.date_deceased_input.setDate(QDate(2000, 1, 1))
                self.date_deceased_input.setSpecialValueText(" ")
        self.toggle_active_requested.emit(is_active)
        self._mark_modified()

    def set_new_mode(self):
        # ... (Diagnostic print retained, logic unchanged from v1.2.8) ...
        print("--- BASICINFOTAB.SET_NEW_MODE CALLED (UNCONDITIONAL PRINT) ---")
        self.logger.info("BasicInfoTab set to new mode.")
        self.current_horse_id = None
        self.clear_fields(suppress_signal=True)
        self.set_form_read_only(False)
        self.update_buttons_state(True, False)
        self._has_modifications = True
        if hasattr(self, "horse_name_input"):
            self.horse_name_input.setFocus()

    def set_edit_mode(self):
        # ... (unchanged from v1.2.8) ...
        self.logger.info(
            f"BasicInfoTab set to edit mode for horse_id: {self.current_horse_id}"
        )
        self.set_form_read_only(False)
        self.update_buttons_state(self._has_modifications, True)
        if hasattr(self, "horse_name_input"):
            self.horse_name_input.setFocus()
