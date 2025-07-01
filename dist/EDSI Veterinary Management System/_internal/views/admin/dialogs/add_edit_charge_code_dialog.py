# views/admin/dialogs/add_edit_charge_code_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Charge Code Dialog
Version: 1.1.12
Purpose: Dialog for creating and editing charge codes.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.1.12 (2025-06-09):
    - Bug Fix: In `validate_and_accept`, correctly pass the `charge_code_id_to_ignore`
      parameter to the validation method to allow saving of edited records.
- v1.1.11 (2025-06-05):
    - Bug Fix: Corrected dictionary key access for category path population.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QComboBox,
    QHBoxLayout,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt, QTimer, Slot

from controllers.charge_code_controller import ChargeCodeController
from models import ChargeCode as ChargeCodeModel
from models import ChargeCodeCategory

from config.app_config import AppConfig
import os

try:
    current_script_path_for_assets = os.path.dirname(os.path.abspath(__file__))
    project_root_for_assets = os.path.abspath(
        os.path.join(current_script_path_for_assets, "..", "..", "..")
    )
    assets_path = os.path.join(project_root_for_assets, "assets", "icons")
    if not os.path.exists(os.path.join(assets_path, "checkmark_light.svg")):
        assets_path = "assets/icons"
except Exception:
    assets_path = "assets/icons"


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


class AddEditChargeCodeDialog(QDialog):
    def __init__(
        self,
        parent,
        controller: ChargeCodeController,
        current_user_id: str,
        charge_code: Optional[ChargeCodeModel] = None,
    ):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent
        self.controller = controller
        self.current_user_id = current_user_id
        self.charge_code = charge_code
        self.is_edit_mode = charge_code is not None

        self.code_input: Optional[QLineEdit] = None
        self.alt_code_input: Optional[QLineEdit] = None
        self.description_input: Optional[QTextEdit] = None
        self.main_category_combo: Optional[QComboBox] = None
        self.sub_category_combo: Optional[QComboBox] = None
        self.standard_charge_input: Optional[QDoubleSpinBox] = None
        self.taxable_checkbox: Optional[QCheckBox] = None
        self.is_active_checkbox: Optional[QCheckBox] = None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Charge Code")
        self.setMinimumWidth(650)

        self._setup_palette()
        self._setup_ui()
        self._load_main_categories()

        if self.is_edit_mode and self.charge_code:
            self._populate_fields()
        else:
            if self.is_active_checkbox:
                self.is_active_checkbox.setChecked(True)
            if self.taxable_checkbox:
                self.taxable_checkbox.setChecked(False)
            if self.sub_category_combo:
                self.sub_category_combo.setEnabled(False)

        if self.is_active_checkbox:
            self.is_active_checkbox.setEnabled(False)
        if self.taxable_checkbox:
            self.taxable_checkbox.setEnabled(False)

    def _get_form_input_style(self, base_bg=DARK_INPUT_FIELD_BACKGROUND) -> str:
        checkmark_path = os.path.join(assets_path, "checkmark_light.svg").replace(
            os.sep, "/"
        )
        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{ background-color: {base_bg}; color: {DARK_TEXT_PRIMARY};
            border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 10px; font-size: 13px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled, QDoubleSpinBox:disabled {{ background-color: {DARK_HEADER_FOOTER};
            color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER};
            }}
            QLineEdit[readOnly="true"] {{ background-color: {DARK_HEADER_FOOTER};
            color: {DARK_TEXT_TERTIARY}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent;
            }}
            QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY};
            }}
            QComboBox QAbstractItemView {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
            border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_HIGHLIGHT_BG}; selection-color: {DARK_HIGHLIGHT_TEXT}; }}
            QCheckBox::indicator:disabled {{ background-color: {DARK_INPUT_FIELD_BACKGROUND};
            border: 1px solid {DARK_TEXT_TERTIARY}; }}
            QCheckBox::indicator:checked:disabled {{ background-color: {DARK_PRIMARY_ACTION};
            border: 1px solid {DARK_PRIMARY_ACTION}; image: url({checkmark_path}); }}
            QCheckBox:disabled {{ color: {DARK_TEXT_SECONDARY};
            }}
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

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background-color: transparent; padding-top: 3px; font-size: 13px;"
        )
        font_size = (
            AppConfig.DEFAULT_FONT_SIZE
            if hasattr(AppConfig, "DEFAULT_FONT_SIZE")
            else 10
        )
        label.setFont(QFont(DEFAULT_FONT_FAMILY, font_size))
        return label

    def _setup_ui(self):
        overall_layout = QVBoxLayout(self)
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(20, 20, 20, 15)
        grid_layout.setSpacing(10)
        grid_layout.setVerticalSpacing(15)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Unique code (e.g., EXAM01)")
        self.alt_code_input = QLineEdit()
        self.alt_code_input.setPlaceholderText("Alternative code (optional)")
        if self.alt_code_input:
            self.alt_code_input.textEdited.connect(self._on_alt_code_text_edited)

        self.main_category_combo = QComboBox()
        self.main_category_combo.setPlaceholderText("Select Main Category")
        self.sub_category_combo = QComboBox()
        self.sub_category_combo.setPlaceholderText("Select Sub-Category")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Detailed description")
        self.description_input.setFixedHeight(70)
        self.standard_charge_input = QDoubleSpinBox()
        self.standard_charge_input.setDecimals(2)
        self.standard_charge_input.setRange(0.00, 99999.99)
        self.standard_charge_input.setPrefix("$ ")
        self.standard_charge_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.taxable_checkbox = QCheckBox("Taxable")
        self.taxable_checkbox.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-size: 13px;"
        )
        self.is_active_checkbox = QCheckBox("Active")
        self.is_active_checkbox.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-size: 13px;"
        )

        row = 0
        grid_layout.addWidget(
            self._create_label("Code*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.code_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Alt. Code:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.alt_code_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Main Category*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.main_category_combo, row, 1, 1, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Sub-Category:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.sub_category_combo, row, 1, 1, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Standard Charge*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.standard_charge_input, row, 1)
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.taxable_checkbox)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.is_active_checkbox)
        status_layout.addStretch()
        grid_layout.addLayout(
            status_layout,
            row,
            2,
            1,
            2,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        row += 1
        grid_layout.addWidget(
            self._create_label("Description*:"),
            row,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        grid_layout.addWidget(self.description_input, row, 1, 1, 3)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        grid_layout.setColumnMinimumWidth(0, 110)
        grid_layout.setColumnMinimumWidth(2, 110)

        form_style = self._get_form_input_style()
        fields_to_style = [
            self.code_input,
            self.alt_code_input,
            self.description_input,
            self.main_category_combo,
            self.sub_category_combo,
            self.standard_charge_input,
        ]
        for field in fields_to_style:
            if field:
                field.setStyleSheet(form_style)

        overall_layout.addLayout(grid_layout)
        overall_layout.addStretch(1)
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
                ok_style = (
                    generic_button_style
                    + f"QPushButton {{ background-color: {DARK_SUCCESS_ACTION}; color: white; }}"
                )
                button.setStyleSheet(ok_style)
        overall_layout.addWidget(self.button_box)
        if self.main_category_combo:
            self.main_category_combo.currentIndexChanged.connect(
                self._on_main_category_changed
            )

    @Slot(str)
    def _on_alt_code_text_edited(self, text: str):
        if self.alt_code_input:
            current_text = text
            uppercase_text = current_text.upper()
            if current_text != uppercase_text:
                self.alt_code_input.blockSignals(True)
                cursor_pos = self.alt_code_input.cursorPosition()
                self.alt_code_input.setText(uppercase_text)
                self.alt_code_input.setCursorPosition(cursor_pos)
                self.alt_code_input.blockSignals(False)

    def _load_main_categories(self):
        if not self.main_category_combo:
            return
        self.main_category_combo.clear()
        self.main_category_combo.addItem("Select Main Category...", None)
        try:
            categories = self.controller.get_charge_code_categories(level=1)
            for cat in categories:
                self.main_category_combo.addItem(cat.name, cat.category_id)
        except Exception as e:
            self.logger.error(f"Error loading main categories: {e}", exc_info=True)

    def _on_main_category_changed(self, index: int):
        if not self.main_category_combo or not self.sub_category_combo:
            return
        self.sub_category_combo.clear()
        self.sub_category_combo.addItem("Select Sub-Category...", None)
        parent_id = self.main_category_combo.itemData(index)
        if parent_id is not None:
            try:
                sub_categories = self.controller.get_charge_code_categories(
                    parent_id=parent_id, level=2
                )
                if sub_categories:
                    for cat in sub_categories:
                        self.sub_category_combo.addItem(cat.name, cat.category_id)
                    self.sub_category_combo.setEnabled(True)
                else:
                    self.sub_category_combo.setEnabled(False)
            except Exception as e:
                self.logger.error(
                    f"Error loading sub-categories for parent_id {parent_id}: {e}",
                    exc_info=True,
                )
                self.sub_category_combo.setEnabled(False)
        else:
            self.sub_category_combo.setEnabled(False)

    def _populate_fields(self):
        if self.is_edit_mode and self.charge_code:
            self.code_input.setText(self.charge_code.code)
            self.code_input.setReadOnly(True)
            self.code_input.setStyleSheet(
                self._get_form_input_style()
                + f"QLineEdit {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
            )
            self.alt_code_input.setText(self.charge_code.alternate_code or "")
            self.description_input.setPlainText(self.charge_code.description)
            self.standard_charge_input.setValue(
                float(self.charge_code.standard_charge)
                if self.charge_code.standard_charge is not None
                else 0.0
            )
            if self.taxable_checkbox:
                self.taxable_checkbox.setChecked(self.charge_code.taxable or False)
            if self.is_active_checkbox:
                self.is_active_checkbox.setChecked(self.charge_code.is_active)
            if self.charge_code.category_id is not None:
                path = self.controller.get_category_path(self.charge_code.category_id)
                if path:
                    if self.main_category_combo:
                        self.main_category_combo.blockSignals(True)
                    if self.sub_category_combo:
                        self.sub_category_combo.blockSignals(True)
                    if len(path) > 0 and self.main_category_combo:
                        main_cat_id = path[0]["id"]
                        index = self.main_category_combo.findData(main_cat_id)
                        if index >= 0:
                            self.main_category_combo.setCurrentIndex(index)
                        self._on_main_category_changed(
                            self.main_category_combo.currentIndex()
                        )
                    if len(path) > 1 and self.sub_category_combo:
                        sub_cat_id = path[1]["id"]
                        QTimer.singleShot(
                            0,
                            lambda: self._select_combo_item(
                                self.sub_category_combo, sub_cat_id, False
                            ),
                        )
                    if self.main_category_combo:
                        self.main_category_combo.blockSignals(False)
                    if self.sub_category_combo:
                        self.sub_category_combo.blockSignals(False)
            else:
                if self.sub_category_combo:
                    self.sub_category_combo.setEnabled(False)

    def _select_combo_item(
        self, combo: QComboBox, item_id_to_select: int, trigger_next_load: bool
    ):
        if not combo:
            return
        index = combo.findData(item_id_to_select)
        if index >= 0:
            combo.setCurrentIndex(index)

    def get_data(self) -> Optional[Dict[str, Any]]:
        code = self.code_input.text().strip().upper()
        description = self.description_input.toPlainText().strip()
        standard_charge_value = self.standard_charge_input.value()
        errors = []
        if not code:
            errors.append("Code is required.")
        if not description:
            errors.append("Description is required.")
        charge_decimal: Optional[Decimal] = None
        try:
            charge_decimal = Decimal(str(standard_charge_value))
            if charge_decimal < Decimal("0.00"):
                errors.append("Standard Charge cannot be negative.")
        except InvalidOperation:
            errors.append("Standard Charge must be a valid number (e.g., 25.00).")
        selected_category_id: Optional[int] = None
        if (
            self.sub_category_combo
            and self.sub_category_combo.currentIndex() > 0
            and self.sub_category_combo.isEnabled()
        ):
            selected_category_id = self.sub_category_combo.currentData()
        elif self.main_category_combo and self.main_category_combo.currentIndex() > 0:
            selected_category_id = self.main_category_combo.currentData()
        if selected_category_id is None:
            errors.append(
                "A category selection (Main Category, or Sub-Category if applicable) is required."
            )
        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return None
        return {
            "code": code,
            "alternate_code": self.alt_code_input.text().strip().upper() or None,
            "description": description,
            "category_id": selected_category_id,
            "standard_charge": charge_decimal,
        }

    def validate_and_accept(self):
        data = self.get_data()
        if data is None:
            return

        charge_code_id_to_ignore = (
            self.charge_code.id if self.is_edit_mode and self.charge_code else None
        )

        is_valid, errors = self.controller.validate_charge_code_data(
            data,
            is_new=(not self.is_edit_mode),
            charge_code_id_to_ignore=charge_code_id_to_ignore,
        )
        if not is_valid:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct the following errors:\n- " + "\n- ".join(errors),
            )
            return

        try:
            if self.is_edit_mode and self.charge_code:
                success, message = self.controller.update_charge_code(
                    self.charge_code.id, data, self.current_user_id
                )
            else:
                success, message, _ = self.controller.create_charge_code(
                    data, self.current_user_id
                )

            if success:
                if hasattr(self.parent_view, "show_info") and callable(
                    getattr(self.parent_view, "show_info")
                ):
                    self.parent_view.show_info("Success", message)
                else:
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
