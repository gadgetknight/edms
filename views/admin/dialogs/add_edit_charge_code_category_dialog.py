# views/admin/dialogs/add_edit_charge_code_category_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Charge Code Category/Process Dialog
Version: 1.0.0
Purpose: Dialog for creating and editing charge code categories (Level 1)
         and processes (Level 2).
Last Updated: June 3, 2025
Author: Gemini
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt

from controllers.charge_code_controller import ChargeCodeController
from models import ChargeCodeCategory

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


class AddEditChargeCodeCategoryDialog(QDialog):
    def __init__(
        self,
        parent,
        controller: ChargeCodeController,
        current_user_id: str,
        category_to_edit: Optional[ChargeCodeCategory] = None,
        parent_category: Optional[
            ChargeCodeCategory
        ] = None,  # For adding a new Level 2 Process
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent
        self.controller = controller
        self.current_user_id = current_user_id
        self.category_to_edit = category_to_edit
        self.parent_category = (
            parent_category  # Will be None if adding/editing a Level 1 Category
        )

        self.is_edit_mode = self.category_to_edit is not None

        # Determine level
        if self.is_edit_mode:
            self.current_level = self.category_to_edit.level
            self.current_parent_id = self.category_to_edit.parent_id
            if (
                self.current_parent_id and not self.parent_category
            ):  # Fetch parent if editing L2 and not passed
                self.parent_category = self.controller.get_category_by_id_internal(
                    self.current_parent_id
                )

        elif self.parent_category:  # Adding a new Level 2 Process
            self.current_level = 2
            self.current_parent_id = self.parent_category.category_id
        else:  # Adding a new Level 1 Category
            self.current_level = 1
            self.current_parent_id = None

        self.item_type_name = "Process" if self.current_level == 2 else "Category"

        self.setWindowTitle(
            f"{'Edit' if self.is_edit_mode else 'Add New'} {self.item_type_name}"
        )
        self.setMinimumWidth(450)

        # Input Fields
        self.name_input: Optional[QLineEdit] = None
        self.parent_name_label: Optional[QLabel] = None  # To display parent name
        self.level_label: Optional[QLabel] = None  # To display level
        self.is_active_checkbox: Optional[QCheckBox] = None

        self._setup_palette()
        self._setup_ui()

        if self.is_edit_mode and self.category_to_edit:
            self._populate_fields()
        else:  # New item
            self.is_active_checkbox.setChecked(True)

    def _get_form_input_style(self, base_bg=DARK_INPUT_FIELD_BACKGROUND) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background-color: {base_bg};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 6px 10px; font-size: 13px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled {{ 
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QCheckBox::indicator {{ width: 13px; height: 13px; }}
            QCheckBox {{ color: {DARK_TEXT_PRIMARY}; background-color: transparent; }}
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
        # ... (rest of palette setup - can be copied from another dialog) ...
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

    def _create_label(self, text: str, is_field_value: bool = False) -> QLabel:
        label = QLabel(text)
        style = f"color: {DARK_TEXT_PRIMARY if is_field_value else DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; font-size: 13px;"
        if is_field_value:
            style += f" padding-left: 5px; border: 1px solid {DARK_BORDER}; border-radius: 4px; background-color: {DARK_HEADER_FOOTER}; min-height: 20px;"

        label.setStyleSheet(style)
        font_size = (
            AppConfig.DEFAULT_FONT_SIZE
            if hasattr(AppConfig, "DEFAULT_FONT_SIZE")
            else 10
        )
        label.setFont(QFont(DEFAULT_FONT_FAMILY, font_size))
        return label

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"Enter {self.item_type_name} Name")

        # Display Parent Category Name (if applicable)
        parent_display_name = (
            self.parent_category.name if self.parent_category else "N/A (Top Level)"
        )
        self.parent_name_label = self._create_label(
            parent_display_name, is_field_value=True
        )

        # Display Level
        self.level_label = self._create_label(
            str(self.current_level), is_field_value=True
        )

        self.is_active_checkbox = QCheckBox("Is Active")

        form_layout.addRow(
            self._create_label(f"{self.item_type_name} Name*:"), self.name_input
        )
        if self.current_level == 2:  # Only show parent for Processes (Level 2)
            form_layout.addRow(
                self._create_label("Parent Category:"), self.parent_name_label
            )
        form_layout.addRow(self._create_label("Level:"), self.level_label)
        form_layout.addRow(self._create_label("Status:"), self.is_active_checkbox)

        input_style = self._get_form_input_style()
        self.name_input.setStyleSheet(input_style)
        self.is_active_checkbox.setStyleSheet(input_style)  # For QCheckBox part

        layout.addLayout(form_layout)
        layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        generic_button_style = self._get_dialog_generic_button_style()
        for button in self.button_box.buttons():
            button.setStyleSheet(generic_button_style)
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ background-color: {DARK_SUCCESS_ACTION}; color: white; }}"
                )
        layout.addWidget(self.button_box)

    def _populate_fields(self):
        if self.category_to_edit:
            self.name_input.setText(self.category_to_edit.name)
            self.is_active_checkbox.setChecked(self.category_to_edit.is_active)
            # Parent and Level are already set in __init__ and displayed by labels

    def get_data(self) -> Optional[Dict[str, Any]]:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Input Error", f"{self.item_type_name} Name is required."
            )
            return None

        return {
            "name": name,
            "is_active": self.is_active_checkbox.isChecked(),
            "level": self.current_level,
            "parent_id": self.current_parent_id,
        }

    def validate_and_accept(self):
        data = self.get_data()
        if data is None:
            return

        # Use the controller's validation method
        is_valid, errors = self.controller.validate_charge_code_category_data(
            data,
            is_new=(not self.is_edit_mode),
            category_id=(
                self.category_to_edit.category_id if self.is_edit_mode else None
            ),
        )

        if not is_valid:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please correct errors:\n- " + "\n- ".join(errors),
            )
            return

        try:
            if self.is_edit_mode and self.category_to_edit:
                success, message = self.controller.update_charge_code_category(
                    self.category_to_edit.category_id, data, self.current_user_id
                )
            else:
                success, message, _ = self.controller.create_charge_code_category(
                    data, self.current_user_id
                )

            if success:
                if hasattr(
                    self.parent_view, "show_info"
                ):  # Check if parent_view has show_info
                    self.parent_view.show_info("Success", message)
                else:
                    QMessageBox.information(self, "Success", message)
                super().accept()
            else:
                QMessageBox.critical(
                    self, "Error", message or "An unknown error occurred."
                )
        except Exception as e:
            self.logger.error(f"Error saving category/process: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Operation Failed", f"An unexpected error occurred: {str(e)}"
            )
