# views/admin/dialogs/add_edit_charge_code_dialog.py

"""
EDSI Veterinary Management System - Add/Edit Charge Code Dialog
Version: 1.1.3
Purpose: Dialog for creating and editing charge codes.
         Resolves circular import and adds missing Optional/Dict import.
Last Updated: May 19, 2025
Author: Claude Assistant

Changelog:
- v1.1.3 (2025-05-19):
    - Added `from typing import Optional, Dict` to resolve NameError for 'Optional'.
- v1.1.2 (2025-05-19):
    - Resolved circular import with UserManagementScreen by removing the import
      and defining necessary style helper methods locally within this dialog.
- v1.1.1 (2025-05-19):
    - Corrected AppConfig constant usage. Imported constants directly instead of
      accessing them via the AppConfig class for palette and button styling.
- v1.1.0 (2025-05-18):
    - Initial version based on artifact and integrated into UserManagementScreen.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict  # ADDED Optional and Dict here

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.charge_code_controller import ChargeCodeController
from models import ChargeCode as ChargeCodeModel

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


class AddEditChargeCodeDialog(QDialog):
    def __init__(
        self,
        parent,
        controller: ChargeCodeController,
        charge_code: Optional[ChargeCodeModel] = None,
    ):  # Optional is now defined
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.controller = controller
        self.charge_code = charge_code
        self.is_edit_mode = charge_code is not None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Charge Code")
        self.setMinimumWidth(450)

        self._setup_palette()
        self._setup_ui()
        self._populate_fields()

    def _get_dialog_specific_input_field_style(self):
        """Generates style string for input fields within this dialog."""
        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QComboBox::drop-down {{
                border: none; background-color: transparent;
                subcontrol-position: right center; width: 15px;
            }}
            QComboBox::down-arrow {{ image: url(none); }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }}
        """

    def _get_dialog_generic_button_style(self):
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

        self.code_input = QLineEdit()
        self.code_input.setStyleSheet(input_style)
        self.code_input.setPlaceholderText("Unique code (e.g., EXAM01)")
        form_layout.addRow("Code*:", self.code_input)

        self.alt_code_input = QLineEdit()
        self.alt_code_input.setStyleSheet(input_style)
        self.alt_code_input.setPlaceholderText("Alternative code (optional)")
        form_layout.addRow("Alt. Code:", self.alt_code_input)

        self.description_input = QTextEdit()
        self.description_input.setStyleSheet(input_style)
        self.description_input.setPlaceholderText(
            "Detailed description of the charge code"
        )
        self.description_input.setFixedHeight(80)
        form_layout.addRow("Description*:", self.description_input)

        self.category_input = QLineEdit()
        self.category_input.setStyleSheet(input_style)
        self.category_input.setPlaceholderText("e.g., Veterinary, Pharmacy, Boarding")
        form_layout.addRow("Category:", self.category_input)

        self.standard_charge_input = QDoubleSpinBox()
        self.standard_charge_input.setStyleSheet(input_style)
        self.standard_charge_input.setDecimals(2)
        self.standard_charge_input.setRange(0.00, 999999.99)
        self.standard_charge_input.setPrefix("$ ")
        form_layout.addRow("Standard Charge*:", self.standard_charge_input)

        self.is_active_checkbox = QCheckBox("Charge Code is Active")
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
        if self.is_edit_mode and self.charge_code:
            self.code_input.setText(self.charge_code.code)
            self.alt_code_input.setText(self.charge_code.alternate_code or "")
            self.description_input.setPlainText(self.charge_code.description)
            self.category_input.setText(self.charge_code.category or "")
            self.standard_charge_input.setValue(
                float(self.charge_code.standard_charge)
                if self.charge_code.standard_charge is not None
                else 0.0
            )
            self.is_active_checkbox.setChecked(self.charge_code.is_active)
        elif not self.is_edit_mode:
            self.is_active_checkbox.setChecked(True)

    def get_data(self) -> Optional[Dict]:  # Dict is now defined
        code = self.code_input.text().strip().upper()
        description = self.description_input.toPlainText().strip()
        standard_charge_value = self.standard_charge_input.value()

        errors = []
        if not code:
            errors.append("Code is required.")
        if not description:
            errors.append("Description is required.")

        charge_decimal = None
        try:
            charge_decimal = Decimal(str(standard_charge_value))
            if charge_decimal < Decimal("0.00"):
                errors.append("Standard Charge cannot be negative.")
        except InvalidOperation:
            errors.append("Standard Charge must be a valid number.")

        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return None

        return {
            "code": code,
            "alternate_code": self.alt_code_input.text().strip().upper() or None,
            "description": description,
            "category": self.category_input.text().strip() or None,
            "standard_charge": charge_decimal,
            "is_active": self.is_active_checkbox.isChecked(),
        }

    def validate_and_accept(self):
        data = self.get_data()
        if data is None:
            return

        try:
            if self.is_edit_mode and self.charge_code:
                success, message = self.controller.update_charge_code(
                    self.charge_code.charge_code_id, data
                )
            else:
                success, message, _ = self.controller.create_charge_code(data)

            if success:
                QMessageBox.information(self, "Success", message)
                super().accept()
            else:
                QMessageBox.critical(
                    self, "Error", message or "An unknown error occurred."
                )
        except Exception as e:
            self.logger.error(
                f"Error during charge code save/update: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Operation Failed", f"An unexpected error occurred: {e}"
            )
