# views/admin/dialogs/add_edit_owner_dialog.py
"""
EDSI Veterinary Management System - Add/Edit Owner Dialog
Version: 1.1.0
Purpose: Dialog for creating and editing Owner master file records,
         including contact, address, and financial information.
         Styled to match HorseUnifiedManagement forms, using QGridLayout.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-09):
    - Fixed validation logic to correctly ignore the current record's own
      account number when checking for duplicates in edit mode.
    - Updated the main action button text to display "Save Owner" in edit mode
      and "Create Owner" in add mode for better clarity.
- v1.0.0 (2025-06-02):
    - Initial implementation.
    - Includes fields for account info, name, address (with state dropdown
      and auto-populated, read-only country), contact details, and financial info
      (Balance (display-only), Credit Limit, Billing Terms dropdown).
    - Uses QGridLayout for layout.
    - Styled using _get_form_input_style (adapted from HorseUnifiedManagement)
      and _create_label helper.
    - Populates states from OwnerController and billing terms from a predefined list.
    - Implements _on_state_changed to auto-populate country code.
    - Implements _populate_fields, get_data, and validate_and_accept methods.
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt

from controllers.owner_controller import OwnerController
from models import Owner as OwnerModel

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

PREDEFINED_BILLING_TERMS = [
    "Net 30 Days",
    "Net 60 Days",
    "Net 90 Days",
    "Due on Receipt",
    "COD",
    "Prepay",
    "Monthly Statement",
]


class AddEditOwnerDialog(QDialog):
    def __init__(
        self,
        parent_view,
        owner_controller: OwnerController,
        current_user_id: str,
        owner_object: Optional[OwnerModel] = None,
    ):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.owner_controller = owner_controller
        self.current_user_id = current_user_id
        self.owner = owner_object
        self.is_edit_mode = owner_object is not None

        self.account_number_input: Optional[QLineEdit] = None
        self.farm_name_input: Optional[QLineEdit] = None
        self.first_name_input: Optional[QLineEdit] = None
        self.last_name_input: Optional[QLineEdit] = None
        self.address_line1_input: Optional[QLineEdit] = None
        self.address_line2_input: Optional[QLineEdit] = None
        self.city_input: Optional[QLineEdit] = None
        self.state_combo: Optional[QComboBox] = None
        self.zip_code_input: Optional[QLineEdit] = None
        self.country_code_input: Optional[QLineEdit] = None
        self.phone_input: Optional[QLineEdit] = None
        self.mobile_phone_input: Optional[QLineEdit] = None
        self.email_input: Optional[QLineEdit] = None
        self.balance_display_input: Optional[QLineEdit] = None
        self.credit_limit_input: Optional[QDoubleSpinBox] = None
        self.billing_terms_combo: Optional[QComboBox] = None
        self.is_active_checkbox: Optional[QCheckBox] = None

        self.setWindowTitle(f"{'Edit' if self.is_edit_mode else 'Add'} Owner")
        self.setMinimumWidth(700)

        self._setup_palette()
        self._setup_ui()
        self._load_reference_data_into_combos()
        if self.is_edit_mode and self.owner:
            self._populate_fields()

    def _get_form_input_style(self, base_bg=DARK_INPUT_FIELD_BACKGROUND) -> str:
        return f"""
            QLineEdit, QComboBox, QDoubleSpinBox {{
                background-color: {base_bg}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 6px 10px; font-size: 13px; min-height: 20px; 
            }}
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled {{ 
                background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY};
                border-color: {DARK_HEADER_FOOTER};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_TERTIARY};
            }}
            QComboBox::drop-down {{ border: none; background-color: transparent; }}
            QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY}; }}
            QComboBox QAbstractItemView {{ 
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
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

        self.account_number_input = QLineEdit()
        self.account_number_input.setPlaceholderText("e.g., SMIJ01")
        self.farm_name_input = QLineEdit()
        self.farm_name_input.setPlaceholderText("Optional")
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Contact's First Name")
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Contact's Last Name")
        self.address_line1_input = QLineEdit()
        self.address_line1_input.setPlaceholderText("Street address, P.O. box")
        self.address_line2_input = QLineEdit()
        self.address_line2_input.setPlaceholderText("Apt, suite, etc. (Optional)")
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City/Town")
        self.state_combo = QComboBox()
        self.state_combo.setPlaceholderText("Select State/Province")
        self.zip_code_input = QLineEdit()
        self.zip_code_input.setPlaceholderText("Zip/Postal Code")
        self.country_code_input = QLineEdit()
        self.country_code_input.setPlaceholderText("Auto (e.g. USA, CAN)")
        self.country_code_input.setReadOnly(True)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(xxx) xxx-xxxx")
        self.mobile_phone_input = QLineEdit()
        self.mobile_phone_input.setPlaceholderText("Optional")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@domain.com")
        self.balance_display_input = QLineEdit("0.00")
        self.balance_display_input.setReadOnly(True)
        self.balance_display_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setRange(0.00, 9999999.99)
        self.credit_limit_input.setPrefix("$ ")
        self.credit_limit_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.credit_limit_input.setValue(0.00)
        self.billing_terms_combo = QComboBox()
        self.is_active_checkbox = QCheckBox("Owner is Active")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-size: 13px;"
        )

        row = 0
        grid_layout.addWidget(
            self._create_label("Account #:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.account_number_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Farm Name:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.farm_name_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("First Name:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.first_name_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Last Name:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.last_name_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Address Line 1*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.address_line1_input, row, 1, 1, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Address Line 2:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.address_line2_input, row, 1, 1, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("City*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.city_input, row, 1)
        grid_layout.addWidget(
            self._create_label("State/Province*:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.state_combo, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Zip/Postal Code*:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.zip_code_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Country Code:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.country_code_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Phone:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.phone_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Mobile Phone:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.mobile_phone_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Email:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.email_input, row, 1, 1, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Balance:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.balance_display_input, row, 1)
        grid_layout.addWidget(
            self._create_label("Credit Limit:"), row, 2, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.credit_limit_input, row, 3)
        row += 1
        grid_layout.addWidget(
            self._create_label("Billing Terms:"), row, 0, Qt.AlignmentFlag.AlignRight
        )
        grid_layout.addWidget(self.billing_terms_combo, row, 1)
        grid_layout.addWidget(
            self.is_active_checkbox, row, 3, Qt.AlignmentFlag.AlignLeft
        )

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        grid_layout.setColumnMinimumWidth(0, 120)
        grid_layout.setColumnMinimumWidth(2, 120)

        form_style = self._get_form_input_style()
        all_fields = [
            self.account_number_input,
            self.farm_name_input,
            self.first_name_input,
            self.last_name_input,
            self.address_line1_input,
            self.address_line2_input,
            self.city_input,
            self.state_combo,
            self.zip_code_input,
            self.country_code_input,
            self.phone_input,
            self.mobile_phone_input,
            self.email_input,
            self.balance_display_input,
            self.credit_limit_input,
            self.billing_terms_combo,
        ]
        for field in all_fields:
            if field:
                field.setStyleSheet(form_style)

        read_only_style_addon = f"QLineEdit {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        if self.balance_display_input:
            self.balance_display_input.setStyleSheet(form_style + read_only_style_addon)
        if self.country_code_input:
            self.country_code_input.setStyleSheet(form_style + read_only_style_addon)

        overall_layout.addLayout(grid_layout)
        overall_layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Save Owner" if self.is_edit_mode else "Create Owner")

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
                ok_button_specific_style = (
                    f"background-color: {DARK_SUCCESS_ACTION}; color: white;"
                )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ {ok_button_specific_style} }}"
                )
        overall_layout.addWidget(self.button_box)

        self.state_combo.currentIndexChanged.connect(self._on_state_changed)

    def _load_reference_data_into_combos(self):
        if not self.state_combo:
            self.logger.error("State combo not initialized.")
            return
        self.state_combo.addItem("", None)
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states = ref_data.get("states", [])
            for state_data in states:
                display_name = f"{state_data['name']} ({state_data['id']})"
                country_code = state_data.get("country_code", "USA")
                if country_code.upper() != "USA":
                    display_name += f" - {country_code}"
                self.state_combo.addItem(
                    display_name,
                    {"state_code": state_data["id"], "country_code": country_code},
                )
            self.logger.info(f"Loaded {len(states)} states into combobox.")
        except Exception as e:
            self.logger.error(
                f"Error loading states from controller: {e}", exc_info=True
            )
            QMessageBox.warning(
                self, "Data Load Error", "Could not load states for selection."
            )

        if not self.billing_terms_combo:
            self.logger.error("Billing terms combo not initialized.")
            return
        self.billing_terms_combo.addItem("", "")
        self.billing_terms_combo.addItems(PREDEFINED_BILLING_TERMS)
        self.billing_terms_combo.setCurrentIndex(0)
        self.logger.info(f"Loaded {len(PREDEFINED_BILLING_TERMS)} billing terms.")

    def _on_state_changed(self, index: int):
        if not self.state_combo or not self.country_code_input:
            return
        selected_data = self.state_combo.itemData(index)
        if selected_data and isinstance(selected_data, dict):
            country_code = selected_data.get("country_code", "")
            self.country_code_input.setText(country_code)
        else:
            self.country_code_input.clear()

    def _populate_fields(self):
        if self.owner:
            self.account_number_input.setText(self.owner.account_number or "")
            if self.is_edit_mode:
                self.account_number_input.setReadOnly(True)
                self.account_number_input.setStyleSheet(
                    self._get_form_input_style()
                    + f"QLineEdit {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
                )

            self.farm_name_input.setText(self.owner.farm_name or "")
            self.first_name_input.setText(self.owner.first_name or "")
            self.last_name_input.setText(self.owner.last_name or "")
            self.address_line1_input.setText(self.owner.address_line1 or "")
            self.address_line2_input.setText(self.owner.address_line2 or "")
            self.city_input.setText(self.owner.city or "")

            current_state_code = self.owner.state_code
            if current_state_code:
                for i in range(self.state_combo.count()):
                    item_data = self.state_combo.itemData(i)
                    if (
                        item_data
                        and isinstance(item_data, dict)
                        and item_data.get("state_code") == current_state_code
                    ):
                        self.state_combo.setCurrentIndex(i)
                        break
            else:
                self.state_combo.setCurrentIndex(0)
                self.country_code_input.clear()

            self.zip_code_input.setText(self.owner.zip_code or "")

            self.phone_input.setText(self.owner.phone or "")
            self.mobile_phone_input.setText(self.owner.mobile_phone or "")
            self.email_input.setText(self.owner.email or "")

            self.balance_display_input.setText(
                f"{self.owner.balance:.2f}"
                if self.owner.balance is not None
                else "0.00"
            )
            self.credit_limit_input.setValue(
                float(self.owner.credit_limit)
                if self.owner.credit_limit is not None
                else 0.00
            )

            if self.owner.billing_terms:
                index = self.billing_terms_combo.findText(
                    self.owner.billing_terms, Qt.MatchFlag.MatchExactly
                )
                if index >= 0:
                    self.billing_terms_combo.setCurrentIndex(index)
                else:
                    self.billing_terms_combo.addItem(self.owner.billing_terms)
                    self.billing_terms_combo.setCurrentText(self.owner.billing_terms)
            else:
                if self.billing_terms_combo.count() > 0:
                    self.billing_terms_combo.setCurrentIndex(0)

            self.is_active_checkbox.setChecked(self.owner.is_active)

    def get_data(self) -> Optional[Dict[str, Any]]:
        selected_state_item_data = self.state_combo.currentData()
        selected_state_code = None
        if selected_state_item_data and isinstance(selected_state_item_data, dict):
            selected_state_code = selected_state_item_data.get("state_code")

        credit_limit_val = self.credit_limit_input.value()
        credit_limit_decimal: Optional[Decimal] = None
        try:
            credit_limit_decimal = Decimal(str(credit_limit_val))
        except InvalidOperation:
            self.logger.warning(
                f"Invalid decimal value for credit limit: {credit_limit_val}, treating as None."
            )

        data = {
            "account_number": self.account_number_input.text().strip() or None,
            "farm_name": self.farm_name_input.text().strip() or None,
            "first_name": self.first_name_input.text().strip() or None,
            "last_name": self.last_name_input.text().strip() or None,
            "address_line1": self.address_line1_input.text().strip() or None,
            "address_line2": self.address_line2_input.text().strip() or None,
            "city": self.city_input.text().strip() or None,
            "state_code": selected_state_code,
            "zip_code": self.zip_code_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "mobile_phone": self.mobile_phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "credit_limit": credit_limit_decimal,
            "billing_terms": (
                self.billing_terms_combo.currentText()
                if self.billing_terms_combo.currentIndex() > 0
                else None
            ),
            "is_active": self.is_active_checkbox.isChecked(),
        }
        return data

    def validate_and_accept(self):
        owner_data = self.get_data()
        if owner_data is None:
            return

        owner_id_to_ignore = (
            self.owner.owner_id if self.is_edit_mode and self.owner else None
        )

        is_valid, errors = self.owner_controller.validate_owner_data(
            owner_data,
            is_new=(not self.is_edit_mode),
            owner_id_to_ignore=owner_id_to_ignore,
        )
        if not is_valid:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct the following errors:\n- " + "\n- ".join(errors),
            )
            return

        try:
            if self.is_edit_mode and self.owner:
                success, message = self.owner_controller.update_master_owner(
                    self.owner.owner_id, owner_data, self.current_user_id
                )
            else:
                success, message, _ = self.owner_controller.create_master_owner(
                    owner_data, self.current_user_id
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
            self.logger.error(f"Error during owner save/update: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Operation Failed", f"An unexpected error occurred: {e}"
            )
