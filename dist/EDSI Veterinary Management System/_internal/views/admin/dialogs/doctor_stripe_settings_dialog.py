# views/admin/dialogs/doctor_stripe_settings_dialog.py

"""
EDMS Veterinary Management System - Doctor Stripe Settings Dialog
Version: 1.0.0
Purpose: Dialog for configuring the doctor's (end-user's) Stripe API keys
         (Publishable and Secret) for payment processing.
Last Updated: June 25, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-06-25):
    - Initial creation of the dialog for managing doctor's Stripe API keys.
    - Includes input fields for Publishable Key and Secret Key.
    - Loads/saves keys to/from AppConfig (for demonstration/temporary persistence).
    - Features input masking for Secret Key and a "Show/Hide" button.
    - Provides basic validation for key format.
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
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtCore import Qt, QSize

from config.app_config import AppConfig

# Assume standard AppConfig colors are available
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
    DEFAULT_FONT_FAMILY,
)


class DoctorStripeSettingsDialog(QDialog):
    def __init__(self, parent_view, current_user_id: str):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view
        self.current_user_id = current_user_id

        self.setWindowTitle("Doctor Stripe Settings")
        self.setMinimumWidth(550)

        self.publishable_key_input: QLineEdit
        self.secret_key_input: QLineEdit
        self.show_hide_secret_btn: QPushButton

        self._setup_palette()
        self._setup_ui()
        self._apply_styles()
        self._setup_connections()
        self._load_settings()

    def _get_input_field_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 22px;
            }}
            QLineEdit:focus {{
                border-color: {DARK_PRIMARY_ACTION};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {DARK_HEADER_FOOTER};
                color: {DARK_TEXT_SECONDARY};
            }}
        """

    def _get_button_style(self, btn_type: str = "standard") -> str:
        base_style = (
            f"QPushButton {{background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )
        if btn_type == "save":
            return (
                f"{base_style} QPushButton {{ background-color: {DARK_SUCCESS_ACTION}; "
                f"color: white; border-color: {DARK_SUCCESS_ACTION}; }}"
                f"QPushButton:hover {{ background-color: {QColor(DARK_SUCCESS_ACTION).lighter(115).name()}; }}"
            )
        return base_style

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
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setContentsMargins(20, 20, 20, 15)
        form_layout.setSpacing(10)

        info_label = QLabel(
            "Enter your Stripe API keys. These keys allow the system to process payments "
            "through your Stripe account. **Your Secret Key should be kept confidential.**"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {DARK_TEXT_SECONDARY}; margin-bottom: 10px;")
        main_layout.addWidget(info_label)

        self.publishable_key_input = QLineEdit()
        self.publishable_key_input.setPlaceholderText("pk_test_...")

        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_input.setPlaceholderText("sk_test_...")

        self.show_hide_secret_btn = QPushButton()
        self.show_hide_secret_btn.setIcon(
            QIcon.fromTheme("visibility_off", QIcon(":/icons/visibility_off.png"))
        )  # Placeholder icon
        self.show_hide_secret_btn.setIconSize(QSize(20, 20))
        self.show_hide_secret_btn.setFixedSize(30, 26)  # Make it fit nicely
        self.show_hide_secret_btn.setCheckable(True)  # Toggle for show/hide
        self.show_hide_secret_btn.setStyleSheet(
            f"QPushButton {{ border: none; background-color: transparent; }}"
        )

        secret_key_layout = QHBoxLayout()
        secret_key_layout.addWidget(self.secret_key_input)
        secret_key_layout.addWidget(self.show_hide_secret_btn)

        form_layout.addRow("Publishable Key:", self.publishable_key_input)
        form_layout.addRow("Secret Key:", secret_key_layout)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._save_settings)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

    def _apply_styles(self):
        input_style = self._get_input_field_style()
        self.publishable_key_input.setStyleSheet(input_style)
        self.secret_key_input.setStyleSheet(input_style)

        save_btn = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setStyleSheet(self._get_button_style("save"))
        cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setStyleSheet(self._get_button_style("standard"))

        # You'll need icons. For demonstration, using text or simple icons:
        # If you have an 'icons' directory with 'visibility_on.png' and 'visibility_off.png'
        # you could use QIcon(':/icons/visibility_on.png')
        self.show_hide_secret_btn.setText("👁️")  # Placeholder text if no icons

    def _setup_connections(self):
        self.show_hide_secret_btn.toggled.connect(self._toggle_secret_visibility)

    def _load_settings(self):
        self.publishable_key_input.setText(AppConfig.DOCTOR_STRIPE_PUBLISHABLE_KEY)
        self.secret_key_input.setText(AppConfig.DOCTOR_STRIPE_SECRET_KEY)

    def _toggle_secret_visibility(self, checked: bool):
        if checked:  # Show
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_hide_secret_btn.setText("🙈")
        else:  # Hide
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_hide_secret_btn.setText("👁️")

    def _save_settings(self):
        pub_key = self.publishable_key_input.text().strip()
        sec_key = self.secret_key_input.text().strip()

        if not pub_key.startswith("pk_") or len(pub_key) < 20:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Invalid Publishable Key format. Must start with 'pk_' and be long enough.",
            )
            return
        if not sec_key.startswith("sk_") or len(sec_key) < 20:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Invalid Secret Key format. Must start with 'sk_' and be long enough.",
            )
            return

        # For this demonstration, we update the module-level constants.
        # In a real app, you would persist these to a database (e.g., in a User table).
        AppConfig.DOCTOR_STRIPE_PUBLISHABLE_KEY = pub_key
        AppConfig.DOCTOR_STRIPE_SECRET_KEY = sec_key

        self.parent_view.show_info(
            "Settings Saved",
            "Stripe API keys saved. Changes will take full effect after application restart.",
        )
        self.accept()
