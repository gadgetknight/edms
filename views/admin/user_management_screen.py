# views/admin/user_management_screen.py

"""
EDSI Veterinary Management System - User Management Screen (Tabbed Interface)
Version: 1.10.1
Purpose: Provides a tabbed interface for managing system settings.
         Uses centralized AppConfig for dark theme colors.
         Ensures input fields in AddMasterOwnerDialog are visually distinct.
Last Updated: May 16, 2025
Author: Claude Assistant

Changelog:
- v1.10.1 (2025-05-16):
  - Updated to use centralized dark theme colors from AppConfig.
  - Removed local dark theme color constant definitions.
  - Applied explicit styling to input fields in AddMasterOwnerDialog,
    AddUserDialog, and ChangePasswordDialog for visual clarity.
- v1.10.0 (2025-05-15): Implemented Delete Master Owner, fixed Add dialogs.
- v1.9.0 (2025-05-15): Implemented "Delete Master Owner" functionality (stub).
- v1.8.0 (2025-05-15): Implemented "Add Master Owner" functionality.
"""

import logging
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLineEdit,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTabWidget,
    QFormLayout,
    QComboBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from views.base_view import BaseView
from controllers.user_controller import UserController
from controllers.owner_controller import OwnerController
from config.app_config import AppConfig  # Import AppConfig for colors
from models import User, Owner, StateProvince


# --- Constants for Dark Theme are now in AppConfig ---


class UserListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {AppConfig.DARK_BORDER}; background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY}; outline: none; border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px; border-bottom: 1px solid {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION}40;
                border-left: 3px solid {AppConfig.DARK_PRIMARY_ACTION}; color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {AppConfig.DARK_ITEM_HOVER}; }}
            """
        )


class OwnerMasterListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {AppConfig.DARK_BORDER}; background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
                color: {AppConfig.DARK_TEXT_PRIMARY}; outline: none; border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px; border-bottom: 1px solid {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION}40;
                border-left: 3px solid {AppConfig.DARK_PRIMARY_ACTION}; color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {AppConfig.DARK_ITEM_HOVER}; }}
            """
        )


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New User")
        self.setMinimumWidth(400)
        self.logger = logging.getLogger(self.__class__.__name__)
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        dialog_styles = (
            f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top:3px; }}"
            + f"QCheckBox::indicator {{ width: 13px; height: 13px; }}"
        )
        self.setStyleSheet(dialog_styles)
        specific_input_style = UserManagementScreen.get_specific_input_field_style()

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("Max 20 chars, no spaces")
        self.user_id_input.setStyleSheet(specific_input_style)
        form_layout.addRow("User ID*:", self.user_id_input)
        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Full name of the user")
        self.user_name_input.setStyleSheet(specific_input_style)
        form_layout.addRow("User Name*:", self.user_name_input)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Min 6 characters")
        self.password_input.setStyleSheet(specific_input_style)
        form_layout.addRow("Password*:", self.password_input)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter password")
        self.confirm_password_input.setStyleSheet(specific_input_style)
        form_layout.addRow("Confirm Password*:", self.confirm_password_input)
        self.is_active_checkbox = QCheckBox("User is Active")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("", self.is_active_checkbox)
        layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(
                UserManagementScreen.get_generic_button_style()
            )  # Use static method
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = AppConfig.DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        user_id = self.user_id_input.text().strip().upper()
        user_name = self.user_name_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        errors = []
        if not user_id:
            errors.append("User ID is required.")
        if " " in user_id:
            errors.append("User ID cannot contain spaces.")
        if not user_name:
            errors.append("User Name is required.")
        if not password:
            errors.append("Password is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return
        self.logger.debug("AddUserDialog validation successful, accepting.")
        super().accept()

    def get_data(self) -> dict:
        return {
            "user_id": self.user_id_input.text().strip().upper(),
            "user_name": self.user_name_input.text().strip(),
            "password": self.password_input.text(),
            "is_active": self.is_active_checkbox.isChecked(),
        }


class ChangePasswordDialog(QDialog):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(f"Change Password for {self.user_id}")
        self.setMinimumWidth(400)
        self.logger = logging.getLogger(self.__class__.__name__)
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)
        dialog_styles = f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top:3px; }}"
        self.setStyleSheet(dialog_styles)
        specific_input_style = UserManagementScreen.get_specific_input_field_style()
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Min 6 characters")
        self.new_password_input.setStyleSheet(specific_input_style)
        form_layout.addRow("New Password*:", self.new_password_input)
        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_new_password_input.setPlaceholderText("Re-enter new password")
        self.confirm_new_password_input.setStyleSheet(specific_input_style)
        form_layout.addRow("Confirm New Password*:", self.confirm_new_password_input)
        layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(UserManagementScreen.get_generic_button_style())
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = AppConfig.DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        new_password = self.new_password_input.text()
        confirm_new_password = self.confirm_new_password_input.text()
        errors = []
        if not new_password:
            errors.append("New Password is required.")
        if len(new_password) < 6:
            errors.append("New Password must be at least 6 characters.")
        if new_password != confirm_new_password:
            errors.append("New passwords do not match.")
        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return
        self.logger.debug(
            f"ChangePasswordDialog validation successful for user {self.user_id}, accepting."
        )
        super().accept()

    def get_new_password(self) -> str:
        return self.new_password_input.text()


class AddMasterOwnerDialog(QDialog):
    def __init__(self, parent_controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Master Owner")
        self.setMinimumWidth(600)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.owner_controller = parent_controller
        palette = QPalette()
        palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_INPUT_FIELD_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        self.setPalette(palette)
        main_dialog_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border: none;"
        )
        form_container_widget = QWidget()
        form_container_widget.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND};"
        )
        form_layout = QFormLayout(form_container_widget)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        dialog_specific_styles = (
            f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
            + f"QCheckBox::indicator {{ width: 13px; height: 13px; }}"
        )
        self.setStyleSheet(dialog_specific_styles)

        self.form_fields = {}
        specific_input_style = UserManagementScreen.get_specific_input_field_style()

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
            ("Phone*:", "phone", "QLineEdit", ""),
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
                if field_name == "state_code":
                    self._populate_states_combo(widget)
            else:
                widget = QWidget()
            widget.setStyleSheet(specific_input_style)
            self.form_fields[field_name] = widget
            form_layout.addRow(label_widget, widget)

        self.form_fields["is_active"] = QCheckBox("Owner is Active")
        self.form_fields["is_active"].setChecked(True)
        form_layout.addRow("", self.form_fields["is_active"])
        scroll_area.setWidget(form_container_widget)
        main_dialog_layout.addWidget(scroll_area)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(UserManagementScreen.get_generic_button_style())
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = AppConfig.DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        main_dialog_layout.addWidget(self.button_box)

    def _populate_states_combo(self, combo_box: QComboBox):
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states = ref_data.get("states", [])
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("", None)
            for state_data in states:
                combo_box.addItem(state_data["name"], state_data["id"])
            combo_box.blockSignals(False)
            self.logger.debug(
                f"Populated states combo in AddMasterOwnerDialog with {len(states)} states."
            )
        except Exception as e:
            self.logger.error(
                f"Error populating states combo in AddMasterOwnerDialog: {e}",
                exc_info=True,
            )

    def validate_and_accept(self):
        owner_data = self.get_data()
        is_valid, errors = self.owner_controller.validate_owner_data(
            owner_data, is_new=True
        )
        if not is_valid:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please correct the following errors:\n- " + "\n- ".join(errors),
            )
            return
        self.logger.debug("AddMasterOwnerDialog validation successful, accepting.")
        super().accept()

    def get_data(self) -> dict:
        data = {}
        for field_name, widget in self.form_fields.items():
            if isinstance(widget, QLineEdit):
                data[field_name] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                data[field_name] = widget.currentData()
            elif isinstance(widget, QCheckBox):
                data[field_name] = widget.isChecked()
        return data


class UserManagementScreen(BaseView):
    exit_requested = Signal()

    def __init__(self, current_admin_user: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"UserManagementScreen __init__ started by admin: {current_admin_user}"
        )
        self.current_admin_user = current_admin_user
        self.user_controller = UserController()
        self.owner_controller = OwnerController()
        self.users_list_data = []
        self.selected_user_id = None
        self.current_selected_user_obj = None
        self.has_details_changed = False
        self.owners_master_list_data = []
        self.selected_master_owner_id = None
        self.current_selected_master_owner_obj = None
        self.has_owner_details_changed = False
        self.owner_form_fields = {}
        super().__init__()
        dark_palette = QPalette()
        dark_palette.setColor(
            QPalette.ColorRole.Window, QColor(AppConfig.DARK_BACKGROUND)
        )
        dark_palette.setColor(
            QPalette.ColorRole.WindowText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        dark_palette.setColor(
            QPalette.ColorRole.Base, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#333333"))
        dark_palette.setColor(
            QPalette.ColorRole.ToolTipBase, QColor(AppConfig.DARK_WIDGET_BACKGROUND)
        )
        dark_palette.setColor(
            QPalette.ColorRole.ToolTipText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        dark_palette.setColor(
            QPalette.ColorRole.Text, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        dark_palette.setColor(
            QPalette.ColorRole.Button, QColor(AppConfig.DARK_BUTTON_BG)
        )
        dark_palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(AppConfig.DARK_TEXT_PRIMARY)
        )
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(
            QPalette.ColorRole.Link, QColor(AppConfig.DARK_PRIMARY_ACTION)
        )
        dark_palette.setColor(
            QPalette.ColorRole.Highlight, QColor(AppConfig.DARK_HIGHLIGHT_BG)
        )
        dark_palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(AppConfig.DARK_HIGHLIGHT_TEXT)
        )
        dark_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(AppConfig.DARK_TEXT_TERTIARY)
        )
        disabled_text_color = QColor(AppConfig.DARK_TEXT_TERTIARY)
        disabled_bg_color = QColor(AppConfig.DARK_HEADER_FOOTER)
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text_color
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            disabled_text_color,
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, disabled_bg_color
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, disabled_bg_color
        )
        self.setPalette(dark_palette)
        self.setAutoFillBackground(True)
        self.load_users_data()
        self.load_master_owners_data()
        self.logger.info("UserManagementScreen initialized with Tabbed Interface.")

    def setup_ui(self):
        self.logger.debug("UserManagementScreen setup_ui started.")
        self.set_title("System Setup & Administration")
        self.resize(900, 700)
        self.center_on_screen()
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setup_screen_header(main_layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            f"QTabWidget::pane {{border: 1px solid {AppConfig.DARK_BORDER}; background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;}} QTabBar::tab {{padding: 10px 20px; margin-right: 2px; background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_SECONDARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-bottom: none; border-top-left-radius: 5px; border-top-right-radius: 5px; font-size: 13px;}} QTabBar::tab:selected {{background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; color: {AppConfig.DARK_TEXT_PRIMARY}; font-weight: bold; border-bottom-color: {AppConfig.DARK_WIDGET_BACKGROUND};}} QTabBar::tab:!selected:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; color: {AppConfig.DARK_TEXT_PRIMARY}; }}"
        )
        main_layout.addWidget(self.tab_widget, 1)
        self.users_tab = QWidget()
        self.users_tab.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND};"
        )
        self.setup_users_tab_ui(self.users_tab)
        self.tab_widget.addTab(self.users_tab, "👥 Users")
        self.owners_tab = QWidget()
        self.owners_tab.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND};"
        )
        self.setup_owners_tab_ui(self.owners_tab)
        self.tab_widget.addTab(self.owners_tab, "👤 Owners")
        placeholder_tabs = [
            "📍 Locations",
            "💊 Drugs",
            "💉 Procedures",
            "💲 Charge Codes",
        ]
        for tab_name in placeholder_tabs:
            placeholder_widget = QWidget()
            placeholder_widget.setStyleSheet(
                f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; padding: 20px;"
            )
            placeholder_layout = QVBoxLayout(placeholder_widget)
            placeholder_label = QLabel(
                f"Management for {tab_name.split(' ')[1]} will be here."
            )
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet(
                f"color: {AppConfig.DARK_TEXT_SECONDARY}; font-size: 16px; background-color: transparent;"
            )
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(placeholder_widget, tab_name)
        persistent_action_bar = QFrame()
        persistent_action_bar.setFixedHeight(50)
        persistent_action_bar.setStyleSheet(
            f"QFrame {{background-color: {AppConfig.DARK_HEADER_FOOTER}; border: none; border-top: 1px solid {AppConfig.DARK_BORDER}; padding: 0 10px;}} QPushButton {{background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;}} QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}"
        )
        persistent_action_layout = QHBoxLayout(persistent_action_bar)
        persistent_action_layout.addStretch()
        self.exit_btn = QPushButton("🔙 Return to Main")
        persistent_action_layout.addWidget(self.exit_btn)
        main_layout.addWidget(persistent_action_bar)
        self.setup_connections()
        self.logger.debug("UserManagementScreen UI setup complete.")

    @staticmethod
    def get_generic_button_style(parent_for_palette=None):  # Now static
        return f"QPushButton {{background-color: {AppConfig.DARK_BUTTON_BG}; color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;}} QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }} QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; color: {AppConfig.DARK_TEXT_TERTIARY}; }}"

    @staticmethod
    def get_specific_input_field_style():
        return f"""
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; 
                color: {AppConfig.DARK_TEXT_PRIMARY}; 
                border: 1px solid {AppConfig.DARK_BORDER}; 
                border-radius: 4px; 
                padding: 6px; 
                min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ 
                border-color: {AppConfig.DARK_PRIMARY_ACTION}; 
            }}
            QLineEdit:read-only {{ 
                background-color: #404040; /* A bit darker than general input field */
                color: {AppConfig.DARK_TEXT_TERTIARY}; 
            }}
            QComboBox::drop-down {{ 
                border: none; background-color: transparent; 
                subcontrol-position: right center; width: 15px; 
            }}
            QComboBox::down-arrow {{ image: url(none); /* Consider a dark theme arrow asset */ }}
            QComboBox QAbstractItemView {{ 
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; 
                color: {AppConfig.DARK_TEXT_PRIMARY}; 
                border: 1px solid {AppConfig.DARK_BORDER}; 
                selection-background-color: {AppConfig.DARK_HIGHLIGHT_BG}; 
                selection-color: {AppConfig.DARK_HIGHLIGHT_TEXT}; 
            }}
        """

    @staticmethod
    def get_dialog_widget_styles():  # Combines specific input with general dialog label/checkbox
        return (
            UserManagementScreen.get_specific_input_field_style()
            + f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
            + f"QCheckBox::indicator {{ width: 13px; height: 13px; }}"
        )

    def setup_screen_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet(
            f"background-color: {AppConfig.DARK_HEADER_FOOTER}; border: none; padding: 0 15px;"
        )
        header_layout = QHBoxLayout(header_frame)
        title_label = QLabel("System Setup & Administration")
        title_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 16, QFont.Weight.Bold))
        title_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; background-color: transparent;"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        parent_layout.addWidget(header_frame)

    def setup_users_tab_ui(self, parent_tab_widget):
        users_tab_layout = QVBoxLayout(parent_tab_widget)
        users_tab_layout.setContentsMargins(15, 15, 15, 15)
        users_tab_layout.setSpacing(10)
        user_action_bar = QFrame()
        user_action_bar_layout = QHBoxLayout(user_action_bar)
        user_action_bar_layout.setContentsMargins(0, 0, 0, 0)
        user_action_bar_layout.setSpacing(10)
        user_action_bar.setStyleSheet("background-color: transparent; border: none;")
        self.add_user_btn = QPushButton("➕ Add User")
        self.delete_user_btn = QPushButton("🗑️ Delete User")
        button_style_generic = self.get_generic_button_style()
        self.add_user_btn.setStyleSheet(
            button_style_generic.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
            ).replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white")
        )  # Use DARK_PRIMARY_ACTION
        self.delete_user_btn.setStyleSheet(
            button_style_generic.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_DANGER_ACTION
            ).replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white")
        )  # Use DARK_DANGER_ACTION
        user_action_bar_layout.addWidget(self.add_user_btn)
        user_action_bar_layout.addWidget(self.delete_user_btn)
        user_action_bar_layout.addStretch()
        users_tab_layout.addWidget(user_action_bar)
        user_content_layout = QHBoxLayout()
        user_content_layout.setSpacing(15)
        list_panel = QFrame()
        list_panel_layout = QVBoxLayout(list_panel)
        list_panel_layout.setContentsMargins(0, 0, 0, 0)
        list_panel.setFixedWidth(300)
        self.user_list_widget = UserListWidget()
        list_panel_layout.addWidget(self.user_list_widget)
        user_content_layout.addWidget(list_panel)
        self.user_details_form_widget = QFrame()
        self.user_details_form_widget.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 5px;"
        )
        details_form_outer_layout = QVBoxLayout(self.user_details_form_widget)
        details_form_outer_layout.setContentsMargins(15, 15, 15, 15)
        details_form_layout = QFormLayout()
        details_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        details_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        details_form_layout.setSpacing(10)

        specific_input_style_form = (
            self.get_specific_input_field_style()
        )  # For this form's inputs
        label_style_form = f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top:3px; }}"

        self.detail_user_id_input = QLineEdit()
        self.detail_user_id_input.setReadOnly(True)
        self.detail_user_id_input.setStyleSheet(
            specific_input_style_form
            + f"QLineEdit:read-only {{ background-color: #404040; color: {AppConfig.DARK_TEXT_TERTIARY}; }}"
        )
        user_id_label = QLabel("User ID:")
        user_id_label.setStyleSheet(label_style_form)
        details_form_layout.addRow(user_id_label, self.detail_user_id_input)
        self.detail_user_name_input = QLineEdit()
        self.detail_user_name_input.setStyleSheet(specific_input_style_form)
        self.detail_user_name_input.textChanged.connect(
            self.on_user_detail_field_changed
        )
        user_name_label = QLabel("User Name*:")
        user_name_label.setStyleSheet(label_style_form)
        details_form_layout.addRow(user_name_label, self.detail_user_name_input)
        self.detail_is_active_checkbox = QCheckBox("User is Active")
        self.detail_is_active_checkbox.setStyleSheet(
            f"QCheckBox {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        self.detail_is_active_checkbox.stateChanged.connect(
            self.on_user_detail_field_changed
        )
        details_form_layout.addRow("", self.detail_is_active_checkbox)
        details_form_outer_layout.addLayout(details_form_layout)
        details_form_outer_layout.addStretch()
        form_button_layout = QHBoxLayout()
        self.save_user_changes_btn = QPushButton("💾 Save Changes")
        self.save_user_changes_btn.setStyleSheet(
            button_style_generic.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
            )
        )
        self.save_user_changes_btn.setEnabled(False)
        self.change_password_btn_form = QPushButton("🔑 Change Password...")
        self.change_password_btn_form.setStyleSheet(button_style_generic)
        self.change_password_btn_form.setEnabled(False)
        form_button_layout.addStretch()
        form_button_layout.addWidget(self.change_password_btn_form)
        form_button_layout.addWidget(self.save_user_changes_btn)
        details_form_outer_layout.addLayout(form_button_layout)
        user_content_layout.addWidget(self.user_details_form_widget, 1)
        self.user_details_form_widget.hide()
        self.user_details_panel_placeholder = QLabel(
            "Select a user from the list to view or edit details."
        )
        self.user_details_panel_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_details_panel_placeholder.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; font-size: 14px; border: 1px dashed {AppConfig.DARK_BORDER}; border-radius: 5px; background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; padding: 20px;"
        )
        user_content_layout.addWidget(self.user_details_panel_placeholder, 1)
        users_tab_layout.addLayout(user_content_layout, 1)
        self.delete_user_btn.setEnabled(False)

    def setup_owners_tab_ui(self, parent_tab_widget):
        owners_tab_layout = QVBoxLayout(parent_tab_widget)
        owners_tab_layout.setContentsMargins(15, 15, 15, 15)
        owners_tab_layout.setSpacing(10)
        owner_action_bar = QFrame()
        owner_action_bar_layout = QHBoxLayout(owner_action_bar)
        owner_action_bar_layout.setContentsMargins(0, 0, 0, 0)
        owner_action_bar_layout.setSpacing(10)
        owner_action_bar.setStyleSheet("background-color: transparent; border: none;")
        self.add_master_owner_btn = QPushButton("➕ Add Owner")
        self.delete_master_owner_btn = QPushButton("🗑️ Delete Owner")
        button_style_generic = self.get_generic_button_style()
        self.add_master_owner_btn.setStyleSheet(
            button_style_generic.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_PRIMARY_ACTION
            ).replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white")
        )
        self.delete_master_owner_btn.setStyleSheet(
            button_style_generic.replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_DANGER_ACTION
            ).replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white")
        )
        self.delete_master_owner_btn.setEnabled(False)
        owner_action_bar_layout.addWidget(self.add_master_owner_btn)
        owner_action_bar_layout.addWidget(self.delete_master_owner_btn)
        owner_action_bar_layout.addStretch()
        owners_tab_layout.addWidget(owner_action_bar)

        owner_content_layout = QHBoxLayout()
        owner_content_layout.setSpacing(15)
        owner_list_panel = QFrame()
        owner_list_panel_layout = QVBoxLayout(owner_list_panel)
        owner_list_panel_layout.setContentsMargins(0, 0, 0, 0)
        owner_list_panel.setFixedWidth(350)
        self.owner_master_list_widget = OwnerMasterListWidget()
        owner_list_panel_layout.addWidget(self.owner_master_list_widget)
        owner_content_layout.addWidget(owner_list_panel)

        self.owner_details_form_widget = QFrame()
        self.owner_details_form_widget.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 5px; padding:0px;"
        )

        owner_details_scroll_area = QScrollArea()
        owner_details_scroll_area.setWidgetResizable(True)
        owner_details_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        owner_details_scroll_area.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; border: none;"
        )

        owner_details_form_container = QWidget()
        owner_details_form_container.setStyleSheet(
            f"background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; padding: 15px;"
        )

        details_form_layout = QFormLayout(owner_details_form_container)
        details_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        details_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        details_form_layout.setSpacing(10)

        owner_form_label_style = f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
        owner_form_input_style = self.get_specific_input_field_style()

        fields_to_create = [
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
            ("Phone*:", "phone", "QLineEdit", ""),
            ("Email:", "email", "QLineEdit", ""),
        ]
        for label_text, field_name, widget_type, placeholder in fields_to_create:
            form_label = QLabel(label_text)
            form_label.setStyleSheet(owner_form_label_style)
            if widget_type == "QLineEdit":
                widget = QLineEdit()
                if placeholder:
                    widget.setPlaceholderText(placeholder)
                widget.textChanged.connect(self.on_owner_detail_field_changed)
            elif widget_type == "QComboBox":
                widget = QComboBox()
                if field_name == "state_code":
                    self.populate_states_combo(widget)
                widget.currentIndexChanged.connect(self.on_owner_detail_field_changed)
            else:
                widget = QWidget()
            widget.setStyleSheet(owner_form_input_style)
            self.owner_form_fields[field_name] = widget
            details_form_layout.addRow(form_label, widget)

        self.owner_form_fields["is_active"] = QCheckBox("Owner is Active")
        self.owner_form_fields["is_active"].setStyleSheet(
            f"QCheckBox {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color: transparent; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        self.owner_form_fields["is_active"].stateChanged.connect(
            self.on_owner_detail_field_changed
        )
        details_form_layout.addRow("", self.owner_form_fields["is_active"])

        owner_details_scroll_area.setWidget(owner_details_form_container)
        owner_details_form_main_layout = QVBoxLayout(self.owner_details_form_widget)
        owner_details_form_main_layout.setContentsMargins(0, 0, 0, 0)
        owner_details_form_main_layout.addWidget(owner_details_scroll_area)
        self.save_master_owner_changes_btn = QPushButton("💾 Save Owner Changes")
        self.save_master_owner_changes_btn.setStyleSheet(
            self.get_generic_button_style().replace(
                AppConfig.DARK_BUTTON_BG, AppConfig.DARK_SUCCESS_ACTION
            )
        )
        self.save_master_owner_changes_btn.setEnabled(False)
        owner_form_button_layout = QHBoxLayout()
        owner_form_button_layout.addStretch()
        owner_form_button_layout.addWidget(self.save_master_owner_changes_btn)
        owner_details_form_main_layout.addLayout(owner_form_button_layout)
        owner_content_layout.addWidget(self.owner_details_form_widget, 1)
        self.owner_details_form_widget.hide()
        self.owner_details_panel_placeholder = QLabel(
            "Select an owner from the list to view or edit details, or click 'Add Owner'."
        )
        self.owner_details_panel_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.owner_details_panel_placeholder.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; font-size: 14px; border: 1px dashed {AppConfig.DARK_BORDER}; border-radius: 5px; background-color: {AppConfig.DARK_WIDGET_BACKGROUND}; padding: 20px;"
        )
        owner_content_layout.addWidget(self.owner_details_panel_placeholder, 1)
        owners_tab_layout.addLayout(owner_content_layout, 1)

    def populate_states_combo(self, combo_box: QComboBox):
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states = ref_data.get("states", [])
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("", None)
            for state_data in states:
                combo_box.addItem(state_data["name"], state_data["id"])
            combo_box.blockSignals(False)
            self.logger.debug(f"Populated states combo with {len(states)} states.")
        except Exception as e:
            self.logger.error(f"Error populating states combo: {e}", exc_info=True)

    def setup_connections(self):
        self.exit_btn.clicked.connect(self.handle_exit_screen)
        self.user_list_widget.itemSelectionChanged.connect(
            self.on_user_selection_changed
        )
        self.add_user_btn.clicked.connect(self.handle_add_user)
        self.delete_user_btn.clicked.connect(self.handle_delete_user)
        if hasattr(self, "save_user_changes_btn"):
            self.save_user_changes_btn.clicked.connect(self.handle_save_user_changes)
        if hasattr(self, "change_password_btn_form"):
            self.change_password_btn_form.clicked.connect(self.handle_change_password)
        if hasattr(self, "add_master_owner_btn"):
            self.add_master_owner_btn.clicked.connect(self.handle_add_master_owner)
        if hasattr(self, "delete_master_owner_btn"):
            self.delete_master_owner_btn.clicked.connect(
                self.handle_delete_master_owner
            )
        if hasattr(self, "owner_master_list_widget"):
            self.owner_master_list_widget.itemSelectionChanged.connect(
                self.on_master_owner_selection_changed
            )
        if hasattr(self, "save_master_owner_changes_btn"):
            self.save_master_owner_changes_btn.clicked.connect(
                self.handle_save_master_owner_changes
            )
        self.logger.debug("UserManagementScreen connections set up.")

    def load_master_owners_data(self):
        self.logger.info("Loading master owners data...")
        self.owners_master_list_data = self.owner_controller.get_all_master_owners(
            include_inactive=True
        )
        current_selection_id = self.selected_master_owner_id
        self.owner_master_list_widget.clear()
        if not self.owners_master_list_data:
            self.logger.info("No master owners found.")
            self.display_owner_details_form(False)
            if hasattr(self, "delete_master_owner_btn"):
                self.delete_master_owner_btn.setEnabled(False)
            return
        new_selection_index = -1
        for i, owner_obj in enumerate(self.owners_master_list_data):
            dp = []
            if owner_obj.farm_name:
                dp.append(owner_obj.farm_name)
            ind_name_parts = []
            if owner_obj.first_name:
                ind_name_parts.append(owner_obj.first_name)
            if owner_obj.last_name:
                ind_name_parts.append(owner_obj.last_name)
            ind_name = " ".join(ind_name_parts)
            if ind_name:
                dp.append(f"({ind_name})" if owner_obj.farm_name else ind_name)
            item_text = " ".join(dp) if dp else "Unnamed Owner"
            if owner_obj.account_number:
                item_text += f" [{owner_obj.account_number}]"
            item_text += f" ({'Active' if owner_obj.is_active else 'Inactive'})"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, owner_obj.owner_id)
            self.owner_master_list_widget.addItem(list_item)
            if owner_obj.owner_id == current_selection_id:
                new_selection_index = i
        self.logger.info(f"Loaded {len(self.owners_master_list_data)} master owners.")
        if new_selection_index != -1:
            self.owner_master_list_widget.setCurrentRow(new_selection_index)
        elif self.owner_master_list_widget.count() > 0:
            self.owner_master_list_widget.setCurrentRow(0)
        else:
            self.display_owner_details_form(False)
            if hasattr(self, "delete_master_owner_btn"):
                self.delete_master_owner_btn.setEnabled(False)

    def on_master_owner_selection_changed(self):
        selected_items = self.owner_master_list_widget.selectedItems()
        if selected_items:
            self.selected_master_owner_id = selected_items[0].data(
                Qt.ItemDataRole.UserRole
            )
            self.logger.info(
                f"Master owner selected: ID {self.selected_master_owner_id}"
            )
            self.current_selected_master_owner_obj = (
                self.owner_controller.get_owner_by_id(self.selected_master_owner_id)
            )
            if self.current_selected_master_owner_obj:
                self.populate_owner_details_form(self.current_selected_master_owner_obj)
                self.display_owner_details_form(True)
            else:
                self.logger.error(
                    f"Could not fetch master owner ID: {self.selected_master_owner_id}"
                )
                self.display_owner_details_form(False)
        else:
            self.selected_master_owner_id = None
            self.current_selected_master_owner_obj = None
            self.display_owner_details_form(False)
            self.logger.info("Master owner selection cleared.")
        self.update_owner_form_button_states()

    def populate_owner_details_form(self, owner: Owner):
        for widget in self.owner_form_fields.values():
            widget.blockSignals(True)
        self.owner_form_fields["account_number"].setText(owner.account_number or "")
        self.owner_form_fields["farm_name"].setText(owner.farm_name or "")
        self.owner_form_fields["first_name"].setText(owner.first_name or "")
        self.owner_form_fields["last_name"].setText(owner.last_name or "")
        self.owner_form_fields["address_line1"].setText(owner.address_line1 or "")
        self.owner_form_fields["address_line2"].setText(owner.address_line2 or "")
        self.owner_form_fields["city"].setText(owner.city or "")
        state_combo = self.owner_form_fields["state_code"]
        state_index = state_combo.findData(owner.state_code)
        state_combo.setCurrentIndex(state_index if state_index != -1 else 0)
        self.owner_form_fields["zip_code"].setText(owner.zip_code or "")
        self.owner_form_fields["country_name"].setText(
            getattr(owner.state, "country_code", "") if owner.state else ""
        )
        self.owner_form_fields["phone"].setText(owner.phone or "")
        self.owner_form_fields["email"].setText(owner.email or "")
        self.owner_form_fields["is_active"].setChecked(owner.is_active)
        for widget in self.owner_form_fields.values():
            widget.blockSignals(False)
        self.has_owner_details_changed = False
        self.update_owner_form_button_states()

    def on_owner_detail_field_changed(self):
        if (
            not self.has_owner_details_changed
            and self.current_selected_master_owner_obj
        ):
            self.logger.debug("Change detected in owner detail form.")
            self.has_owner_details_changed = True
            self.update_owner_form_button_states()

    def display_owner_details_form(self, show: bool):
        if show and self.current_selected_master_owner_obj:
            self.owner_details_form_widget.show()
            self.owner_details_panel_placeholder.hide()
        else:
            self.owner_details_form_widget.hide()
            self.owner_details_panel_placeholder.setText(
                "Select an owner from the list to view or edit details, or click 'Add Owner'."
            )
            self.owner_details_panel_placeholder.show()
            if hasattr(self, "save_master_owner_changes_btn"):
                self.save_master_owner_changes_btn.setEnabled(False)
            self.has_owner_details_changed = False

    def update_owner_form_button_states(self):
        is_owner_selected = self.current_selected_master_owner_obj is not None
        can_save_owner = self.has_owner_details_changed and is_owner_selected
        if hasattr(self, "save_master_owner_changes_btn"):
            self.save_master_owner_changes_btn.setEnabled(can_save_owner)
        if hasattr(self, "delete_master_owner_btn"):
            self.delete_master_owner_btn.setEnabled(is_owner_selected)

    def handle_save_master_owner_changes(self):
        if (
            not self.current_selected_master_owner_obj
            or not self.has_owner_details_changed
        ):
            self.logger.warning("Save owner changes: No owner selected or no changes.")
            return
        self.logger.info(
            f"Saving changes for master owner: {self.current_selected_master_owner_obj.owner_id}"
        )
        owner_data_to_save = {
            "account_number": self.owner_form_fields["account_number"].text().strip(),
            "farm_name": self.owner_form_fields["farm_name"].text().strip(),
            "first_name": self.owner_form_fields["first_name"].text().strip(),
            "last_name": self.owner_form_fields["last_name"].text().strip(),
            "address_line1": self.owner_form_fields["address_line1"].text().strip(),
            "address_line2": self.owner_form_fields["address_line2"].text().strip(),
            "city": self.owner_form_fields["city"].text().strip(),
            "state_code": self.owner_form_fields["state_code"].currentData(),
            "zip_code": self.owner_form_fields["zip_code"].text().strip(),
            "country_name": self.owner_form_fields["country_name"].text().strip(),
            "phone": self.owner_form_fields["phone"].text().strip(),
            "email": self.owner_form_fields["email"].text().strip(),
            "is_active": self.owner_form_fields["is_active"].isChecked(),
        }
        validation_payload = owner_data_to_save.copy()
        is_valid, errors = self.owner_controller.validate_owner_data(
            validation_payload, is_new=False
        )
        if not is_valid:
            self.show_error(
                "Validation Error", "Cannot save owner changes:\n" + "\n".join(errors)
            )
            return

        success, message = self.owner_controller.update_master_owner(
            self.current_selected_master_owner_obj.owner_id,
            owner_data_to_save,
            self.current_admin_user,
        )
        if success:
            self.show_info("Owner Updated", message)
            original_selected_id = self.selected_master_owner_id
            self.load_master_owners_data()
            if original_selected_id:
                for i in range(self.owner_master_list_widget.count()):
                    if (
                        self.owner_master_list_widget.item(i).data(
                            Qt.ItemDataRole.UserRole
                        )
                        == original_selected_id
                    ):
                        self.owner_master_list_widget.setCurrentRow(i)
                        break
            if (
                not self.owner_master_list_widget.selectedItems()
                and self.owner_master_list_widget.count() == 0
            ):
                self.display_owner_details_form(False)
            self.has_owner_details_changed = False
            self.update_owner_form_button_states()
        else:
            self.show_error("Update Failed", message)

    def handle_add_master_owner(self):
        self.logger.info("Add Master Owner button clicked.")
        dialog = AddMasterOwnerDialog(
            parent_controller=self.owner_controller, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            owner_data = dialog.get_data()
            self.logger.debug(f"Data from AddMasterOwnerDialog: {owner_data}")
            success, message, new_owner_obj = self.owner_controller.create_master_owner(
                owner_data, self.current_admin_user
            )
            if success:
                self.show_info("Master Owner Created", message)
                self.load_master_owners_data()
                if new_owner_obj:
                    for i in range(self.owner_master_list_widget.count()):
                        if (
                            self.owner_master_list_widget.item(i).data(
                                Qt.ItemDataRole.UserRole
                            )
                            == new_owner_obj.owner_id
                        ):
                            self.owner_master_list_widget.setCurrentRow(i)
                            break
            else:
                self.show_error("Failed to Create Master Owner", message)
        else:
            self.logger.info("Add Master Owner dialog cancelled.")

    def handle_delete_master_owner(self):
        self.logger.info("Delete Master Owner button clicked.")
        if not self.current_selected_master_owner_obj:
            self.show_warning(
                "Delete Owner", "Please select an owner from the list to delete."
            )
            return
        owner_id_to_delete = self.current_selected_master_owner_obj.owner_id
        owner_name_parts = []
        if self.current_selected_master_owner_obj.farm_name:
            owner_name_parts.append(self.current_selected_master_owner_obj.farm_name)
        individual_name_parts = []
        if self.current_selected_master_owner_obj.first_name:
            individual_name_parts.append(
                self.current_selected_master_owner_obj.first_name
            )
        if self.current_selected_master_owner_obj.last_name:
            individual_name_parts.append(
                self.current_selected_master_owner_obj.last_name
            )
        individual_name = " ".join(individual_name_parts)
        if individual_name:
            owner_name_parts.append(
                f"({individual_name})"
                if self.current_selected_master_owner_obj.farm_name
                else individual_name
            )
        owner_name_display = (
            " ".join(owner_name_parts)
            if owner_name_parts
            else f"ID {owner_id_to_delete}"
        )
        reply = self.show_question(
            "Confirm Permanent Deletion",
            f"Are you sure you want to permanently delete owner '{owner_name_display}' (ID: {owner_id_to_delete})?\n\n"
            "This action cannot be undone and will remove the owner from the system entirely.",
        )
        if reply:
            self.logger.info(
                f"User confirmed permanent deletion for master owner ID: {owner_id_to_delete}"
            )
            success, message = self.owner_controller.delete_master_owner(
                owner_id_to_delete, self.current_admin_user
            )
            if success:
                self.show_info("Owner Deleted", message)
                self.selected_master_owner_id = None
                self.current_selected_master_owner_obj = None
                self.load_master_owners_data()
                self.display_owner_details_form(False)
            else:
                self.show_error("Deletion Failed", message)
        else:
            self.logger.info("Master owner deletion cancelled by user.")

    # --- User Tab Methods ---
    def load_users_data(self):
        self.logger.info("Loading users data...")
        self.users_list_data = self.user_controller.get_all_users(include_inactive=True)
        current_selection_id = self.selected_user_id
        self.user_list_widget.clear()
        if not self.users_list_data:
            self.logger.info("No users found.")
            self.display_user_details_form(False)
            self.delete_user_btn.setEnabled(False)
            return
        new_selection_index = -1
        for i, user_obj in enumerate(self.users_list_data):
            item_text = f"{user_obj.user_id} - {user_obj.user_name} ({'Active' if user_obj.is_active else 'Inactive'})"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, user_obj.user_id)
            self.user_list_widget.addItem(list_item)
            if user_obj.user_id == current_selection_id:
                new_selection_index = i
        self.logger.info(f"Loaded {len(self.users_list_data)} users.")
        if new_selection_index != -1:
            self.user_list_widget.setCurrentRow(new_selection_index)
        elif self.user_list_widget.count() > 0:
            self.user_list_widget.setCurrentRow(0)
        else:
            self.display_user_details_form(False)
            self.delete_user_btn.setEnabled(False)

    def on_user_selection_changed(self):
        selected_items = self.user_list_widget.selectedItems()
        if selected_items:
            self.selected_user_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.logger.info(f"User selected: {self.selected_user_id}")
            self.current_selected_user_obj = self.user_controller.get_user_by_id(
                self.selected_user_id
            )
            if self.current_selected_user_obj:
                self.populate_user_details_form(self.current_selected_user_obj)
                self.display_user_details_form(True)
            else:
                self.logger.error(f"Could not fetch user ID: {self.selected_user_id}")
                self.display_user_details_form(False)
        else:
            self.selected_user_id = None
            self.current_selected_user_obj = None
            self.display_user_details_form(False)
            self.logger.info("User selection cleared.")
        self.update_user_form_button_states()

    def display_user_details_form(self, show: bool):
        if show:
            self.user_details_form_widget.show()
            self.user_details_panel_placeholder.hide()
        else:
            self.user_details_form_widget.hide()
            self.user_details_panel_placeholder.show()
            if hasattr(self, "detail_user_id_input"):
                self.detail_user_id_input.clear()
                self.detail_user_name_input.clear()
                self.detail_is_active_checkbox.setChecked(False)
            self.has_details_changed = False

    def populate_user_details_form(self, user: User):
        self.detail_user_id_input.setText(user.user_id)
        self.detail_user_name_input.setText(user.user_name)
        self.detail_is_active_checkbox.setChecked(user.is_active)
        self.has_details_changed = False
        self.update_user_form_button_states()

    def on_user_detail_field_changed(self):
        if not self.has_details_changed and self.current_selected_user_obj:
            self.logger.debug("Change in user detail form.")
            self.has_details_changed = True
            self.update_user_form_button_states()

    def update_user_form_button_states(self):
        is_user_selected = self.current_selected_user_obj is not None
        can_save = self.has_details_changed and is_user_selected
        self.save_user_changes_btn.setEnabled(can_save)
        self.change_password_btn_form.setEnabled(is_user_selected)
        self.delete_user_btn.setEnabled(is_user_selected)

    def handle_exit_screen(self):
        self.logger.info("User Management exit.")
        self.exit_requested.emit()

    def handle_add_user(self):
        self.logger.info("Add User clicked.")
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_data()
            self.logger.debug(f"Data from AddUserDialog: {user_data}")
            success, message, new_user = self.user_controller.create_user(user_data)
            if success:
                self.show_info("User Created", message)
                self.load_users_data()
                if new_user:
                    for i in range(self.user_list_widget.count()):
                        if (
                            self.user_list_widget.item(i).data(Qt.ItemDataRole.UserRole)
                            == new_user.user_id
                        ):
                            self.user_list_widget.setCurrentRow(i)
                            break
            else:
                self.show_error("Failed to Create User", message)
        else:
            self.logger.info("Add User dialog cancelled.")

    def handle_save_user_changes(self):
        if not self.current_selected_user_obj or not self.has_details_changed:
            self.logger.warning("Save user: No user/no changes.")
            return
        self.logger.info(f"Saving user: {self.current_selected_user_obj.user_id}")
        updated_data = {
            "user_name": self.detail_user_name_input.text().strip(),
            "is_active": self.detail_is_active_checkbox.isChecked(),
        }
        validation_payload_user = {
            "user_id": self.current_selected_user_obj.user_id,
            **updated_data,
        }
        is_valid, errors = self.user_controller.validate_user_data(
            validation_payload_user, is_new=False
        )
        if not is_valid:
            self.show_error(
                "Validation Error", "Cannot save user:\n" + "\n".join(errors)
            )
            return
        success, message = self.user_controller.update_user(
            self.current_selected_user_obj.user_id, updated_data
        )
        if success:
            self.show_info("User Updated", message)
            original_selected_id = self.selected_user_id
            self.load_users_data()
            if original_selected_id:
                for i in range(self.user_list_widget.count()):
                    if (
                        self.user_list_widget.item(i).data(Qt.ItemDataRole.UserRole)
                        == original_selected_id
                    ):
                        self.user_list_widget.setCurrentRow(i)
                        break
            if (
                not self.user_list_widget.selectedItems()
                and self.user_list_widget.count() == 0
            ):
                self.display_user_details_form(False)
            self.has_details_changed = False
            self.update_user_form_button_states()
        else:
            self.show_error("Update Failed", message)

    def handle_delete_user(self):
        if not self.selected_user_id or not self.current_selected_user_obj:
            self.show_warning("Delete User", "Select user to delete.")
            return
        user_id_to_delete = self.current_selected_user_obj.user_id
        user_name_display = (
            self.current_selected_user_obj.user_name or user_id_to_delete
        )
        self.logger.warning(
            f"Deleting user: {user_name_display} (ID: {user_id_to_delete})"
        )
        reply = self.show_question(
            "Confirm Deletion",
            f"Permanently delete user '{user_name_display}'?\n\nThis cannot be undone.",
        )
        if reply:
            self.logger.info(f"Confirmed delete user ID: {user_id_to_delete}")
            success, message = self.user_controller.delete_user_permanently(
                user_id_to_delete, self.current_admin_user
            )
            if success:
                self.show_info("User Deleted", message)
                self.selected_user_id = None
                self.current_selected_user_obj = None
                self.load_users_data()
            else:
                self.show_error("Deletion Failed", message)
        else:
            self.logger.info("User delete cancelled.")

    def handle_change_password(self):
        if not self.selected_user_id or not self.current_selected_user_obj:
            self.show_warning("Change Password", "Select user.")
            return
        self.logger.info(f"Change Password for: {self.selected_user_id}")
        dialog = ChangePasswordDialog(self.selected_user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = dialog.get_new_password()
            self.logger.debug(f"Attempt change pass for {self.selected_user_id}.")
            success, message = self.user_controller.change_password(
                self.selected_user_id, new_password
            )
            if success:
                self.show_info("Password Changed", message)
            else:
                self.show_error("Password Change Failed", message)
        else:
            self.logger.info(f"Change pass cancelled for {self.selected_user_id}.")
