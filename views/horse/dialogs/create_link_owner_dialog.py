# views/horse/dialogs/create_link_owner_dialog.py
"""
EDSI Veterinary Management System - Create New Owner and Link Dialog
Version: 1.0.8
Purpose: Dialog for creating a new owner and linking them to a horse with a percentage.
         - Corrected tuple unpacking error in _setup_ui by ensuring all field
           definitions in `fields_setup` list have a consistent number of elements.
Last Updated: May 26, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.0.8 (2025-05-26):
    - In `_setup_ui`, standardized the tuples in the `fields_setup` list to consistently
      provide 8 elements (label, name, layout coordinates, widget_type_str, placeholder).
    - Updated the for-loop unpacking these tuples to match the 8 elements,
      resolving the "ValueError: not enough values to unpack".
- v1.0.7 (2025-05-26):
    - Modified `__init__` to accept an optional `total_ownership_validator` callback.
    - Updated `validate_and_accept` to call this external validator.
- v1.0.6 (2025-05-26):
    - Redesigned UI to use a two-column QGridLayout for owner detail fields.
# ... (rest of previous changelog entries assumed present)
"""

import logging
from typing import Optional, Dict, List, Callable

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QWidget,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.owner_controller import OwnerController

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_INPUT_FIELD_BACKGROUND,
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
    DARK_HEADER_FOOTER,
)


class CreateAndLinkOwnerDialog(QDialog):
    def __init__(
        self,
        parent_view,
        horse_name: str,
        current_user_login: str,
        total_ownership_validator: Optional[
            Callable[[Optional[int], float], bool]
        ] = None,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_name = horse_name
        self.current_user_login = current_user_login
        self.owner_controller = OwnerController()
        self.total_ownership_validator = total_ownership_validator

        self.setWindowTitle(f"Create & Link New Owner to {self.horse_name}")
        self.setMinimumWidth(750)

        self._setup_palette()
        self._setup_ui()

        if "state_code" in self.form_fields and isinstance(
            self.form_fields["state_code"], QComboBox
        ):
            self._populate_states_combo(self.form_fields["state_code"])

    def _get_dialog_specific_input_field_style(self):
        # (Same as v1.0.7)
        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent; subcontrol-position: right center; width: 15px; }}
            QComboBox::down-arrow {{ image: url(none); }} /* Consider a Qt built-in or SVG icon for better dark theme compatibility */
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }} """

    def _get_dialog_generic_button_style(self):
        # (Same as v1.0.7)
        return (
            f"QPushButton {{background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _setup_palette(self):
        # (Same as v1.0.7)
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

    def _setup_ui(self):
        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setSpacing(15)
        main_dialog_layout.setContentsMargins(15, 15, 15, 15)

        instruction_label = QLabel(
            f"Enter details for the new owner to be linked to <b>{self.horse_name}</b>."
        )
        instruction_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-bottom: 5px; background-color: transparent;"
        )
        instruction_label.setWordWrap(True)
        main_dialog_layout.addWidget(instruction_label)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)

        self.form_fields = {}
        specific_input_style = self._get_dialog_specific_input_field_style()

        # Each tuple: (Label, field_name, r_lbl, c_lbl, r_fld, c_fld, widget_type_str, placeholder_or_None)
        fields_setup = [
            ("Farm Name:", "farm_name", 0, 0, 0, 1, "QLineEdit", None),
            ("Account #:", "account_number", 0, 2, 0, 3, "QLineEdit", None),
            ("First Name:", "first_name", 1, 0, 1, 1, "QLineEdit", None),
            ("Last Name*:", "last_name", 1, 2, 1, 3, "QLineEdit", None),
            ("Address 1*:", "address_line1", 2, 0, 2, 1, "QLineEdit", None),
            ("Address 2:", "address_line2", 2, 2, 2, 3, "QLineEdit", None),
            ("City*:", "city", 3, 0, 3, 1, "QLineEdit", None),
            ("State*:", "state_code", 3, 2, 3, 3, "QComboBox", None),
            ("Zip/Postal*:", "zip_code", 4, 0, 4, 1, "QLineEdit", None),
            ("Country:", "country_name", 4, 2, 4, 3, "QLineEdit", "e.g. USA"),
            ("Phone:", "phone", 5, 0, 5, 1, "QLineEdit", None),
            ("Email:", "email", 5, 2, 5, 3, "QLineEdit", None),
        ]

        for (
            label_text,
            field_name,
            r_lbl,
            c_lbl,
            r_fld,
            c_fld,
            widget_type_str,
            placeholder_text,
        ) in fields_setup:
            lbl = QLabel(label_text)
            grid_layout.addWidget(lbl, r_lbl, c_lbl, Qt.AlignmentFlag.AlignRight)

            widget: QWidget  # Type hint for clarity
            if widget_type_str == "QComboBox":
                widget = QComboBox()
            else:  # Default to QLineEdit
                widget = QLineEdit()
                if placeholder_text:  # Check if placeholder_text is not None
                    widget.setPlaceholderText(placeholder_text)

            widget.setStyleSheet(specific_input_style)
            self.form_fields[field_name] = widget
            grid_layout.addWidget(widget, r_fld, c_fld)

        # Row 6: Ownership Percentage and Active Checkbox
        self.percentage_input = QDoubleSpinBox()
        self.percentage_input.setRange(0.00, 100.00)
        self.percentage_input.setDecimals(2)
        self.percentage_input.setSuffix(" %")
        self.percentage_input.setValue(100.00)
        self.percentage_input.setStyleSheet(specific_input_style)
        grid_layout.addWidget(
            QLabel("Ownership %*:"), 6, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.percentage_input, 6, 1)

        self.form_fields["is_active"] = QCheckBox("Owner is Active")
        self.form_fields["is_active"].setChecked(True)
        self.form_fields["is_active"].setStyleSheet(
            f"QCheckBox{{color:{DARK_TEXT_SECONDARY};background:transparent;padding-top:3px;}}QCheckBox::indicator{{width:13px;height:13px;}}"
        )
        grid_layout.addWidget(
            self.form_fields["is_active"],
            6,
            3,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )  # Align left in its cell

        main_dialog_layout.addLayout(grid_layout)
        main_dialog_layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Create & Link Owner"
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
                ok_bg = DARK_SUCCESS_ACTION
                ok_bg = (
                    f"#{ok_bg[1]*2}{ok_bg[2]*2}{ok_bg[3]*2}"
                    if len(ok_bg) == 4
                    else ok_bg
                )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton{{background-color:{ok_bg};color:white;}}"
                )
        main_dialog_layout.addWidget(self.button_box)
        self.setStyleSheet(
            f"QDialog{{background-color:{DARK_WIDGET_BACKGROUND};}} QLabel{{color:{DARK_TEXT_SECONDARY};background:transparent;padding-top:3px;}} QCheckBox::indicator{{width:13px;height:13px;}} QCheckBox{{color:{DARK_TEXT_SECONDARY};}}"
        )

    def _populate_states_combo(self, combo_box: QComboBox):
        # (Same as v1.0.7)
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states: List[Dict[str, str]] = ref_data.get("states", [])
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("", None)
            for state_data in states:
                combo_box.addItem(state_data["name"], state_data["id"])
            combo_box.blockSignals(False)
            self.logger.debug(f"Populated states: {len(states)}")
        except Exception as e:
            self.logger.error(f"Error populating states: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", "Could not load states.")

    def validate_and_accept(self):
        # (Same as v1.0.7 - calls self.total_ownership_validator)
        owner_data = {}
        for field_name, widget in self.form_fields.items():
            if isinstance(widget, QLineEdit):
                owner_data[field_name] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                owner_data[field_name] = widget.currentData()
            elif isinstance(widget, QCheckBox):
                owner_data[field_name] = widget.isChecked()
        percentage = self.percentage_input.value()

        is_valid, errors = self.owner_controller.validate_owner_data(
            owner_data, is_new=True
        )
        if not is_valid:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct owner details:\n- " + "\n- ".join(errors),
            )
            return
        if not (0.00 <= percentage <= 100.00):
            QMessageBox.warning(
                self,
                "Input Error",
                "Ownership percentage must be between 0.00 and 100.00.",
            )
            return
        if self.total_ownership_validator:
            if not self.total_ownership_validator(
                None, percentage
            ):  # Pass None for owner_id_being_changed (new owner)
                self.logger.debug(
                    "External total ownership validation failed for new owner link."
                )
                return
        self.logger.debug("CreateAndLinkOwnerDialog validation successful, accepting.")
        super().accept()

    def get_data(self) -> Optional[Dict]:
        # (Same as v1.0.7)
        owner_details = {}
        for field_name, widget in self.form_fields.items():
            if isinstance(widget, QLineEdit):
                owner_details[field_name] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                owner_details[field_name] = widget.currentData()
            elif isinstance(widget, QCheckBox):
                owner_details[field_name] = widget.isChecked()
        return {
            "owner_details": owner_details,
            "percentage": self.percentage_input.value(),
        }
