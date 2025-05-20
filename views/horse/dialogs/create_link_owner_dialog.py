# views/horse/dialogs/create_link_owner_dialog.py
"""
EDSI Veterinary Management System - Create New Owner and Link Dialog
Version: 1.0.5
Purpose: Dialog for creating a new owner and linking them to a horse with a percentage.
         Allows 0% ownership and ensures dialog stays open on validation error.
Last Updated: May 19, 2025
Author: Claude Assistant

Changelog:
- v1.0.5 (2025-05-19):
    - Changed percentage_input range and validation to allow 0.00%.
    - Ensured dialog validation logic explicitly keeps dialog open on error.
- v1.0.4 (2025-05-19):
    - Changed "Phone*:" label to "Phone:" to reflect it's not a mandatory field.
- v1.0.3 (2025-05-19):
    - Corrected `scroll_area.setFrameShape(QWidget.Shape.NoFrame)` to
      `scroll_area.setFrameShape(QFrame.Shape.NoFrame)`.
- v1.0.2 (2025-05-19):
    - Resolved AppConfig constant AttributeError by importing constants directly.
    - Removed import of UserManagementScreen and localized style helper methods.
"""

import logging
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.owner_controller import OwnerController
from models import Owner as OwnerModel

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
    def __init__(self, parent_view, horse_name: str, current_user_login: str):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.horse_name = horse_name
        self.current_user_login = current_user_login
        self.owner_controller = OwnerController()

        self.setWindowTitle(f"Create & Link New Owner to {self.horse_name}")
        self.setMinimumWidth(600)

        self._setup_palette()
        self._setup_ui()

        if "state_code" in self.form_fields and isinstance(
            self.form_fields["state_code"], QComboBox
        ):
            self._populate_states_combo(self.form_fields["state_code"])

    def _get_dialog_specific_input_field_style(self):
        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent; subcontrol-position: right center; width: 15px; }}
            QComboBox::down-arrow {{ image: url(none); }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }} """

    def _get_dialog_generic_button_style(self):
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

    def _setup_ui(self):
        main_dialog_layout = QVBoxLayout(self)
        instruction_label = QLabel(
            f"Enter details for the new owner to be linked to <b>{self.horse_name}</b>."
        )
        instruction_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-bottom: 10px; background-color: transparent;"
        )
        instruction_label.setWordWrap(True)
        main_dialog_layout.addWidget(instruction_label)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND}; border: none;"
        )
        form_container_widget = QWidget()
        form_container_widget.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND};"
        )
        form_layout = QFormLayout(form_container_widget)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)
        dialog_specific_styles = (
            f"QLabel {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
            + f"QCheckBox::indicator {{ width: 13px; height: 13px; }}"
        )
        self.setStyleSheet(dialog_specific_styles)
        self.form_fields = {}
        specific_input_style = self._get_dialog_specific_input_field_style()
        dialog_fields = [
            ("Account #:", "account_number", "QLineEdit", ""),
            ("Farm Name:", "farm_name", "QLineEdit", ""),
            ("First Name:", "first_name", "QLineEdit", ""),
            ("Last Name*:", "last_name", "QLineEdit", ""),
            ("Address 1*:", "address_line1", "QLineEdit", ""),
            ("Address 2:", "address_line2", "QLineEdit", ""),
            ("City*:", "city", "QLineEdit", ""),
            ("State*:", "state_code", "QComboBox", ""),
            ("Zip/Postal*:", "zip_code", "QLineEdit", ""),
            ("Country:", "country_name", "QLineEdit", "e.g. USA"),
            ("Phone:", "phone", "QLineEdit", ""),
            ("Email:", "email", "QLineEdit", ""),
        ]
        for label_text, field_name, widget_type, placeholder in dialog_fields:
            label_widget = QLabel(label_text)
            if widget_type == "QLineEdit":
                widget = QLineEdit()
                if placeholder:
                    widget.setPlaceholderText(placeholder)
            elif widget_type == "QComboBox":
                widget = QComboBox()
            else:
                widget = QLineEdit()
            widget.setStyleSheet(specific_input_style)
            self.form_fields[field_name] = widget
            form_layout.addRow(label_widget, widget)
        self.form_fields["is_active"] = QCheckBox("Owner is Active")
        self.form_fields["is_active"].setChecked(True)
        form_layout.addRow("", self.form_fields["is_active"])
        self.percentage_input = QDoubleSpinBox()
        self.percentage_input.setRange(0.00, 100.00)  # MODIFIED: Allow 0.00
        self.percentage_input.setDecimals(2)
        self.percentage_input.setSuffix(" %")
        self.percentage_input.setValue(100.00)
        self.percentage_input.setStyleSheet(specific_input_style)
        form_layout.addRow("Ownership %*:", self.percentage_input)
        scroll_area.setWidget(form_container_widget)
        main_dialog_layout.addWidget(scroll_area)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Connect accepted to validate_and_accept, which will decide to call super().accept()
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(
            self.reject
        )  # reject() will close the dialog with Rejected status
        generic_button_style = self._get_dialog_generic_button_style()
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(generic_button_style)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4 and ok_bg_color.startswith("#"):
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        main_dialog_layout.addWidget(self.button_box)

    def _populate_states_combo(self, combo_box: QComboBox):
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states: List[Dict[str, str]] = ref_data.get("states", [])
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("", None)
            for state_data in states:
                combo_box.addItem(state_data["name"], state_data["id"])
            combo_box.blockSignals(False)
            self.logger.debug(f"Populated states combo with {len(states)} states.")
        except Exception as e:
            self.logger.error(f"Error populating states combo: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", "Could not load states for the form.")

    def validate_and_accept(self):
        """Validates the form data. If valid, accepts the dialog. Otherwise, shows errors and keeps dialog open."""
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
            return  # Explicitly return, do not call accept()

        if not (0.00 <= percentage <= 100.00):  # MODIFIED: Allow 0.00
            QMessageBox.warning(
                self,
                "Input Error",
                "Ownership percentage must be between 0.00 and 100.00.",
            )
            return  # Explicitly return, do not call accept()

        self.logger.debug("CreateAndLinkOwnerDialog validation successful, accepting.")
        super().accept()  # Only accept if all validations pass

    def get_data(self) -> Optional[Dict]:
        """Returns the collected data if the dialog was accepted. Should be called by the parent."""
        # This method assumes validation has already passed if dialog was accepted.
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
