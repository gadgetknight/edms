# views/admin/user_management_screen.py

"""
EDSI Veterinary Management System - User Management Screen (Tabbed Interface)
Version: 1.4.1
Purpose: Provides a tabbed interface for managing system settings.
         Implements Change Password functionality.
Last Updated: May 13, 2025
Author: Claude Assistant

Changelog:
- v1.4.1 (2025-05-13): Implemented Change Password functionality.
  - Created `ChangePasswordDialog` for entering new password.
  - Updated `handle_change_password` to show this dialog, call
    `user_controller.change_password`, and display success/error.
- v1.4.0 (2025-05-13): Implemented Delete User, fixed tab styling, removed Edit button.
- v1.3.3 (2025-05-13): Fixed tab pane background and removed redundant Edit User button.
- v1.3.2 (2025-05-13): Fixed AttributeError for QFormLayout.setStyleSheet.
- v1.3.1 (2025-05-13): Fixed AttributeError for UserController.User type hint.
- v1.3.0 (2025-05-13): Implemented User Details display and Edit User form.
- v1.2.1 (2025-05-13): Fixed dark theme styling for tab pane and persistent action bar.
- v1.2.0 (2025-05-13): Refactored for Tabbed Interface.
- v1.1.0 (2025-05-13): Implemented "Add User" functionality with a dialog.
- v1.0.1 (2025-05-13): Fixed NameError for DARK_TEXT_TERTIARY.
- v1.0.0 (2025-05-13): Initial creation of UserManagementScreen.
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
    QScrollArea,
    QGridLayout,
    QLineEdit,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTabWidget,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from views.base_view import BaseView
from controllers.user_controller import UserController
from config.app_config import AppConfig
from models import User


# --- Constants for Dark Theme ---
DARK_BACKGROUND = "#1e1e1e"
DARK_WIDGET_BACKGROUND = "#2b2b2b"
DARK_HEADER_FOOTER = "#2d2d2d"
DARK_BORDER = "#444"
DARK_TEXT_PRIMARY = "#e0e0e0"
DARK_TEXT_SECONDARY = "#aaa"
DARK_TEXT_TERTIARY = "#888"
DARK_ITEM_HOVER = "#3a3a3a"
DARK_BUTTON_BG = "#444"
DARK_BUTTON_HOVER = "#555"
DARK_PRIMARY_ACTION_LIGHT = "#3498db"
DARK_SUCCESS_COLOR = "#28a745"
DARK_WARNING_COLOR = "#ffc107"
DARK_DANGER_COLOR = "#dc3545"


class UserListWidget(QListWidget):
    """Custom list widget for displaying users, styled for dark theme."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {DARK_BORDER};
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                outline: none;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {DARK_BORDER};
                background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION_LIGHT}40;
                border-left: 3px solid {DARK_PRIMARY_ACTION_LIGHT};
                color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {DARK_ITEM_HOVER};
            }}
            """
        )


class AddUserDialog(QDialog):
    """Dialog for adding a new user."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New User")
        self.setMinimumWidth(400)
        self.logger = logging.getLogger(self.__class__.__name__)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_BACKGROUND))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        input_style = f"""
            QLineEdit, QCheckBox {{
                background-color: {DARK_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }}
            QLineEdit:focus {{ border-color: {DARK_PRIMARY_ACTION_LIGHT}; }}
            QCheckBox::indicator {{ width: 13px; height: 13px; }}
            QLabel {{ color: {DARK_TEXT_SECONDARY}; }}
        """
        self.setStyleSheet(input_style)

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("Max 20 chars, no spaces")
        form_layout.addRow("User ID*:", self.user_id_input)

        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Full name of the user")
        form_layout.addRow("User Name*:", self.user_name_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Min 6 characters")
        form_layout.addRow("Password*:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter password")
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
                f"""
                QPushButton {{
                    background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                    border: 1px solid {DARK_BORDER}; border-radius: 4px;
                    padding: 6px 15px; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            """
            )
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = DARK_PRIMARY_ACTION_LIGHT
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    + f"QPushButton {{ background-color: {ok_bg_color}B3; color: white; }}"
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
    """Dialog for changing a user's password."""

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(f"Change Password for {self.user_id}")
        self.setMinimumWidth(400)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Apply dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_BACKGROUND))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        input_style = f"""
            QLineEdit {{
                background-color: {DARK_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }}
            QLineEdit:focus {{ border-color: {DARK_PRIMARY_ACTION_LIGHT}; }}
            QLabel {{ color: {DARK_TEXT_SECONDARY}; }}
        """
        self.setStyleSheet(
            input_style
        )  # Apply to dialog to style QLabels in QFormLayout

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Min 6 characters")
        form_layout.addRow("New Password*:", self.new_password_input)

        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_new_password_input.setPlaceholderText("Re-enter new password")
        form_layout.addRow("Confirm New Password*:", self.confirm_new_password_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                    border: 1px solid {DARK_BORDER}; border-radius: 4px;
                    padding: 6px 15px; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            """
            )
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = DARK_SUCCESS_COLOR  # Use success color for OK
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
        """Validate new password inputs before accepting."""
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
        """Returns the entered new password."""
        return self.new_password_input.text()


class UserManagementScreen(BaseView):
    """Screen for managing system users and other settings via tabs."""

    exit_requested = Signal()

    def __init__(self, current_admin_user: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"UserManagementScreen __init__ started by admin: {current_admin_user}"
        )
        self.current_admin_user = current_admin_user
        self.user_controller = UserController()
        self.users_list_data = []
        self.selected_user_id = None
        self.current_selected_user_obj = None
        self.has_details_changed = False

        super().__init__()

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(DARK_WIDGET_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#333333"))
        dark_palette.setColor(
            QPalette.ColorRole.ToolTipBase, QColor(DARK_WIDGET_BACKGROUND)
        )
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(
            QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION_LIGHT)
        )
        dark_palette.setColor(
            QPalette.ColorRole.Highlight, QColor(DARK_PRIMARY_ACTION_LIGHT)
        )
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        dark_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY)
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(DARK_TEXT_TERTIARY),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(DARK_TEXT_TERTIARY),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Base,
            QColor(DARK_HEADER_FOOTER),
        )
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Button,
            QColor(DARK_HEADER_FOOTER),
        )
        self.setPalette(dark_palette)

        self.load_users_data()
        self.logger.info("UserManagementScreen initialized with Tabbed Interface.")

    def setup_ui(self):
        """Setup the UI for user management with tabs."""
        self.logger.debug("UserManagementScreen setup_ui started.")
        self.set_title("System Setup")
        self.resize(900, 700)
        self.center_on_screen()

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_screen_header(main_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {DARK_BORDER};
                background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QTabBar::tab {{
                padding: 10px 20px; margin-right: 2px;
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY};
                border: 1px solid {DARK_BORDER}; border-bottom: none;
                border-top-left-radius: 5px; border-top-right-radius: 5px;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                font-weight: bold;
                border-bottom-color: {DARK_WIDGET_BACKGROUND}; 
            }}
            QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            """
        )
        main_layout.addWidget(self.tab_widget, 1)

        self.users_tab = QWidget()
        self.users_tab.setStyleSheet(f"background-color: {DARK_WIDGET_BACKGROUND};")
        self.setup_users_tab_ui(self.users_tab)
        self.tab_widget.addTab(self.users_tab, "👥 Users")

        placeholder_tabs = [
            "📍 Locations",
            "💊 Drugs",
            "💉 Procedures",
            "💲 Charge Codes",
        ]
        for tab_name in placeholder_tabs:
            placeholder_widget = QWidget()
            placeholder_widget.setStyleSheet(
                f"background-color: {DARK_WIDGET_BACKGROUND}; border-radius: 5px; padding: 20px;"
            )
            placeholder_layout = QVBoxLayout(placeholder_widget)
            placeholder_label = QLabel(
                f"Management for {tab_name.split(' ')[1]} will be here."
            )
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet(
                f"color: {DARK_TEXT_SECONDARY}; font-size: 16px; background-color: transparent;"
            )
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(placeholder_widget, tab_name)

        persistent_action_bar = QFrame()
        persistent_action_bar.setFixedHeight(50)
        persistent_action_bar.setStyleSheet(
            f"""
            QFrame {{
                background-color: {DARK_HEADER_FOOTER}; 
                border: none; border-top: 1px solid {DARK_BORDER}; padding: 0 10px;
            }}
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            """
        )
        persistent_action_layout = QHBoxLayout(persistent_action_bar)
        persistent_action_layout.addStretch()
        self.exit_btn = QPushButton("🔙 Return to Main")
        persistent_action_layout.addWidget(self.exit_btn)
        main_layout.addWidget(persistent_action_bar)

        self.setup_connections()
        self.logger.debug("UserManagementScreen UI setup complete.")

    def setup_users_tab_ui(self, parent_tab_widget):
        """Sets up the UI specifically for the 'Users' tab."""
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

        button_style = self.get_generic_button_style()
        add_btn_bg_color = DARK_PRIMARY_ACTION_LIGHT
        if len(add_btn_bg_color) == 4:
            add_btn_bg_color = f"#{add_btn_bg_color[1]*2}{add_btn_bg_color[2]*2}{add_btn_bg_color[3]*2}"
        self.add_user_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, add_btn_bg_color + "B3").replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white"
            )
        )

        delete_btn_style = self.get_generic_button_style()
        delete_btn_bg_color = DARK_DANGER_COLOR
        if len(delete_btn_bg_color) == 4:
            delete_btn_bg_color = f"#{delete_btn_bg_color[1]*2}{delete_btn_bg_color[2]*2}{delete_btn_bg_color[3]*2}"
        self.delete_user_btn.setStyleSheet(
            delete_btn_style.replace(DARK_BUTTON_BG, delete_btn_bg_color).replace(
                f"color: {DARK_TEXT_PRIMARY}", "color: white"
            )
        )

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
            f"background-color: {DARK_WIDGET_BACKGROUND}; border: 1px solid {DARK_BORDER}; border-radius: 5px;"
        )
        details_form_outer_layout = QVBoxLayout(self.user_details_form_widget)
        details_form_outer_layout.setContentsMargins(15, 15, 15, 15)

        details_form_layout = QFormLayout()
        details_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        details_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        details_form_layout.setSpacing(10)

        input_style = self.get_generic_input_style()
        label_style = (
            f"QLabel {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; }}"
        )

        self.detail_user_id_input = QLineEdit()
        self.detail_user_id_input.setReadOnly(True)
        self.detail_user_id_input.setStyleSheet(
            input_style + "QLineEdit:read-only { background-color: #404040; }"
        )
        user_id_label = QLabel("User ID:")
        user_id_label.setStyleSheet(label_style)
        details_form_layout.addRow(user_id_label, self.detail_user_id_input)

        self.detail_user_name_input = QLineEdit()
        self.detail_user_name_input.setStyleSheet(input_style)
        self.detail_user_name_input.textChanged.connect(self.on_detail_field_changed)
        user_name_label = QLabel("User Name*:")
        user_name_label.setStyleSheet(label_style)
        details_form_layout.addRow(user_name_label, self.detail_user_name_input)

        self.detail_is_active_checkbox = QCheckBox("User is Active")
        self.detail_is_active_checkbox.setStyleSheet(
            f"QCheckBox {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        self.detail_is_active_checkbox.stateChanged.connect(
            self.on_detail_field_changed
        )
        details_form_layout.addRow("", self.detail_is_active_checkbox)

        details_form_outer_layout.addLayout(details_form_layout)
        details_form_outer_layout.addStretch()

        form_button_layout = QHBoxLayout()
        self.save_user_changes_btn = QPushButton("💾 Save Changes")
        save_btn_style = self.get_generic_button_style()
        save_btn_bg_color = DARK_SUCCESS_COLOR
        if len(save_btn_bg_color) == 4:
            save_btn_bg_color = f"#{save_btn_bg_color[1]*2}{save_btn_bg_color[2]*2}{save_btn_bg_color[3]*2}"
        self.save_user_changes_btn.setStyleSheet(
            save_btn_style.replace(DARK_BUTTON_BG, save_btn_bg_color)
        )
        self.save_user_changes_btn.setEnabled(False)
        self.save_user_changes_btn.clicked.connect(self.handle_save_user_changes)

        self.change_password_btn_form = QPushButton("🔑 Change Password...")
        self.change_password_btn_form.setStyleSheet(self.get_generic_button_style())
        self.change_password_btn_form.setEnabled(False)
        self.change_password_btn_form.clicked.connect(self.handle_change_password)

        form_button_layout.addStretch()
        form_button_layout.addWidget(self.change_password_btn_form)
        form_button_layout.addWidget(self.save_user_changes_btn)
        details_form_outer_layout.addLayout(form_button_layout)

        user_content_layout.addWidget(self.user_details_form_widget, 1)
        self.user_details_form_widget.hide()

        self.details_panel_placeholder = QLabel(
            "Select a user from the list to view or edit details."
        )
        self.details_panel_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_panel_placeholder.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 14px; border: 1px dashed {DARK_BORDER}; border-radius: 5px; background-color: {DARK_WIDGET_BACKGROUND};"
        )
        user_content_layout.addWidget(self.details_panel_placeholder, 1)

        users_tab_layout.addLayout(user_content_layout, 1)
        self.delete_user_btn.setEnabled(False)

    def get_generic_button_style(self):
        """Provides a generic dark theme button style."""
        return f"""
            QPushButton {{
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 8px 12px; font-size: 12px; font-weight: 500;
                min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
            QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}
        """

    def get_generic_input_style(self):
        """Provides a generic dark theme input style."""
        return f"""
            QLineEdit {{
                background-color: {DARK_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px;
                padding: 6px; min-height: 20px;
            }}
            QLineEdit:focus {{ border-color: {DARK_PRIMARY_ACTION_LIGHT}; }}
            QLineEdit:read-only {{ background-color: #404040; }}
        """

    def setup_screen_header(self, parent_layout):
        """Sets up a simple header for the screen."""
        header_frame = QFrame()
        header_frame.setFixedHeight(50)
        header_frame.setStyleSheet(
            f"background-color: {DARK_HEADER_FOOTER}; border: none; padding: 0 15px;"
        )
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("System Setup & Administration")
        title_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 16, QFont.Weight.Bold))
        title_label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background-color: transparent;"
        )

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        parent_layout.addWidget(header_frame)

    def setup_connections(self):
        """Connect signals to slots."""
        self.exit_btn.clicked.connect(self.handle_exit_screen)

        self.user_list_widget.itemSelectionChanged.connect(
            self.on_user_selection_changed
        )
        self.add_user_btn.clicked.connect(self.handle_add_user)
        self.delete_user_btn.clicked.connect(self.handle_delete_user)

        # Connect form buttons if they exist (they are created in setup_users_tab_ui)
        if hasattr(self, "save_user_changes_btn"):
            self.save_user_changes_btn.clicked.connect(self.handle_save_user_changes)
        if hasattr(self, "change_password_btn_form"):
            self.change_password_btn_form.clicked.connect(self.handle_change_password)

        self.logger.debug("UserManagementScreen connections set up.")

    def load_users_data(self):
        """Loads users from the controller and populates the list widget."""
        self.logger.info("Loading users data...")
        self.users_list_data = self.user_controller.get_all_users(include_inactive=True)

        current_selection_id = self.selected_user_id
        self.user_list_widget.clear()

        if not self.users_list_data:
            self.logger.info("No users found in the database.")
            self.display_user_details_form(False)
            return

        new_selection_index = -1
        for i, user in enumerate(self.users_list_data):
            item_text = f"{user.user_id} - {user.user_name} ({'Active' if user.is_active else 'Inactive'})"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, user.user_id)
            self.user_list_widget.addItem(list_item)
            if user.user_id == current_selection_id:
                new_selection_index = i

        self.logger.info(f"Loaded {len(self.users_list_data)} users into the list.")
        if new_selection_index != -1:
            self.user_list_widget.setCurrentRow(new_selection_index)
        elif self.user_list_widget.count() > 0:
            self.user_list_widget.setCurrentRow(0)
        else:
            self.display_user_details_form(False)

    def on_user_selection_changed(self):
        """Handles selection changes in the user list."""
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
                self.logger.error(
                    f"Could not fetch details for selected user ID: {self.selected_user_id}"
                )
                self.display_user_details_form(False)
        else:
            self.selected_user_id = None
            self.current_selected_user_obj = None
            self.display_user_details_form(False)
            self.logger.info("User selection cleared.")

        self.update_form_button_states()

    def display_user_details_form(self, show: bool):
        """Shows or hides the user details form and placeholder."""
        if show:
            self.user_details_form_widget.show()
            self.details_panel_placeholder.hide()
        else:
            self.user_details_form_widget.hide()
            self.details_panel_placeholder.show()
            if hasattr(self, "detail_user_id_input"):
                self.detail_user_id_input.clear()
                self.detail_user_name_input.clear()
                self.detail_is_active_checkbox.setChecked(False)
            self.has_details_changed = False

    def populate_user_details_form(self, user: User):
        """Populates the details form with data from the given user object."""
        self.detail_user_id_input.setText(user.user_id)
        self.detail_user_name_input.setText(user.user_name)
        self.detail_is_active_checkbox.setChecked(user.is_active)
        self.has_details_changed = False
        self.update_form_button_states()

    def on_detail_field_changed(self):
        """Marks details as changed when a form field is modified."""
        if not self.has_details_changed:
            self.logger.debug("Change detected in user detail form.")
            self.has_details_changed = True
            self.update_form_button_states()

    def update_form_button_states(self):
        """Updates the enabled state of form buttons and delete button."""
        is_user_selected = self.current_selected_user_obj is not None
        can_save = self.has_details_changed and is_user_selected

        self.save_user_changes_btn.setEnabled(can_save)
        self.change_password_btn_form.setEnabled(is_user_selected)
        self.delete_user_btn.setEnabled(is_user_selected)

    def handle_exit_screen(self):
        """Emits signal to close this screen."""
        self.logger.info("User Management screen exit requested.")
        self.exit_requested.emit()

    def handle_add_user(self):
        """Handles the 'Add User' button click."""
        self.logger.info("Add User button clicked.")
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

    def handle_edit_user_button_click(self):
        """This button was removed. Editing is implicit."""
        self.logger.debug("handle_edit_user_button_click called (button is removed).")
        if self.current_selected_user_obj:
            self.display_user_details_form(True)
            self.detail_user_name_input.setFocus()
        else:
            self.show_warning("Edit User", "Please select a user from the list first.")

    def handle_save_user_changes(self):
        """Handles saving changes made in the user details form."""
        if not self.current_selected_user_obj or not self.has_details_changed:
            self.logger.warning(
                "Save user changes called, but no user selected or no changes made."
            )
            return

        self.logger.info(
            f"Saving changes for user: {self.current_selected_user_obj.user_id}"
        )

        updated_data = {
            "user_name": self.detail_user_name_input.text().strip(),
            "is_active": self.detail_is_active_checkbox.isChecked(),
        }

        is_valid, errors = self.user_controller.validate_user_data(
            {"user_id": self.current_selected_user_obj.user_id, **updated_data},
            is_new=False,
        )
        if not is_valid:
            self.show_error(
                "Validation Error", "Cannot save changes:\n" + "\n".join(errors)
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
            if not self.user_list_widget.selectedItems():
                self.display_user_details_form(False)
            self.has_details_changed = False
            self.update_form_button_states()
        else:
            self.show_error("Update Failed", message)

    def handle_delete_user(self):
        """Handles the 'Delete User' button click."""
        if not self.selected_user_id or not self.current_selected_user_obj:
            self.show_warning(
                "Delete User", "Please select a user from the list to delete."
            )
            return

        user_id_to_delete = self.current_selected_user_obj.user_id
        user_name_display = (
            self.current_selected_user_obj.user_name or user_id_to_delete
        )

        self.logger.warning(
            f"Attempting to delete user: {user_name_display} (ID: {user_id_to_delete})"
        )

        reply = self.show_question(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete user '{user_name_display}'?\n\n"
            "This action cannot be undone.",
        )
        if reply:
            self.logger.info(
                f"User confirmed permanent deletion for user ID: {user_id_to_delete}"
            )
            success, message = self.user_controller.delete_user_permanently(
                user_id_to_delete, self.current_admin_user
            )
            if success:
                self.show_info("User Deleted", message)
                self.selected_user_id = None
                self.current_selected_user_obj = None
                self.load_users_data()
                self.display_user_details_form(False)
            else:
                self.show_error("Deletion Failed", message)
        else:
            self.logger.info("User cancelled deletion.")

    def handle_change_password(self):
        """Handles the 'Change Password...' button click on the form."""
        if not self.selected_user_id or not self.current_selected_user_obj:
            self.show_warning(
                "Change Password", "Please select a user from the list first."
            )
            return

        self.logger.info(
            f"Change Password button clicked for user: {self.selected_user_id}"
        )
        dialog = ChangePasswordDialog(
            self.selected_user_id, self
        )  # Pass user_id to dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = dialog.get_new_password()
            self.logger.debug(
                f"Attempting to change password for user {self.selected_user_id}."
            )

            success, message = self.user_controller.change_password(
                self.selected_user_id, new_password
            )
            if success:
                self.show_info("Password Changed", message)
            else:
                self.show_error("Password Change Failed", message)
        else:
            self.logger.info(
                f"Change password dialog cancelled for user {self.selected_user_id}."
            )
