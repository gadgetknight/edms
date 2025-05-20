# views/horse/tabs/basic_info_tab.py

"""
EDSI Veterinary Management System - Horse Basic Info Tab
Version: 1.0.4
Purpose: Provides a tab widget for displaying and editing basic horse information.
         Corrects enable/disable logic for Save/Discard buttons, especially for new horses.
Last Updated: May 19, 2025
Author: Claude Assistant

Changelog:
- v1.0.4 (2025-05-19):
    - Modified `update_buttons_state` to enable Save/Discard buttons if
      `has_modifications` is true AND the form is currently editable,
      fixing the issue where Save was not enabled for new horses.
- v1.0.3 (2025-05-19):
    - Added `_emit_data_modified` slot to correctly handle argument-emitting signals
      from input widgets and emit the argument-less `data_modified` signal,
      resolving the TypeError.
- v1.0.2 (2025-05-18):
    - Corrected AppConfig constant usage. Imported constants directly instead of
      accessing them via the AppConfig class.
- v1.0.1 (2025-05-17):
    - Added `from typing import List` to resolve NameError.
- v1.0.0 (2025-05-17):
    - Initial extraction from horse_unified_management.py.
"""

import logging
from typing import Optional, Dict, Callable, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_INPUT_FIELD_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DARK_BORDER,
    DARK_BUTTON_HOVER,
    DARK_BUTTON_BG,
    DARK_PRIMARY_ACTION,
    DARK_SUCCESS_ACTION,
    DARK_WARNING_ACTION,
    DARK_ITEM_HOVER,
    DARK_HEADER_FOOTER,
    DEFAULT_FONT_FAMILY,
)
from models import Horse


class BasicInfoTab(QWidget):
    """Tab widget for displaying and editing basic horse information."""

    data_modified = Signal()
    save_requested = Signal()
    discard_requested = Signal()
    toggle_active_requested = Signal(bool)

    def __init__(self, parent_view, horse_controller):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_controller = horse_controller

        self.current_horse_is_active: Optional[bool] = None

        self.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND}; border: none;"
        )

        form_container_widget = QWidget()
        form_container_widget.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND};"
        )

        form_layout = QGridLayout(form_container_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        self.form_fields: Dict[str, QWidget] = {}
        self._fields_config = [
            ("Name", "horse_name", "text", True),
            ("Account Number", "account_number", "text", False),
            ("Breed", "breed", "text", False),
            ("Color", "color", "text", False),
            ("Sex", "sex", "combo", False),
            ("Date of Birth", "date_of_birth", "date", False),
            ("Reg. Number", "registration_number", "text", False),
            ("Microchip ID", "microchip_id", "text", False),
            ("Tattoo", "tattoo", "text", False),
            ("Brand", "brand", "text", False),
            ("Location", "current_location_id", "combo", False),
            ("Band/Tag", "band_tag_number", "text", False),
        ]

        self._setup_form_fields(form_layout)
        self._setup_action_buttons(form_layout)

        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setRowStretch((len(self._fields_config) + 1) // 2 + 1, 1)

        scroll_area.setWidget(form_container_widget)
        main_layout.addWidget(scroll_area)
        self.set_form_read_only(
            True
        )  # Initially read-only until a horse is selected for edit or new horse mode

    def _get_input_style(self):
        if hasattr(self.parent_view, "get_form_input_style"):
            return self.parent_view.get_form_input_style()
        return f"QLineEdit, QComboBox, QDateEdit {{ background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; padding: 5px; }}"

    def _get_calendar_style(self):
        return (
            f"QCalendarWidget QWidget {{ alternate-background-color: {DARK_BUTTON_HOVER}; background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; }} "
            f"QCalendarWidget QToolButton {{ color: {DARK_TEXT_PRIMARY}; background-color: {DARK_BUTTON_BG}; border: 1px solid {DARK_BORDER}; margin: 2px; padding: 5px; }} "
            f"QCalendarWidget QToolButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QCalendarWidget QAbstractItemView:enabled {{ color: {DARK_TEXT_PRIMARY}; selection-background-color: {DARK_PRIMARY_ACTION}; }} "
            f"QCalendarWidget QAbstractItemView:disabled {{ color: {DARK_TEXT_TERTIARY}; }} "
            f"QCalendarWidget QMenu {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; }} "
            f"QCalendarWidget QSpinBox {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER};}} "
            f"#qt_calendar_navigationbar {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_PRIMARY}; }} "
            f"#qt_calendar_prevmonth, #qt_calendar_nextmonth {{ qproperty-icon: none; }} "
            f"#qt_calendar_monthbutton, #qt_calendar_yearbutton {{ color: {DARK_TEXT_PRIMARY}; }}"
        )

    def _emit_data_modified(self, *args):
        """Slot to catch arguments from widget signals and emit data_modified without arguments."""
        self.data_modified.emit()

    def _setup_form_fields(self, form_layout: QGridLayout):
        input_style = self._get_input_style()
        calendar_style = self._get_calendar_style()

        for i, (label_text, field_name, field_type, required) in enumerate(
            self._fields_config
        ):
            row, col = i // 2, (i % 2)
            label_str = label_text + ("*" if required else "") + ":"
            label = QLabel(label_str)
            label.setStyleSheet(
                f"font-weight: {'bold' if required else '500'}; color: {DARK_TEXT_SECONDARY}; font-size: 12px; background: transparent; padding-top: 5px;"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            field_widget: Optional[QWidget] = None
            if field_type == "text":
                field_widget = QLineEdit()
                field_widget.textChanged.connect(self._emit_data_modified)
            elif field_type == "combo":
                field_widget = QComboBox()
                if field_name == "sex":
                    field_widget.addItems(
                        ["", "Male", "Female", "Gelding", "Stallion", "Mare"]
                    )
                field_widget.currentIndexChanged.connect(self._emit_data_modified)
            elif field_type == "date":
                field_widget = QDateEdit()
                field_widget.setCalendarPopup(True)
                field_widget.setDate(QDate.currentDate())  # Sensible default
                if field_widget.calendarWidget():
                    field_widget.calendarWidget().setStyleSheet(calendar_style)
                field_widget.dateChanged.connect(self._emit_data_modified)

            if field_widget:
                field_widget.setStyleSheet(input_style)
                field_widget.setMinimumHeight(32)
                form_layout.addWidget(label, row, col * 2)
                form_layout.addWidget(field_widget, row, col * 2 + 1)
                self.form_fields[field_name] = field_widget

    def _setup_action_buttons(self, form_layout: QGridLayout):
        self.save_btn = QPushButton("💾 Save Changes")
        if hasattr(self.parent_view, "get_toolbar_button_style"):
            self.save_btn.setStyleSheet(
                self.parent_view.get_toolbar_button_style(DARK_PRIMARY_ACTION)
            )
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_requested.emit)

        self.discard_btn = QPushButton("↩️ Discard Changes")
        if hasattr(self.parent_view, "get_generic_button_style"):
            discard_style = f"""
                QPushButton {{
                    background-color: transparent; color: {DARK_TEXT_SECONDARY};
                    border: 1px solid {DARK_BORDER}; border-radius: 4px;
                    padding: 6px 12px; font-size: 13px; font-weight: 500; min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {DARK_ITEM_HOVER}; border-color: {DARK_TEXT_SECONDARY};
                    color: {DARK_TEXT_PRIMARY};
                }}
                QPushButton:disabled {{
                    background-color: transparent; border-color: {DARK_BORDER};
                    color: {DARK_TEXT_TERTIARY}; opacity: 0.7;
                }}
            """
            self.discard_btn.setStyleSheet(discard_style)
        self.discard_btn.setEnabled(False)
        self.discard_btn.clicked.connect(self.discard_requested.emit)

        self.toggle_active_btn = QPushButton("Deactivate")
        if hasattr(self.parent_view, "get_generic_button_style"):
            self.toggle_active_btn.setStyleSheet(
                self.parent_view.get_generic_button_style()
            )
        self.toggle_active_btn.setEnabled(False)
        self.toggle_active_btn.clicked.connect(self._on_toggle_active_clicked)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_active_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.discard_btn)
        button_layout.addWidget(self.save_btn)

        form_layout.addLayout(
            button_layout, (len(self._fields_config) + 1) // 2, 0, 1, 4
        )

    def _on_toggle_active_clicked(self):
        if self.current_horse_is_active is not None:
            self.toggle_active_requested.emit(self.current_horse_is_active)

    def populate_fields(self, horse: Horse):
        self.logger.debug(
            f"Populating BasicInfoTab for horse ID: {horse.horse_id if horse else 'None'}"
        )
        for field_widget in self.form_fields.values():  # Block all first
            field_widget.blockSignals(True)

        if not horse:  # No horse selected or clearing for new
            self.clear_fields()  # This handles unblocking and button updates
            self.current_horse_is_active = None
            self.set_form_read_only(True)  # If no horse, form should be read-only
            self.update_buttons_state(False, False)
            return

        self.current_horse_is_active = horse.is_active

        self.form_fields["horse_name"].setText(horse.horse_name or "")
        self.form_fields["account_number"].setText(horse.account_number or "")
        self.form_fields["breed"].setText(horse.breed or "")
        self.form_fields["color"].setText(horse.color or "")
        sex_combo: QComboBox = self.form_fields["sex"]
        sex_index = sex_combo.findText(horse.sex or "", Qt.MatchFlag.MatchFixedString)
        sex_combo.setCurrentIndex(sex_index if sex_index >= 0 else 0)
        dob_field: QDateEdit = self.form_fields["date_of_birth"]
        dob_field.setDate(
            QDate(horse.date_of_birth) if horse.date_of_birth else QDate.currentDate()
        )
        self.form_fields["registration_number"].setText(horse.registration_number or "")
        self.form_fields["microchip_id"].setText(horse.microchip_id or "")
        self.form_fields["tattoo"].setText(horse.tattoo or "")
        self.form_fields["brand"].setText(horse.brand or "")
        self.form_fields["band_tag_number"].setText(horse.band_tag_number or "")

        location_combo: QComboBox = self.form_fields["current_location_id"]
        loc_index = location_combo.findData(horse.current_location_id)
        location_combo.setCurrentIndex(loc_index if loc_index >= 0 else 0)

        for field_widget in self.form_fields.values():  # Unblock all
            field_widget.blockSignals(False)

        self.set_form_read_only(
            True
        )  # After populating existing horse, form is read-only initially
        self.update_buttons_state(
            False, True
        )  # No modifications yet, existing horse selected

    def get_data(self) -> Optional[Dict[str, any]]:
        try:
            date_field: QDateEdit = self.form_fields["date_of_birth"]
            birth_date = (
                date_field.date().toPython() if date_field.date().isValid() else None
            )

            data = {
                "horse_name": self.form_fields["horse_name"].text().strip(),
                "account_number": self.form_fields["account_number"].text().strip(),
                "breed": self.form_fields["breed"].text().strip(),
                "color": self.form_fields["color"].text().strip(),
                "sex": self.form_fields["sex"].currentText() or None,
                "date_of_birth": birth_date,
                "registration_number": self.form_fields["registration_number"]
                .text()
                .strip(),
                "microchip_id": self.form_fields["microchip_id"].text().strip(),
                "tattoo": self.form_fields["tattoo"].text().strip(),
                "brand": self.form_fields["brand"].text().strip(),
                "band_tag_number": self.form_fields["band_tag_number"].text().strip(),
                "current_location_id": self.form_fields[
                    "current_location_id"
                ].currentData(),
            }
            return data
        except Exception as e:
            self.logger.error(
                f"Error collecting data from BasicInfoTab: {e}", exc_info=True
            )
            return None

    def clear_fields(self):
        self.current_horse_is_active = None
        for field_name, field_widget in self.form_fields.items():
            was_blocked = field_widget.signalsBlocked()
            field_widget.blockSignals(True)
            if isinstance(field_widget, QLineEdit):
                field_widget.clear()
            elif isinstance(field_widget, QComboBox):
                # Assuming the first item is the blank/default one
                field_widget.setCurrentIndex(0)
            elif isinstance(field_widget, QDateEdit):
                field_widget.setDate(QDate.currentDate())  # Reset to current date
            field_widget.blockSignals(was_blocked)
        # After clearing, form is for new entry, so not read-only, and no modifications yet
        self.set_form_read_only(False)
        self.update_buttons_state(False, False)  # is_horse_selected is False for new

    def set_new_mode(self):
        self.clear_fields()  # This now sets form editable and updates buttons for no mods/no selected horse
        if "horse_name" in self.form_fields:
            self.form_fields["horse_name"].setFocus()
        # Parent (HorseUnifiedManagement) will call update_buttons_state on this tab
        # with has_modifications=True, is_horse_selected=False, which is correct.

    def set_form_read_only(self, read_only: bool):
        for field_widget in self.form_fields.values():
            if hasattr(field_widget, "setReadOnly"):
                field_widget.setReadOnly(read_only)
            else:
                field_widget.setEnabled(not read_only)
        self.logger.debug(f"BasicInfoTab form read-only state set to: {read_only}")
        # When form read-only state changes, it might affect button states.
        # However, button states are primarily driven by has_modifications and is_horse_selected
        # which are passed from the parent view. This direct call here might be redundant or
        # could interfere if called out of sync with parent's state.
        # Consider if parent's update_main_action_buttons_state covers this.
        # For now, let's rely on parent to call update_buttons_state.

    def update_buttons_state(
        self, has_modifications: bool, is_existing_horse_selected: bool
    ):
        """
        Updates the state of Save, Discard, and Toggle Active buttons.
        Args:
            has_modifications (bool): True if data in the tab has been changed.
            is_existing_horse_selected (bool): True if an existing horse is loaded (not a new one).
        """
        form_is_currently_editable = False
        # Check if a representative field (e.g., horse_name) is editable
        if "horse_name" in self.form_fields:
            if hasattr(self.form_fields["horse_name"], "isReadOnly"):
                form_is_currently_editable = not self.form_fields[
                    "horse_name"
                ].isReadOnly()
            elif hasattr(
                self.form_fields["horse_name"], "isEnabled"
            ):  # Fallback for widgets like QComboBox
                form_is_currently_editable = self.form_fields["horse_name"].isEnabled()
        else:
            # If no form fields yet (e.g., during setup), assume not editable for safety
            self.logger.warning(
                "update_buttons_state called before form_fields['horse_name'] is available."
            )

        can_save_or_discard = has_modifications and form_is_currently_editable
        self.save_btn.setEnabled(can_save_or_discard)
        self.discard_btn.setEnabled(can_save_or_discard)

        self.toggle_active_btn.setEnabled(is_existing_horse_selected)

        if is_existing_horse_selected and self.current_horse_is_active is not None:
            self.toggle_active_btn.setText(
                "Deactivate" if self.current_horse_is_active else "Activate"
            )
            warn_color = (
                DARK_WARNING_ACTION
                if self.current_horse_is_active
                else DARK_SUCCESS_ACTION
            )
            if hasattr(self.parent_view, "get_toolbar_button_style"):
                self.toggle_active_btn.setStyleSheet(
                    self.parent_view.get_toolbar_button_style(warn_color)
                )
        else:  # New horse or no horse selected
            self.toggle_active_btn.setText("Toggle Active")  # Generic text
            if hasattr(self.parent_view, "get_generic_button_style"):
                self.toggle_active_btn.setStyleSheet(
                    self.parent_view.get_generic_button_style()
                )

    def populate_locations_combo(self, locations_data: List[Dict[str, any]]):
        combo: QComboBox = self.form_fields.get("current_location_id")
        if combo:
            current_data = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("", None)
            for loc_data in locations_data:
                combo.addItem(loc_data["name"], loc_data["id"])
            index = combo.findData(current_data)
            combo.setCurrentIndex(index if index != -1 else 0)
            combo.blockSignals(False)
        else:
            self.logger.warning(
                "Location combo box not found in form_fields for population."
            )
