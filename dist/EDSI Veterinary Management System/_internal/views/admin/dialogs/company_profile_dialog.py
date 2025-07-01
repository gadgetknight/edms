# views/admin/dialogs/company_profile_dialog.py
"""
EDSI Veterinary Management System - Company Profile Dialog
Version: 1.0.2
Purpose: Dialog for editing the main company profile information.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v1.0.2 (2025-06-28):
    - Added `use_stripe_payments` QCheckBox to the UI for toggling Stripe integration.
    - Updated `_load_profile` to populate the checkbox state.
    - Modified `_save_profile` to include the checkbox's state in the data sent to the controller.
- v1.0.1 (2025-06-09):
    - Bug Fix: Added QHBoxLayout to the PySide6.QtWidgets import list to resolve
      a NameError during UI setup.
- v1.0.0 (2025-06-08):
    - Initial creation of the dialog.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QFileDialog,
    QCheckBox,  # Added for use_stripe_payments
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from controllers.company_profile_controller import CompanyProfileController
from config.app_config import AppConfig


class CompanyProfileDialog(QDialog):
    def __init__(self, parent, current_user_id: str):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = current_user_id
        self.controller = CompanyProfileController()

        self.setWindowTitle("Manage Company Profile")
        self.setMinimumWidth(600)

        self._setup_ui()
        self._apply_styles()
        self._setup_connections()
        self._load_profile()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.company_name_input = QLineEdit()
        self.address1_input = QLineEdit()
        self.address2_input = QLineEdit()
        self.city_input = QLineEdit()
        self.state_input = QLineEdit()
        self.zip_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.website_input = QLineEdit()
        self.logo_path_input = QLineEdit()
        self.browse_logo_btn = QPushButton("Browse...")

        # NEW: Stripe Payments Toggle
        self.use_stripe_payments_checkbox = QCheckBox("Enable Stripe Payment Links")
        self.use_stripe_payments_checkbox.setChecked(False)  # Default to false
        self.use_stripe_payments_checkbox.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_PRIMARY};"  # Style to match other checkboxes
        )

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logo_path_input)
        logo_layout.addWidget(self.browse_logo_btn)

        form_layout.addRow("Company Name*:", self.company_name_input)
        form_layout.addRow("Address 1:", self.address1_input)
        form_layout.addRow("Address 2:", self.address2_input)
        form_layout.addRow("City:", self.city_input)
        form_layout.addRow("State:", self.state_input)
        form_layout.addRow("Zip Code:", self.zip_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Website:", self.website_input)
        form_layout.addRow("Logo Path:", logo_layout)
        form_layout.addRow(
            "", self.use_stripe_payments_checkbox
        )  # Add the new checkbox

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

    def _apply_styles(self):
        field_style = f"""
            QLineEdit, QTextEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {AppConfig.DARK_PRIMARY_ACTION};
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 3px;
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND};
            }}
            QCheckBox::indicator:checked {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                border-color: {AppConfig.DARK_SUCCESS_ACTION};
            }}
        """
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(field_style)
        for widget in self.findChildren(QTextEdit):
            widget.setStyleSheet(field_style)

        # Style the browse button separately if needed, or rely on global QPushButton styles
        self.browse_logo_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.DARK_BUTTON_HOVER};
            }}
        """
        )

        # Style dialog buttons
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        save_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_SUCCESS_ACTION};
                color: white;
                border: 1px solid {QColor(AppConfig.DARK_SUCCESS_ACTION).darker(120).name()};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        cancel_button_style = f"""
            QPushButton {{
                background-color: {AppConfig.DARK_BUTTON_BG};
                color: {AppConfig.DARK_TEXT_PRIMARY};
                border: 1px solid {AppConfig.DARK_BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}
        """
        save_button.setStyleSheet(save_button_style)
        cancel_button.setStyleSheet(cancel_button_style)

    def _setup_connections(self):
        self.button_box.accepted.connect(self._save_profile)
        self.button_box.rejected.connect(self.reject)
        self.browse_logo_btn.clicked.connect(self._browse_for_logo)

    def _load_profile(self):
        profile = self.controller.get_company_profile()
        if profile:
            self.company_name_input.setText(profile.company_name or "")
            self.address1_input.setText(profile.address_line1 or "")
            self.address2_input.setText(profile.address_line2 or "")
            self.city_input.setText(profile.city or "")
            self.state_input.setText(profile.state or "")
            self.zip_input.setText(profile.zip_code or "")
            self.phone_input.setText(profile.phone or "")
            self.email_input.setText(profile.email or "")
            self.website_input.setText(profile.website or "")
            self.logo_path_input.setText(profile.logo_path or "")
            # NEW: Load checkbox state
            self.use_stripe_payments_checkbox.setChecked(profile.use_stripe_payments)

    def _browse_for_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.logo_path_input.setText(file_path)

    def _save_profile(self):
        if not self.company_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Company Name is required.")
            return

        data = {
            "company_name": self.company_name_input.text().strip(),
            "address_line1": self.address1_input.text().strip(),
            "address_line2": self.address2_input.text().strip(),
            "city": self.city_input.text().strip(),
            "state": self.state_input.text().strip(),
            "zip_code": self.zip_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "website": self.website_input.text().strip(),
            "logo_path": self.logo_path_input.text().strip(),
            "use_stripe_payments": self.use_stripe_payments_checkbox.isChecked(),  # NEW: Save checkbox state
        }

        success, message = self.controller.update_company_profile(
            data, self.current_user_id
        )
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
