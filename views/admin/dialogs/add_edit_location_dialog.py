# views/admin/dialogs/add_edit_location_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Location Dialog
Version: 1.0.0
Purpose: Dialog for creating and editing practice locations.
Last Updated: May 19, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-05-19):
    - Initial implementation for adding and editing locations.
    - Fields: Location Name, Description, Is Active.
    - Uses LocationController for backend operations.
    - Styled for dark theme using imported constants.
"""
# Ensure NO leading spaces/tabs before this comment or the imports below

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.location_controller import LocationController
from models import Location as LocationModel

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
        self.controller = controller
        self.current_user_id = current_user_id
        self.location = location
        self.is_edit_mode = location is not None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Location")
        self.setMinimumWidth(450)

        self._setup_palette()
        self._setup_ui()
        if self.is_edit_mode and self.location:
            self._populate_fields()

    def _get_dialog_specific_input_field_style(self) -> str:
        """Generates style string for input fields within this dialog."""
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
        """

    def _get_dialog_generic_button_style(self) -> str:
        """Generates generic button style string for this dialog."""
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
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        input_style = self._get_dialog_specific_input_field_style()
        dialog_styles = (
            f"QLabel {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; padding-top:3px; }}"
            + f"QCheckBox::indicator {{ width: 13px; height: 13px; }}"
        )
        self.setStyleSheet(dialog_styles)

        self.location_name_input = QLineEdit()
        self.location_name_input.setStyleSheet(input_style)
        self.location_name_input.setPlaceholderText("e.g., Main Barn, Paddock A")
        form_layout.addRow("Location Name*:", self.location_name_input)

        self.description_input = QTextEdit()
        self.description_input.setStyleSheet(input_style)
        self.description_input.setPlaceholderText(
            "Optional description or details about the location"
        )
        self.description_input.setFixedHeight(80)
        form_layout.addRow("Description:", self.description_input)

        self.is_active_checkbox = QCheckBox("Location is Active")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("", self.is_active_checkbox)

        layout.addLayout(form_layout)

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
                ok_bg_color = DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4 and ok_bg_color.startswith("#"):
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        layout.addWidget(self.button_box)

    def _populate_fields(self):
        """Populates fields if in edit mode."""
        if self.location:
            self.location_name_input.setText(self.location.location_name)
            self.description_input.setPlainText(self.location.description or "")
            self.is_active_checkbox.setChecked(self.location.is_active)

    def get_data(self) -> Dict[str, Any]:
        """Collects data from the form fields."""
        return {
            "location_name": self.location_name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "is_active": self.is_active_checkbox.isChecked(),
        }

    def validate_and_accept(self):
        """Validates form data and accepts dialog if valid."""
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
                success, message = self.controller.update_location(
                    self.location.location_id, data, self.current_user_id
                )
            else:
                success, message, _ = self.controller.create_location(
                    data, self.current_user_id
                )

            if success:
                if hasattr(self.parent(), "show_info"):
                    self.parent().show_info("Success", message)
                else:
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
