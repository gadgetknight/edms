# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen (Dark Theme)
Version: 1.4.3
Purpose: Unified interface for horse management. Includes "Owners" tab.
         Ensures correct signal definitions and meticulously reviewed save_changes
         for syntax and indentation. Includes CreateAndLinkOwnerDialog updates.
Last Updated: May 14, 2025
Author: Claude Assistant

Changelog:
- v1.4.3 (2025-05-14): Final attempt to fix Signal AttributeError and save_changes SyntaxError.
  - Signals (`exit_requested`, `setup_requested`, etc.) explicitly defined at class top.
  - `save_changes` method re-typed and re-indented with extreme care.
  - Includes all dialog changes from v1.3.10 (owner dialog field/layout updates).
- v1.3.10 (2025-05-14): Updated CreateAndLinkOwnerDialog fields and layout.
- v1.3.9 (2025-05-14): Fixed UnboundLocalError in `add_new_horse`.
- v1.3.8 (2025-05-14): Fixed AttributeError for horse_controller init order.
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QPushButton,
    QFrame,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QSplitter,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QMenu,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QAction

from views.base_view import BaseView
from config.app_config import AppConfig
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController
from models import StateProvince, User


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
DARK_WARNING_COLOR = "#ffc107"
DARK_SUCCESS_COLOR = "#28a745"
DARK_DANGER_COLOR = "#dc3545"


class HorseListWidget(QListWidget):
    """Custom list widget styled for the dark theme."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: none; background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY}; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 15px; border-bottom: 1px solid {DARK_BORDER};
                min-height: 55px; background-color: {DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION_LIGHT}40; /* RGBA */
                border-left: 3px solid {DARK_PRIMARY_ACTION_LIGHT}; color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
            """
        )


class HorseOwnerListWidget(QListWidget):
    """Custom list widget for displaying horse owners in the Owners tab."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {DARK_BORDER};
                background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY};
                outline: none; border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px; border-bottom: 1px solid {DARK_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {DARK_PRIMARY_ACTION_LIGHT}50;
                color: #ffffff;
            }}
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
            """
        )


class CreateAndLinkOwnerDialog(QDialog):
    """Dialog to create a new owner and link them to a horse with an ownership percentage."""

    def __init__(self, parent_horse_screen, horse_name: str):
        super().__init__(parent_horse_screen)
        self.horse_name = horse_name
        self.setWindowTitle(f"Create New Owner & Link to {self.horse_name}")
        self.setMinimumWidth(750)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.owner_controller = OwnerController()
        self.parent_screen = parent_horse_screen

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(DARK_BACKGROUND))
        palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY))
        self.setPalette(palette)

        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setSpacing(15)
        main_dialog_layout.setContentsMargins(15, 15, 15, 15)

        form_fields_grid_layout = QGridLayout()
        form_fields_grid_layout.setSpacing(25)

        form_layout_left = QFormLayout()
        form_layout_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout_left.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout_left.setSpacing(10)

        form_layout_right = QFormLayout()
        form_layout_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout_right.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout_right.setSpacing(10)

        self.setStyleSheet(f"QLabel {{ color: {DARK_TEXT_SECONDARY}; }}")
        input_style = self.parent_screen.get_form_input_style()

        # Column 1 Fields
        self.account_number_input = QLineEdit()
        self.account_number_input.setPlaceholderText("Account Number")
        self.account_number_input.setStyleSheet(input_style)
        form_layout_left.addRow("Account Number:", self.account_number_input)

        self.farm_name_input = QLineEdit()
        self.farm_name_input.setStyleSheet(input_style)
        form_layout_left.addRow("Farm Name:", self.farm_name_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setStyleSheet(input_style)
        form_layout_left.addRow("First Name*:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setStyleSheet(input_style)
        form_layout_left.addRow("Last Name*:", self.last_name_input)

        self.address1_input = QLineEdit()
        self.address1_input.setStyleSheet(input_style)
        form_layout_left.addRow("Street Address*:", self.address1_input)

        self.address2_input = QLineEdit()
        self.address2_input.setStyleSheet(input_style)
        form_layout_left.addRow("Address Line 2:", self.address2_input)

        self.city_input = QLineEdit()
        self.city_input.setStyleSheet(input_style)
        form_layout_left.addRow("City*:", self.city_input)

        # Column 2 Fields
        self.state_combo = QComboBox()
        self.state_combo.setStyleSheet(input_style)
        form_layout_right.addRow("State/Province*:", self.state_combo)
        self.populate_states_combo()

        self.zip_code_input = QLineEdit()
        self.zip_code_input.setStyleSheet(input_style)
        form_layout_right.addRow("Zip/Postal Code*:", self.zip_code_input)

        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("e.g., USA, Canada")
        self.country_input.setStyleSheet(input_style)
        form_layout_right.addRow("Country:", self.country_input)

        self.phone1_input = QLineEdit()
        self.phone1_input.setStyleSheet(input_style)
        form_layout_right.addRow("Primary Phone:", self.phone1_input)

        self.email_input = QLineEdit()
        self.email_input.setStyleSheet(input_style)
        form_layout_right.addRow("Email:", self.email_input)

        self.credit_rating_input = QLineEdit()
        self.credit_rating_input.setStyleSheet(input_style)
        form_layout_right.addRow("Credit Rating:", self.credit_rating_input)

        self.is_active_checkbox = QCheckBox("Owner is Active")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.setStyleSheet(
            f"QCheckBox {{ color: {DARK_TEXT_SECONDARY}; }} QCheckBox::indicator {{width: 13px; height: 13px;}}"
        )
        form_layout_right.addRow("", self.is_active_checkbox)

        form_fields_grid_layout.addLayout(form_layout_left, 0, 0)
        form_fields_grid_layout.addLayout(form_layout_right, 0, 1)
        main_dialog_layout.addLayout(form_fields_grid_layout)

        percentage_frame = QFrame()
        percentage_layout = QHBoxLayout(percentage_frame)
        percentage_label = QLabel(f"Ownership % for {self.horse_name}:*")
        percentage_label.setStyleSheet(f"color: {DARK_TEXT_SECONDARY};")
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setRange(0.01, 100.00)
        self.percentage_spinbox.setDecimals(2)
        self.percentage_spinbox.setValue(100.00)
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setStyleSheet(self.parent_screen.get_form_input_style())
        percentage_layout.addWidget(percentage_label)
        percentage_layout.addStretch()
        percentage_layout.addWidget(self.percentage_spinbox)
        main_dialog_layout.addWidget(percentage_frame)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Save Owner & Link"
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(self.parent_screen.get_generic_button_style())
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = DARK_SUCCESS_COLOR
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    .replace(DARK_BUTTON_BG, ok_bg_color)
                    .replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;")
                )
        main_dialog_layout.addWidget(self.button_box)

    def populate_states_combo(self):
        try:
            ref_data = self.owner_controller.get_owner_form_reference_data()
            states = ref_data.get("states", [])
            self.state_combo.addItem("", None)
            for state_data in states:
                self.state_combo.addItem(state_data["name"], state_data["id"])
        except Exception as e:
            self.logger.error(f"Error populating states combo: {e}", exc_info=True)

    def validate_and_accept(self):
        errors = []
        if (
            not self.first_name_input.text().strip()
            and not self.farm_name_input.text().strip()
        ):
            errors.append("Either First Name or Farm Name is required.")
        if (
            self.first_name_input.text().strip()
            and not self.last_name_input.text().strip()
        ):
            errors.append("Last Name is required if First Name is provided.")
        elif (
            not self.farm_name_input.text().strip()
            and not self.last_name_input.text().strip()
        ):
            errors.append("Last Name is required if Farm Name is not provided.")
        if not self.address1_input.text().strip():
            errors.append("Street Address is required.")
        if not self.city_input.text().strip():
            errors.append("City is required.")
        if self.state_combo.currentIndex() <= 0:
            errors.append("State/Province is required.")
        if not self.zip_code_input.text().strip():
            errors.append("Zip/Postal Code is required.")
        # Phone is now optional
        percentage = self.percentage_spinbox.value()
        if not (0 < percentage <= 100):
            errors.append("Ownership percentage must be > 0 and <= 100.")
        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return
        self.logger.debug("CreateAndLinkOwnerDialog validation passed, accepting.")
        super().accept()

    def get_data(self) -> Optional[dict]:
        name_parts = []
        if self.first_name_input.text().strip():
            name_parts.append(self.first_name_input.text().strip())
        if self.last_name_input.text().strip():
            name_parts.append(self.last_name_input.text().strip())
        individual_name = " ".join(name_parts)

        constructed_owner_name = ""
        if self.farm_name_input.text().strip():
            constructed_owner_name = self.farm_name_input.text().strip()
            if individual_name:
                constructed_owner_name += f" ({individual_name})"
        elif individual_name:
            constructed_owner_name = individual_name
        else:
            constructed_owner_name = "Unnamed Owner"

        owner_data = {
            "account_number": self.account_number_input.text().strip(),
            "farm_name": self.farm_name_input.text().strip(),
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "owner_name": constructed_owner_name,
            "address_line1": self.address1_input.text().strip(),
            "address_line2": self.address2_input.text().strip(),
            "city": self.city_input.text().strip(),
            "state_code": self.state_combo.currentData(),
            "zip_code": self.zip_code_input.text().strip(),
            "country_name": self.country_input.text().strip(),
            "phone": self.phone1_input.text().strip(),
            "email": self.email_input.text().strip(),
            "is_active": self.is_active_checkbox.isChecked(),
            "credit_rating": self.credit_rating_input.text().strip(),
        }
        return {
            "owner_details": owner_data,
            "percentage": self.percentage_spinbox.value(),
        }


class LinkExistingOwnerDialog(QDialog):
    """Dialog to search for and link an existing owner."""

    def __init__(self, parent_horse_screen, horse_name: str):
        super().__init__(parent_horse_screen)
        self.horse_name = horse_name
        self.setWindowTitle(f"Link Existing Owner to {self.horse_name}")
        self.setMinimumWidth(500)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.owner_controller = OwnerController()
        self.selected_owner_id = None
        self.parent_screen = parent_horse_screen

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
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search Existing Owner:")
        search_label.setStyleSheet(f"color: {DARK_TEXT_SECONDARY};")
        self.owner_search_input = QLineEdit()
        self.owner_search_input.setPlaceholderText("Name or Account #")
        self.owner_search_input.setStyleSheet(self.parent_screen.get_form_input_style())
        self.owner_search_input.textChanged.connect(self.search_owners)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.owner_search_input, 1)
        layout.addLayout(search_layout)

        self.owner_results_list = QListWidget()
        self.owner_results_list.setStyleSheet(HorseOwnerListWidget().styleSheet())
        self.owner_results_list.setFixedHeight(150)
        self.owner_results_list.itemClicked.connect(self.on_owner_selected_from_search)
        layout.addWidget(self.owner_results_list)

        self.selected_owner_display = QLineEdit()
        self.selected_owner_display.setPlaceholderText("No owner selected")
        self.selected_owner_display.setReadOnly(True)
        self.selected_owner_display.setStyleSheet(
            self.parent_screen.get_form_input_style()
            + "QLineEdit:read-only { background-color: #404040; }"
        )
        layout.addWidget(QLabel(f"Selected Owner (to link to {self.horse_name}):"))
        layout.addWidget(self.selected_owner_display)

        percentage_layout = QHBoxLayout()
        percentage_label = QLabel("Ownership Percentage (%):*")
        percentage_label.setStyleSheet(f"color: {DARK_TEXT_SECONDARY};")
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setRange(0.01, 100.00)
        self.percentage_spinbox.setDecimals(2)
        self.percentage_spinbox.setValue(100.00)
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setStyleSheet(self.parent_screen.get_form_input_style())
        percentage_layout.addWidget(percentage_label)
        percentage_layout.addStretch()
        percentage_layout.addWidget(self.percentage_spinbox)
        layout.addLayout(percentage_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Link Owner")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(self.parent_screen.get_generic_button_style())
            if (
                self.button_box.buttonRole(button)
                == QDialogButtonBox.ButtonRole.AcceptRole
            ):
                ok_bg_color = DARK_SUCCESS_COLOR
                if len(ok_bg_color) == 4:
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    button.styleSheet()
                    .replace(DARK_BUTTON_BG, ok_bg_color)
                    .replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;")
                )
        layout.addWidget(self.button_box)
        self.search_owners()

    def search_owners(self):
        search_term = self.owner_search_input.text()
        owners = self.owner_controller.get_all_owners_for_lookup(search_term)
        self.owner_results_list.clear()
        for owner_data in owners:
            item = QListWidgetItem(owner_data["name_account"])
            item.setData(Qt.ItemDataRole.UserRole, owner_data["id"])
            self.owner_results_list.addItem(item)
        self.selected_owner_id = None
        self.selected_owner_display.clear()
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def on_owner_selected_from_search(self, item: QListWidgetItem):
        self.selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_owner_display.setText(item.text())
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def get_data(self) -> Optional[dict]:
        if self.selected_owner_id is None:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please select an owner from the search results.",
            )
            return None
        percentage = self.percentage_spinbox.value()
        if not (0 < percentage <= 100):
            QMessageBox.warning(
                self, "Input Error", "Ownership percentage must be > 0 and <= 100."
            )
            return None
        return {"owner_id": self.selected_owner_id, "percentage": percentage}


class HorseUnifiedManagement(BaseView):
    """Unified horse management interface styled for the dark theme."""

    # --- Signal Definitions ---
    horse_selection_changed = Signal(int)
    unsaved_changes = Signal(bool)
    exit_requested = Signal()
    setup_requested = Signal()

    def __init__(self, current_user=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"HorseUnifiedManagement __init__ started for user: {current_user}"
        )
        self.current_user = current_user or "ADMIN"
        self.horse_controller = HorseController()
        self.owner_controller = OwnerController()
        super().__init__()

        self.logger.info(
            f"DEBUG __init__: hasattr(self, 'setup_connections') -> {hasattr(self, 'setup_connections')}"
        )
        self.logger.info(
            f"DEBUG __init__: hasattr(self, 'setup_requested') -> {hasattr(self, 'setup_requested')}"
        )
        self.logger.info(
            f"DEBUG __init__: hasattr(self, 'exit_requested') -> {hasattr(self, 'exit_requested')}"
        )

        self.horses_list = []
        self.current_horse = None
        self.current_horse_owners = []
        self.selected_horse_owner_id = None
        self.has_changes = False
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

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

        self.load_initial_data()
        self.logger.info("HorseUnifiedManagement screen __init__ finished.")

    def setup_ui(self):
        self.logger.debug("HorseUnifiedManagement setup_ui started.")
        self.set_title("Horse Management")
        self.resize(1200, 800)
        self.center_on_screen()
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setup_header(main_layout)
        self.setup_action_bar(main_layout)
        self.setup_main_content(main_layout)
        self.setup_footer(main_layout)
        self.logger.debug("About to call setup_connections from setup_ui.")
        self.setup_connections()
        self.logger.debug("Dark Theme UI setup complete.")

    def setup_header(self, parent_layout):
        self.logger.debug("setup_header started.")
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setFixedHeight(55)
        header_frame.setStyleSheet(
            f"#HeaderFrame {{ background-color: {DARK_HEADER_FOOTER}; border: none; padding: 0 20px; }} QLabel {{ color: {DARK_TEXT_PRIMARY}; background-color: transparent; }} QPushButton#UserMenuButton {{ color: {DARK_TEXT_SECONDARY}; font-size: 12px; background-color: transparent; border: none; padding: 5px; text-align: right; }} QPushButton#UserMenuButton::menu-indicator {{ image: none; }} QPushButton#UserMenuButton:hover {{ color: {DARK_TEXT_PRIMARY}; background-color: rgba(85, 85, 85, 0.2); }}"
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addStretch()
        title_label = QLabel("EDSI - Horse Management")
        title_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 15, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        breadcrumb_label = QLabel("🏠 Horse Management")
        breadcrumb_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 11px;"
        )
        left_layout.addWidget(breadcrumb_label)
        left_layout.addStretch()
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh Data (F5)")
        self.help_btn = QPushButton("❓")
        self.help_btn.setToolTip("Help (F1)")
        self.print_btn = QPushButton("🖨️")
        self.print_btn.setToolTip("Print Options")
        self.setup_icon_btn = QPushButton("⚙️")
        self.setup_icon_btn.setToolTip("System Setup")
        header_button_style = f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 5px; font-size: 14px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; }} QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} QPushButton:pressed {{ background-color: {DARK_BUTTON_BG}; }}"
        self.refresh_btn.setStyleSheet(header_button_style)
        self.help_btn.setStyleSheet(header_button_style)
        self.print_btn.setStyleSheet(header_button_style)
        self.setup_icon_btn.setStyleSheet(header_button_style)
        self.user_menu_button = QPushButton(f"👤 User: {self.current_user}")
        self.user_menu_button.setObjectName("UserMenuButton")
        self.user_menu_button.setToolTip("User options")
        self.user_menu_button.setFlat(True)
        self.user_menu = QMenu(self)
        self.user_menu.setStyleSheet(
            f"QMenu {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; padding: 5px; }} QMenu::item {{ padding: 5px 20px 5px 20px; min-width: 100px; }} QMenu::item:selected {{ background-color: {DARK_PRIMARY_ACTION_LIGHT}70; color: white; }} QMenu::separator {{ height: 1px; background: {DARK_BORDER}; margin-left: 5px; margin-right: 5px; }}"
        )
        logout_action = QAction("Log Out", self)
        logout_action.triggered.connect(self.handle_logout_request)
        self.user_menu.addAction(logout_action)
        self.user_menu_button.setMenu(self.user_menu)
        right_layout.addWidget(self.refresh_btn)
        right_layout.addWidget(self.help_btn)
        right_layout.addWidget(self.print_btn)
        right_layout.addWidget(self.setup_icon_btn)
        right_layout.addWidget(self.user_menu_button)
        header_layout.addWidget(left_widget)
        header_layout.addStretch()
        header_layout.addWidget(right_widget)
        parent_layout.addWidget(header_frame)
        self.logger.debug("setup_header finished.")

    def handle_logout_request(self):
        self.logger.info("Log Out action triggered from user menu.")
        self.exit_requested.emit()

    def setup_action_bar(self, parent_layout):
        self.logger.debug("setup_action_bar started.")
        action_bar_frame = QFrame()
        action_bar_frame.setObjectName("ActionBarFrame")
        action_bar_frame.setFixedHeight(50)
        action_bar_frame.setStyleSheet(
            f"#ActionBarFrame {{ background-color: {DARK_BACKGROUND}; border: none; border-bottom: 1px solid {DARK_BORDER}; padding: 0 20px; }} QPushButton {{ min-height: 30px; }} QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; }} QRadioButton::indicator {{ width: 13px; height: 13px; }} QRadioButton {{ color: {DARK_TEXT_SECONDARY}; background: transparent; padding: 5px; }}"
        )
        action_bar_layout = QHBoxLayout(action_bar_frame)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(12)
        action_bar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.add_horse_btn = QPushButton("➕ Add Horse")
        self.edit_horse_btn = QPushButton("✓ Edit Selected")
        action_button_style = f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 12px; font-size: 13px; font-weight: 500; }} QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} QPushButton:pressed {{ background-color: {DARK_BUTTON_BG}; }} QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}"
        add_btn_bg_color = DARK_PRIMARY_ACTION_LIGHT
        if len(add_btn_bg_color) == 4:
            add_btn_bg_color = f"#{add_btn_bg_color[1]*2}{add_btn_bg_color[2]*2}{add_btn_bg_color[3]*2}"
        self.add_horse_btn.setStyleSheet(
            action_button_style.replace(
                DARK_BUTTON_BG, add_btn_bg_color + "B3"
            ).replace(f"color: {DARK_TEXT_PRIMARY}", "color: white")
        )  # Using RGBA
        self.edit_horse_btn.setStyleSheet(action_button_style)
        action_bar_layout.addWidget(self.add_horse_btn)
        action_bar_layout.addWidget(self.edit_horse_btn)
        self.filter_group = QButtonGroup(self)
        self.active_only_radio = QRadioButton("Active Only")
        self.all_horses_radio = QRadioButton("All Horses")
        self.deactivated_radio = QRadioButton("Deactivated")
        self.filter_group.addButton(self.active_only_radio)
        self.filter_group.addButton(self.all_horses_radio)
        self.filter_group.addButton(self.deactivated_radio)
        self.active_only_radio.setChecked(True)
        action_bar_layout.addWidget(self.active_only_radio)
        action_bar_layout.addWidget(self.all_horses_radio)
        action_bar_layout.addWidget(self.deactivated_radio)
        action_bar_layout.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(
            self.get_form_input_style(base_bg=DARK_HEADER_FOOTER)
        )
        action_bar_layout.addWidget(self.search_input)
        self.edit_horse_btn.setEnabled(False)
        parent_layout.addWidget(action_bar_frame)
        self.logger.debug("setup_action_bar finished.")

    def setup_main_content(self, parent_layout):
        self.logger.debug("setup_main_content started.")
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(
            f"QSplitter {{ background-color: {DARK_BACKGROUND}; border: none; }} QSplitter::handle {{ background-color: {DARK_BORDER}; }} QSplitter::handle:horizontal {{ width: 1px; }} QSplitter::handle:pressed {{ background-color: {DARK_TEXT_SECONDARY}; }}"
        )
        self.setup_horse_list_panel()
        self.setup_horse_details_panel()
        self.splitter.setSizes([300, 850])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        parent_layout.addWidget(self.splitter, 1)
        self.logger.debug("setup_main_content finished.")

    def setup_horse_list_panel(self):
        self.logger.debug("setup_horse_list_panel started.")
        self.list_widget_container = QWidget()
        self.list_widget_container.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none; border-right: 1px solid {DARK_BORDER};"
        )
        list_layout = QVBoxLayout(self.list_widget_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        self.horse_list = HorseListWidget()
        self.horse_list.setMinimumWidth(250)
        list_layout.addWidget(self.horse_list, 1)
        self.splitter.addWidget(self.list_widget_container)
        self.logger.debug("setup_horse_list_panel finished.")

    def setup_horse_details_panel(self, parent_layout_for_tabs=None):
        self.logger.debug("setup_horse_details_panel started.")
        self.details_widget = QWidget()
        self.details_widget.setStyleSheet(
            f"background-color: {DARK_BACKGROUND}; border: none;"
        )
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(15, 10, 15, 10)
        self.details_layout.setSpacing(15)
        self.horse_details_content_widget = QWidget()
        details_content_layout = QVBoxLayout(self.horse_details_content_widget)
        details_content_layout.setContentsMargins(0, 0, 0, 0)
        details_content_layout.setSpacing(15)
        self.setup_horse_header_details(details_content_layout)
        self.setup_horse_tabs(details_content_layout)
        self.setup_empty_state()
        self.details_layout.addWidget(self.empty_frame)
        self.details_layout.addWidget(self.horse_details_content_widget)
        self.horse_details_content_widget.hide()
        self.splitter.addWidget(self.details_widget)
        self.logger.debug("setup_horse_details_panel finished.")

    def setup_empty_state(self):
        self.logger.debug("setup_empty_state started.")
        self.empty_frame = QFrame()
        self.empty_frame.setObjectName("EmptyFrame")
        self.empty_frame.setStyleSheet(
            f"#EmptyFrame {{ background-color: transparent; border: none; }}"
        )
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(15)
        empty_label = QLabel("Select a horse from the list")
        empty_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 16px; background: transparent;"
        )
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.logger.debug("setup_empty_state finished.")

    def setup_horse_header_details(self, parent_layout):
        self.logger.debug("setup_horse_header_details started.")
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        self.horse_title = QLabel("Horse Name")
        self.horse_title.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold)
        )
        self.horse_title.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )
        self.horse_info_line = QLabel(
            "Account: N/A | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A"
        )
        self.horse_info_line.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        self.horse_info_line.setWordWrap(True)
        header_layout.addWidget(self.horse_title)
        header_layout.addWidget(self.horse_info_line)
        parent_layout.addWidget(header_widget)
        self.logger.debug("setup_horse_header_details finished.")

    def setup_horse_tabs(self, parent_layout_for_tabs):
        self.logger.debug("setup_horse_tabs started.")
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DetailsTabWidget")
        self.tab_widget.setStyleSheet(
            f"""
            QTabWidget#DetailsTabWidget::pane {{
                border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND};
                border-radius: 6px; margin-top: -1px;
            }}
            QTabBar::tab {{
                padding: 8px 15px; margin-right: 2px;
                background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_SECONDARY};
                border: 1px solid {DARK_BORDER}; border-bottom: none;
                border-top-left-radius: 5px; border-top-right-radius: 5px;
                min-width: 90px; font-size: 13px; font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border-color: {DARK_BORDER}; border-bottom-color: {DARK_WIDGET_BACKGROUND};
            }}
            QTabBar::tab:!selected:hover {{ background-color: {DARK_BUTTON_HOVER}; color: {DARK_TEXT_PRIMARY}; }}
            QTabBar {{ border: none; background-color: transparent; margin-bottom: 0px; }}
            """
        )
        self.setup_basic_info_tab()
        self.setup_owners_tab()
        placeholder_tab_names = ["📍 Location", "💰 Billing", "📊 History"]
        for name in placeholder_tab_names:
            placeholder_widget = QWidget()
            placeholder_widget.setStyleSheet(
                f"background-color: {DARK_WIDGET_BACKGROUND};"
            )
            placeholder_layout = QVBoxLayout(placeholder_widget)
            placeholder_label = QLabel(f"Content for {name} tab.")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet(
                f"color: {DARK_TEXT_SECONDARY}; background: transparent;"
            )
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(placeholder_widget, name)
        parent_layout_for_tabs.addWidget(self.tab_widget, 1)
        self.logger.debug("setup_horse_tabs finished.")

    def setup_basic_info_tab(self):
        self.logger.debug("setup_basic_info_tab started.")
        self.basic_info_tab = QWidget()
        self.basic_info_tab.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND};"
        )
        basic_layout = QVBoxLayout(self.basic_info_tab)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        basic_layout.setSpacing(0)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND}; border: none;"
        )
        form_container_widget = QWidget()
        form_container_widget.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND};"
        )
        form_layout = QGridLayout(form_container_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        self.form_fields = {}
        fields = [
            ("Name", "horse_name", "text", True),
            ("Account Number", "account_number", "text", False),
            ("Breed", "breed", "text", False),
            ("Color", "color", "text", False),
            ("Sex", "sex", "combo", False),
            ("Date of Birth", "date_of_birth", "date", False),
            ("Reg. Number", "registration_number", "text", False),
            ("Microchip ID", "microchip_id", "text", False),
            ("Tattoo", "tattoo", "text", False),
            ("Brand", "brand", "text", False),
            ("Location", "current_location_id", "combo", False),
            ("Band/Tag", "band_tag_number", "text", False),
        ]
        for i, (label_text, field_name, field_type, required) in enumerate(fields):
            row, col = i // 2, (i % 2)
            label_str = label_text + ("*" if required else "") + ":"
            label = QLabel(label_str)
            label.setStyleSheet(
                f"font-weight: {'bold' if required else '500'}; color: {DARK_TEXT_SECONDARY}; font-size: 12px; background: transparent; padding-top: 5px;"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            field = None
            input_style = self.get_form_input_style()
            if field_type == "text":
                field = QLineEdit()
                field.textChanged.connect(self.on_field_changed)
            elif field_type == "combo":
                field = QComboBox()
                if field_name == "sex":
                    field.addItems(
                        ["", "Male", "Female", "Gelding", "Stallion", "Mare"]
                    )
                elif field_name == "current_location_id":
                    self.load_locations_combo(field)
                field.currentIndexChanged.connect(self.on_field_changed)
            elif field_type == "date":
                field = QDateEdit()
                field.setCalendarPopup(True)
                field.setDate(QDate())
                field.dateChanged.connect(self.on_field_changed)
                calendar_style = f"QCalendarWidget QWidget {{ alternate-background-color: {DARK_BUTTON_HOVER}; background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; }} QCalendarWidget QToolButton {{ color: {DARK_TEXT_PRIMARY}; background-color: {DARK_BUTTON_BG}; border: 1px solid {DARK_BORDER}; margin: 2px; padding: 5px; }} QCalendarWidget QToolButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} QCalendarWidget QAbstractItemView:enabled {{ color: {DARK_TEXT_PRIMARY}; selection-background-color: {DARK_PRIMARY_ACTION_LIGHT}; }} QCalendarWidget QAbstractItemView:disabled {{ color: {DARK_TEXT_TERTIARY}; }} QCalendarWidget QMenu {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; }} QCalendarWidget QSpinBox {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER};}} #qt_calendar_navigationbar {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_PRIMARY}; }} #qt_calendar_prevmonth, #qt_calendar_nextmonth {{ qproperty-icon: none; }} #qt_calendar_monthbutton, #qt_calendar_yearbutton {{ color: {DARK_TEXT_PRIMARY}; }}"
                field.calendarWidget().setStyleSheet(calendar_style)
            if field:
                field.setStyleSheet(input_style)
                field.setMinimumHeight(32)
                form_layout.addWidget(label, row, col * 2)
                form_layout.addWidget(field, row, col * 2 + 1)
                self.form_fields[field_name] = field
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setStyleSheet(
            self.get_toolbar_button_style(DARK_PRIMARY_ACTION_LIGHT)
        )
        self.save_btn.setEnabled(False)
        self.discard_btn = QPushButton("↩️ Discard Changes")
        self.discard_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {DARK_TEXT_SECONDARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 12px; font-size: 13px; font-weight: 500; min-height: 32px; }} QPushButton:hover {{ background-color: {DARK_ITEM_HOVER}; border-color: {DARK_TEXT_SECONDARY}; color: {DARK_TEXT_PRIMARY}; }} QPushButton:disabled {{ background-color: transparent; border-color: {DARK_BORDER}; color: {DARK_TEXT_TERTIARY}; opacity: 0.7; }}"
        )
        self.discard_btn.setEnabled(False)
        self.toggle_active_btn = QPushButton("Deactivate")
        self.toggle_active_btn.setToolTip("Toggle horse active status")
        self.toggle_active_btn.setEnabled(False)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_active_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.discard_btn)
        button_layout.addWidget(self.save_btn)
        form_layout.addLayout(button_layout, (len(fields) + 1) // 2, 0, 1, 4)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setRowStretch((len(fields) + 1) // 2 + 1, 1)
        scroll_area.setWidget(form_container_widget)
        basic_layout.addWidget(scroll_area)
        self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")
        self.logger.debug("setup_basic_info_tab finished.")

    def setup_owners_tab(self):  # Unchanged
        self.logger.debug("setup_owners_tab started.")
        self.owners_tab_widget = QWidget()
        self.owners_tab_widget.setStyleSheet(
            f"background-color: {DARK_WIDGET_BACKGROUND};"
        )
        owners_layout = QVBoxLayout(self.owners_tab_widget)
        owners_layout.setContentsMargins(15, 15, 15, 15)
        owners_layout.setSpacing(10)
        owners_action_layout = QHBoxLayout()
        self.create_link_owner_btn = QPushButton("➕ Create New & Link")
        self.link_existing_owner_btn = QPushButton("🔗 Link Existing")
        self.remove_horse_owner_btn = QPushButton("➖ Remove Selected Owner")
        button_style = self.get_generic_button_style()
        create_link_style = button_style.replace(DARK_BUTTON_BG, DARK_SUCCESS_COLOR)
        self.create_link_owner_btn.setStyleSheet(
            create_link_style.replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;")
        )
        self.link_existing_owner_btn.setStyleSheet(
            button_style.replace(DARK_BUTTON_BG, DARK_PRIMARY_ACTION_LIGHT)
        )
        remove_owner_style = button_style.replace(
            DARK_BUTTON_BG, DARK_DANGER_COLOR
        ).replace(f"color: {DARK_TEXT_PRIMARY}", "color: white;")
        self.remove_horse_owner_btn.setStyleSheet(remove_owner_style)
        self.create_link_owner_btn.setEnabled(False)
        self.link_existing_owner_btn.setEnabled(False)
        self.remove_horse_owner_btn.setEnabled(False)
        owners_action_layout.addWidget(self.create_link_owner_btn)
        owners_action_layout.addWidget(self.link_existing_owner_btn)
        owners_action_layout.addWidget(self.remove_horse_owner_btn)
        owners_action_layout.addStretch()
        owners_layout.addLayout(owners_action_layout)
        self.current_owners_list_widget = HorseOwnerListWidget()
        self.current_owners_list_widget.itemSelectionChanged.connect(
            self.on_horse_owner_selection_changed
        )
        owners_list_label = QLabel("Current Owners & Percentages:")
        owners_list_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; background: transparent; margin-bottom: 5px; font-weight: bold;"
        )
        owners_layout.addWidget(owners_list_label)
        owners_layout.addWidget(self.current_owners_list_widget, 1)
        self.percentage_edit_frame = QFrame()
        self.percentage_edit_frame.setStyleSheet("background-color: transparent;")
        percentage_edit_layout = QHBoxLayout(self.percentage_edit_frame)
        percentage_edit_layout.setContentsMargins(0, 5, 0, 0)
        self.selected_owner_for_pct_label = QLabel("Edit % for:")
        self.selected_owner_for_pct_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY};"
        )
        self.edit_owner_percentage_spinbox = QDoubleSpinBox()
        self.edit_owner_percentage_spinbox.setRange(0.01, 100.00)
        self.edit_owner_percentage_spinbox.setDecimals(2)
        self.edit_owner_percentage_spinbox.setSuffix(" %")
        self.edit_owner_percentage_spinbox.setStyleSheet(self.get_form_input_style())
        self.save_owner_percentage_btn = QPushButton("💾 Save %")
        self.save_owner_percentage_btn.setStyleSheet(
            self.get_generic_button_style().replace(DARK_BUTTON_BG, DARK_SUCCESS_COLOR)
        )
        percentage_edit_layout.addWidget(self.selected_owner_for_pct_label)
        percentage_edit_layout.addWidget(self.edit_owner_percentage_spinbox)
        percentage_edit_layout.addWidget(self.save_owner_percentage_btn)
        percentage_edit_layout.addStretch()
        owners_layout.addWidget(self.percentage_edit_frame)
        self.percentage_edit_frame.hide()
        self.tab_widget.addTab(self.owners_tab_widget, "👥 Owners")
        self.logger.debug("setup_owners_tab finished.")

    def get_form_input_style(self, base_bg=DARK_WIDGET_BACKGROUND):  # Unchanged
        return f""" QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{ background-color: {base_bg}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 10px; font-size: 13px; }} QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION_LIGHT}; }} QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QDoubleSpinBox:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }} QComboBox::drop-down {{ border: none; background-color: transparent; width: 15px; }} QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY}; }} QDateEdit::up-button, QDateEdit::down-button {{ width: 18px; }} QComboBox QAbstractItemView {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_PRIMARY_ACTION_LIGHT}; selection-color: white; }} """

    def setup_footer(self, parent_layout):  # Unchanged
        self.logger.debug("setup_footer started.")
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_SECONDARY}; border: none; border-top: 1px solid {DARK_BORDER}; padding: 0 15px; font-size: 11px; }} QStatusBar::item {{ border: none; }} QLabel {{ color: {DARK_TEXT_SECONDARY}; background: transparent; font-size: 11px; }}"
        )
        parent_layout.addWidget(self.status_bar)
        self.status_label = QLabel("Ready")
        self.footer_horse_count_label = QLabel("Showing 0 of 0 horses")
        self.shortcut_label = QLabel("F5=Refresh")
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.footer_horse_count_label)
        separator_label = QLabel(" | ")
        separator_label.setStyleSheet(
            f"color: {DARK_BORDER}; background: transparent; margin: 0 5px;"
        )
        self.status_bar.addPermanentWidget(separator_label)
        self.status_bar.addPermanentWidget(self.shortcut_label)
        self.logger.debug("setup_footer finished.")

    def get_toolbar_button_style(self, bg_color, text_color="white"):  # Unchanged
        if len(bg_color) == 4 and bg_color.startswith("#"):
            bg_color = f"#{bg_color[1]*2}{bg_color[2]*2}{bg_color[3]*2}"
        hover_bg = bg_color
        pressed_bg = bg_color
        try:
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            hover_bg = f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
            pressed_bg = f"#{max(0,r-40):02x}{max(0,g-40):02x}{max(0,b-40):02x}"
        except ValueError:
            self.logger.warning(f"Could not parse color for hover/pressed: {bg_color}")
        return f"QPushButton {{ background-color: {bg_color}; color: {text_color}; border: none; border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: 500; }} QPushButton:hover {{ background-color: {hover_bg}; }} QPushButton:pressed {{ background-color: {pressed_bg}; }} QPushButton:disabled {{ background-color: #adb5bd; color: #f8f9fa; }}"

    def get_generic_button_style(self):  # Unchanged
        return f"QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px; }} QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"

    def load_initial_data(self):  # Unchanged
        self.logger.debug("load_initial_data started.")
        self.load_horses()
        self.update_status("Initialization complete. Ready.")
        self.logger.info("Initial data loaded.")

    def load_horses(self):  # Unchanged
        try:
            search_term = self.search_input.text()
            status_filter = "active"
            if self.all_horses_radio.isChecked():
                status_filter = "all"
            elif self.deactivated_radio.isChecked():
                status_filter = "inactive"
            self.logger.info(
                f"Loading horses (Status: {status_filter}, Search: '{search_term}')"
            )
            selected_id_before_load = (
                self.current_horse.horse_id if self.current_horse else None
            )
            self.horses_list = self.horse_controller.search_horses(
                search_term, status=status_filter
            )
            self.populate_horse_list()
            reselected_item = None
            if selected_id_before_load:
                for i in range(self.horse_list.count()):
                    item = self.horse_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == selected_id_before_load:
                        self.horse_list.setCurrentItem(item)
                        reselected_item = item
                        break
            if not reselected_item and self.horse_list.count() > 0:
                self.horse_list.setCurrentRow(0)
            elif not self.horses_list:
                self.display_empty_state()
            self.update_status(f"Loaded {len(self.horses_list)} horses.")
        except Exception as e:
            self.logger.error(f"Error loading horses: {e}", exc_info=True)
            self.show_error("Load Error", f"Failed to load horse list: {e}")
            self.horses_list = []
            self.populate_horse_list()
            self.display_empty_state()

    def populate_horse_list(self):  # Unchanged
        self.horse_list.clear()
        self.logger.debug(f"Populating list with {len(self.horses_list)} horses.")
        for horse in self.horses_list:
            item = QListWidgetItem()
            item_widget = self.create_horse_list_item_widget(horse)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, horse.horse_id)
            self.horse_list.addItem(item)
            self.horse_list.setItemWidget(item, item_widget)
        count_text = (
            f"Showing {self.horse_list.count()} of {len(self.horses_list)} horses"
        )
        self.footer_horse_count_label.setText(count_text)
        self.logger.debug("Horse list population complete.")

    def create_horse_list_item_widget(self, horse):  # Unchanged
        widget = QWidget()
        widget.setStyleSheet(
            f"background-color: transparent; border: none; color: {DARK_TEXT_PRIMARY};"
        )
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(2)
        name_label = QLabel(horse.horse_name or "Unnamed Horse")
        name_label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold))
        name_label.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; background: transparent;"
        )
        acc_breed_text = (
            f"Acct: {horse.account_number or 'N/A'} | {horse.breed or 'N/A'}"
        )
        info_label = QLabel(acc_breed_text)
        info_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        details_text = f"{horse.color or '?'} | {horse.sex or '?'}"
        details_label = QLabel(details_text)
        details_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        location_text = horse.location.location_name if horse.location else "N/A"
        location_label = QLabel(f"📍 {location_text}")
        location_label.setStyleSheet(
            f"color: {DARK_TEXT_TERTIARY}; font-size: 10px; background: transparent;"
        )
        layout.addWidget(name_label)
        layout.addWidget(info_label)
        layout.addWidget(details_label)
        layout.addWidget(location_label)
        layout.addStretch()
        return widget

    def calculate_age(self, birth_date):  # Unchanged
        if not birth_date or not isinstance(birth_date, date):
            return "Age N/A"
        try:
            today = date.today()
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
            return f"{age} yr" if age == 1 else f"{age} yrs"
        except Exception:
            self.logger.warning(f"Could not calculate age for date: {birth_date}")
            return "Age Error"

    def load_locations_combo(self, combo_widget):  # Unchanged
        if not isinstance(combo_widget, QComboBox):
            self.logger.warning("Invalid widget passed to load_locations_combo.")
            return
        try:
            current_data = combo_widget.currentData()
            combo_widget.blockSignals(True)
            combo_widget.clear()
            combo_widget.addItem("", None)
            locations = self.horse_controller.get_locations_list()
            self.logger.debug(f"Loading {len(locations)} locations into combo box.")
            for location in locations:
                combo_widget.addItem(location.location_name, location.location_id)
            index = combo_widget.findData(current_data)
            combo_widget.setCurrentIndex(index if index != -1 else 0)
        except Exception as e:
            self.logger.error(f"Error loading locations combo: {e}", exc_info=True)
            self.show_error("Load Error", "Failed to load locations.")
        finally:
            combo_widget.blockSignals(False)

    def on_search_text_changed(self):  # Unchanged
        self.search_timer.stop()
        self.search_timer.start(350)
        self.logger.debug("Search timer started/restarted.")

    def perform_search(self):  # Unchanged
        self.logger.info("Performing search...")
        self.load_horses()

    def on_filter_changed(self):  # Unchanged
        sender = self.sender()
        if isinstance(sender, QRadioButton) and sender.isChecked():
            self.logger.info(
                f"Filter changed. Active: {self.active_only_radio.isChecked()}, Deactivated: {self.deactivated_radio.isChecked()}, All: {self.all_horses_radio.isChecked()}"
            )
            self.load_horses()

    def on_selection_changed(self):  # Unchanged (main horse list)
        selected_items = self.horse_list.selectedItems()
        newly_selected_horse_id = None
        if selected_items:
            newly_selected_horse_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        current_horse_id = self.current_horse.horse_id if self.current_horse else None
        if (
            newly_selected_horse_id == current_horse_id
            and self.horse_details_content_widget.isVisible()
        ):
            self.logger.debug(
                "Selection changed event, but selected horse is the same and details visible."
            )
            return
        if self.has_changes:
            reply = self.show_question(
                "Unsaved Changes",
                "You have unsaved changes on the current horse. Discard and load selected horse?",
            )
            if not reply:
                self.horse_list.blockSignals(True)
                for i in range(self.horse_list.count()):
                    item = self.horse_list.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == current_horse_id:
                        self.horse_list.setCurrentRow(i)
                        break
                self.horse_list.blockSignals(False)
                return
        if newly_selected_horse_id is not None:
            self.logger.info(f"Horse selected: ID {newly_selected_horse_id}")
            self.load_horse_details(newly_selected_horse_id)
        else:
            self.logger.info("Horse selection cleared.")
            self.display_empty_state()

    def on_field_changed(self):  # Unchanged (main horse form)
        if self.horse_details_content_widget.isVisible():
            if not self.has_changes:
                self.logger.debug("Change detected in horse detail form.")
                self.has_changes = True
                self.update_action_button_states()

    def on_horse_owner_selection_changed(self):  # Unchanged
        selected_items = self.current_owners_list_widget.selectedItems()
        if selected_items:
            self.selected_horse_owner_id = selected_items[0].data(
                Qt.ItemDataRole.UserRole
            )
            self.logger.info(
                f"Horse-owner selected: Owner ID {self.selected_horse_owner_id}"
            )
            for owner_assoc in self.current_horse_owners:
                if owner_assoc["owner_id"] == self.selected_horse_owner_id:
                    self.selected_owner_for_pct_label.setText(
                        f"Edit % for: {owner_assoc['display_name']}"
                    )
                    self.edit_owner_percentage_spinbox.setValue(
                        owner_assoc["percentage"]
                    )
                    self.percentage_edit_frame.show()
                    break
        else:
            self.selected_horse_owner_id = None
            self.percentage_edit_frame.hide()
            self.logger.info("Horse-owner selection cleared.")
        self.update_horse_owner_buttons_state()

    def add_new_horse(self):  # Unchanged
        proceed_with_add = True
        if self.has_changes:
            reply = self.show_question(
                "Unsaved Changes", "Discard unsaved changes and start new horse?"
            )
            if not reply:
                proceed_with_add = False
        if not proceed_with_add:
            return
        self.logger.info("Initiating add new horse.")
        self.current_horse = None
        self.horse_list.clearSelection()
        self.current_owners_list_widget.clear()
        self.update_horse_owner_buttons_state()
        for field in self.form_fields.values():
            field.blockSignals(True)
        for field_name, field in self.form_fields.items():
            if isinstance(field, QLineEdit):
                field.clear()
            elif isinstance(field, QComboBox):
                field.setCurrentIndex(0)
            elif isinstance(field, QDateEdit):
                field.setDate(QDate())
        for field in self.form_fields.values():
            field.blockSignals(False)
        self.horse_title.setText("New Horse Record")
        self.horse_info_line.setText("Enter horse details below")
        self.display_details_state()
        self.tab_widget.setCurrentIndex(0)
        self.form_fields["horse_name"].setFocus()
        self.has_changes = True
        self.update_action_button_states()
        self.update_status("Enter details for the new horse.")

    def edit_selected_horse(self):  # Unchanged
        if self.current_horse:
            self.logger.info(
                f"Enabling edit for horse: {self.current_horse.horse_name}"
            )
            self.display_details_state()
            self.tab_widget.setCurrentIndex(0)
            self.form_fields["horse_name"].setFocus()
            self.update_status(f"Editing: {self.current_horse.horse_name}")
        else:
            self.show_info("Edit Horse", "Please select a horse from the list to edit.")

    def delete_selected_horse(self):  # Unchanged
        self.logger.warning(
            "delete_selected_horse was called, but is deprecated. Use form's Activate/Deactivate button."
        )
        if self.current_horse:
            self.handle_toggle_active_status()
        else:
            self.show_info(
                "Deactivate Horse", "Please select a horse to deactivate via the form."
            )

    def save_changes(self):  # Meticulously reviewed for SyntaxError
        if not self.has_changes:
            self.update_status("No changes to save.")
            return

        is_new_horse = self.current_horse is None
        self.logger.info(f"Attempting to save changes... New horse: {is_new_horse}")

        try:
            date_field = self.form_fields["date_of_birth"]
            birth_date = (
                date_field.date().toPython() if date_field.date().isValid() else None
            )
            if birth_date and not isinstance(birth_date, date):
                raise ValueError("Date conversion failed.")
            horse_data = {
                "horse_name": self.form_fields["horse_name"].text().strip(),
                "account_number": self.form_fields["account_number"].text().strip(),
                "breed": self.form_fields["breed"].text().strip(),
                "color": self.form_fields["color"].text().strip(),
                "sex": self.form_fields["sex"].currentText() or None,
                "date_of_birth": birth_date,
                "registration_number": self.form_fields["registration_number"]
                .text()
                .strip(),
                "microchip_id": self.form_fields["microchip_id"].text().strip(),
                "tattoo": self.form_fields["tattoo"].text().strip(),
                "brand": self.form_fields["brand"].text().strip(),
                "band_tag_number": self.form_fields["band_tag_number"].text().strip(),
                "current_location_id": self.form_fields[
                    "current_location_id"
                ].currentData(),
            }
            self.logger.debug(f"Collected horse data: {horse_data}")
        except Exception as e:
            self.logger.error(f"Error collecting form data: {e}", exc_info=True)
            self.show_error("Data Error", f"Error reading form data: {e}")
            return

        is_valid, errors = self.horse_controller.validate_horse_data(horse_data)
        if not is_valid:
            error_message = "Please correct the following errors:\n\n- " + "\n- ".join(
                errors
            )
            self.show_warning("Validation Error", error_message)
            return

        try:
            saved_horse_id = None
            success = False
            message = ""

            if not is_new_horse and self.current_horse:
                self.logger.info(f"Updating horse ID: {self.current_horse.horse_id}")
                op_success, op_message = self.horse_controller.update_horse(
                    self.current_horse.horse_id, horse_data, self.current_user
                )
                success = op_success
                message = op_message
                if success:
                    saved_horse_id = self.current_horse.horse_id
            else:  # This is for new horse creation
                self.logger.info("Creating new horse.")
                op_success, op_message, new_horse_obj = (
                    self.horse_controller.create_horse(horse_data, self.current_user)
                )
                success = op_success
                message = op_message
                if success and new_horse_obj:
                    saved_horse_id = new_horse_obj.horse_id
                    self.logger.info(f"New horse created with ID: {saved_horse_id}")

            # This is the critical if/else block
            if success:
                self.show_info("Success", message)
                self.has_changes = False
                self.load_horses()
                if saved_horse_id:
                    for i in range(self.horse_list.count()):
                        if (
                            self.horse_list.item(i).data(Qt.ItemDataRole.UserRole)
                            == saved_horse_id
                        ):
                            self.horse_list.setCurrentRow(i)
                            break
                self.update_status(
                    f"Saved: {horse_data.get('horse_name', 'Unknown Horse')}"
                )
            else:
                # Ensure message is not None before using it in show_error
                error_display_message = (
                    message if message else "An unknown error occurred during save."
                )
                self.show_error("Save Failed", error_display_message)

        except Exception as e:
            self.logger.error(f"Exception during save operation: {e}", exc_info=True)
            self.show_error(
                "Save Error", f"An unexpected error occurred during save: {e}"
            )

    def discard_changes(self):  # Unchanged
        if not self.has_changes:
            return
        self.logger.info("Discarding changes...")
        reply = self.show_question("Confirm Discard", "Discard all unsaved changes?")
        if reply:
            if self.current_horse:
                self.load_horse_details(self.current_horse.horse_id)
            else:
                self.display_empty_state()
            self.update_status("Changes discarded.")
        else:
            self.logger.info("User cancelled discard.")

    def refresh_data(self):  # Unchanged
        if self.has_changes:
            reply = self.show_question(
                "Unsaved Changes", "Discard unsaved changes and refresh data?"
            )
        if not reply:
            return
        self.logger.info("Refreshing data...")
        self.load_horses()
        self.update_status("Data refreshed.")

    def show_help(self):  # Unchanged
        help_text = "<style> ul {margin-left:20px;} li {margin-bottom:5px;} b {color:#e0e0e0;} </style><b>Horse Management Help</b><hr><p>Manage horse records using this screen.</p><ul><li><b>List (Left):</b> Shows horses. Click to select.</li><li><b>Details (Right):</b> View/edit selected horse info.</li><li><b>Action Bar:</b> Add, Edit, Filter, Search.</li><li><b>Tabs:</b> Different information categories.</li><li><b>Save/Discard/Toggle Active:</b> Appear in the form when changes are made or horse selected.</li></ul><b>Keyboard Shortcuts:</b><ul><li><b>F1:</b> This help</li><li><b>F5:</b> Refresh data</li><li><b>Ctrl+N:</b> Add New Horse</li><li><b>Ctrl+S:</b> Save Changes</li><li><b>Esc:</b> Exit Screen</li></ul>"
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help - Horse Management")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setPalette(self.palette())
        msg_box.exec()

    def load_horse_details(self, horse_id: int):  # Unchanged
        self.logger.info(f"Loading details for horse ID: {horse_id}")
        try:
            horse = self.horse_controller.get_horse_by_id(horse_id)
            if not horse:
                self.show_error("Error", f"Could not load horse with ID {horse_id}.")
                self.display_empty_state()
                return
            self.current_horse = horse
            self.horse_title.setText(horse.horse_name or "Unnamed Horse")
            age_str = self.calculate_age(horse.date_of_birth)
            info_text = f"Account: {horse.account_number or 'N/A'} | Breed: {horse.breed or 'N/A'} | Color: {horse.color or 'N/A'} | Sex: {horse.sex or 'N/A'} | Age: {age_str}"
            self.horse_info_line.setText(info_text)
            for field in self.form_fields.values():
                field.blockSignals(True)
            self.form_fields["horse_name"].setText(horse.horse_name or "")
            self.form_fields["account_number"].setText(horse.account_number or "")
            self.form_fields["breed"].setText(horse.breed or "")
            self.form_fields["color"].setText(horse.color or "")
            sex_combo = self.form_fields["sex"]
            sex_index = sex_combo.findText(
                horse.sex or "", Qt.MatchFlag.MatchFixedString
            )
            sex_combo.setCurrentIndex(sex_index if sex_index >= 0 else 0)
            dob_field = self.form_fields["date_of_birth"]
            if horse.date_of_birth and isinstance(horse.date_of_birth, date):
                dob_field.setDate(QDate(horse.date_of_birth))
            else:
                dob_field.setDate(QDate())
            self.form_fields["registration_number"].setText(
                horse.registration_number or ""
            )
            self.form_fields["microchip_id"].setText(horse.microchip_id or "")
            self.form_fields["tattoo"].setText(horse.tattoo or "")
            self.form_fields["brand"].setText(horse.brand or "")
            self.form_fields["band_tag_number"].setText(horse.band_tag_number or "")
            loc_combo = self.form_fields["current_location_id"]
            if loc_combo.count() <= 1:
                self.load_locations_combo(loc_combo)
            loc_index = loc_combo.findData(horse.current_location_id)
            loc_combo.setCurrentIndex(loc_index if loc_index >= 0 else 0)
            for field in self.form_fields.values():
                field.blockSignals(False)
            if horse.is_active:
                self.toggle_active_btn.setText("Deactivate Horse")
                self.toggle_active_btn.setStyleSheet(
                    self.get_toolbar_button_style(
                        DARK_WARNING_COLOR, text_color="black"
                    )
                )
                self.toggle_active_btn.setToolTip("Mark this horse as inactive.")
            else:
                self.toggle_active_btn.setText("Activate Horse")
                self.toggle_active_btn.setStyleSheet(
                    self.get_toolbar_button_style(DARK_SUCCESS_COLOR)
                )
                self.toggle_active_btn.setToolTip("Mark this horse as active.")
            self.populate_horse_owners_list(horse_id)
            self.display_details_state()
            self.has_changes = False
            self.update_action_button_states()
            self.update_status(
                f"Viewing: {horse.horse_name} (Status: {'Active' if horse.is_active else 'Inactive'})"
            )
        except Exception as e:
            self.logger.error(
                f"Error loading horse details for ID {horse_id}: {e}", exc_info=True
            )
            self.show_error("Load Error", f"Failed to load horse details: {e}")
            self.display_empty_state()

    def populate_horse_owners_list(self, horse_id: Optional[int]):  # Unchanged
        self.current_owners_list_widget.clear()
        self.selected_horse_owner_id = None
        if horse_id is None:
            self.current_horse_owners = []
        else:
            self.current_horse_owners = self.horse_controller.get_horse_owners(horse_id)
        self.logger.debug(
            f"Populating owners list for horse ID {horse_id} with {len(self.current_horse_owners)} owners."
        )
        for owner_assoc in self.current_horse_owners:
            item_text = (
                f"{owner_assoc['display_name']} - {owner_assoc['percentage']:.2f}%"
            )
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, owner_assoc["owner_id"])
            self.current_owners_list_widget.addItem(list_item)
        self.update_horse_owner_buttons_state()

    def display_empty_state(self):  # Unchanged
        self.logger.debug("Displaying empty state.")
        self.empty_frame.show()
        self.horse_details_content_widget.hide()
        self.current_horse = None
        self.has_changes = False
        if hasattr(self, "current_owners_list_widget"):
            self.current_owners_list_widget.clear()
        self.update_action_button_states()
        self.update_horse_owner_buttons_state()

    def display_details_state(self):  # Unchanged
        self.logger.debug("Displaying details state.")
        self.empty_frame.hide()
        self.horse_details_content_widget.show()

    def update_status(self, message, timeout=4000):  # Unchanged
        self.logger.debug(f"Status update: {message}")
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.clear_status_if_matches(message))

    def clear_status_if_matches(self, original_message):  # Unchanged
        if self.status_label.text() == original_message:
            self.status_label.setText("Ready")

    def update_action_button_states(self):  # Unchanged
        is_horse_selected = self.current_horse is not None
        form_is_visible_for_new = (
            self.current_horse is None and self.horse_details_content_widget.isVisible()
        )
        can_save_or_discard = self.has_changes and (
            is_horse_selected or form_is_visible_for_new
        )
        self.save_btn.setEnabled(can_save_or_discard)
        self.discard_btn.setEnabled(can_save_or_discard)
        self.toggle_active_btn.setEnabled(is_horse_selected)
        self.edit_horse_btn.setEnabled(is_horse_selected)
        self.add_horse_btn.setEnabled(True)
        self.update_horse_owner_buttons_state()
        self.logger.debug(
            f"Action button states updated. HasChanges: {self.has_changes}, HorseSelected: {is_horse_selected}, FormVisibleForNew: {form_is_visible_for_new}"
        )

    def update_horse_owner_buttons_state(self):  # Unchanged
        is_horse_selected = self.current_horse is not None
        is_owner_in_list_selected = self.selected_horse_owner_id is not None
        if hasattr(self, "create_link_owner_btn"):
            self.create_link_owner_btn.setEnabled(is_horse_selected)
            self.link_existing_owner_btn.setEnabled(is_horse_selected)
            self.remove_horse_owner_btn.setEnabled(
                is_horse_selected and is_owner_in_list_selected
            )
            self.save_owner_percentage_btn.setEnabled(
                is_horse_selected and is_owner_in_list_selected
            )

    def handle_toggle_active_status(self):  # Unchanged
        if not self.current_horse:
            self.logger.warning("Toggle active status called, but no current horse.")
            return
        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )
        action_text = "activate" if not self.current_horse.is_active else "deactivate"
        reply = self.show_question(
            f"Confirm {action_text.capitalize()}",
            f"Are you sure you want to {action_text} '{horse_name_display}'?",
        )
        if reply:
            self.logger.info(
                f"User confirmed to {action_text} horse ID: {self.current_horse.horse_id}"
            )
            try:
                if self.current_horse.is_active:
                    success, message = self.horse_controller.deactivate_horse(
                        self.current_horse.horse_id, self.current_user
                    )
                else:
                    success, message = self.horse_controller.activate_horse(
                        self.current_horse.horse_id, self.current_user
                    )
                if success:
                    self.show_info(f"Horse Status Changed", message)
                    self.load_horse_details(self.current_horse.horse_id)
                    self.load_horses()
                    self.update_status(message)
                else:
                    self.show_error(f"{action_text.capitalize()} Failed", message)
            except Exception as e:
                self.logger.error(
                    f"Exception during toggle active status: {e}", exc_info=True
                )
                self.show_error("Operation Error", f"An unexpected error occurred: {e}")
        else:
            self.logger.info(f"User cancelled {action_text} action.")

    def exit_application(self):  # Unchanged
        self.logger.info("Exit requested.")
        if self.has_changes:
            reply = self.show_question(
                "Unsaved Changes", "Discard unsaved changes and exit?"
            )
        if not reply:
            self.logger.info("Exit cancelled due to unsaved changes.")
            return
        self.logger.info("Emitting exit_requested signal.")
        self.exit_requested.emit()

    def keyPressEvent(self, event):  # Unchanged
        key = event.key()
        modifiers = event.modifiers()
        self.logger.debug(f"KeyPressEvent: Key={key}, Modifiers={modifiers}")
        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            if self.add_horse_btn.isEnabled():
                self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            if self.save_btn.isEnabled():
                self.save_changes()
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            self.exit_application()
        else:
            super().keyPressEvent(event)

    def setup_connections(self):  # Unchanged
        self.logger.debug("setup_connections started.")
        self.add_horse_btn.clicked.connect(self.add_new_horse)
        self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.help_btn.clicked.connect(self.show_help)
        self.setup_icon_btn.clicked.connect(self.handle_setup_icon_click)
        self.active_only_radio.toggled.connect(self.on_filter_changed)
        self.all_horses_radio.toggled.connect(self.on_filter_changed)
        self.deactivated_radio.toggled.connect(self.on_filter_changed)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.save_btn.clicked.connect(self.save_changes)
        self.discard_btn.clicked.connect(self.discard_changes)
        self.toggle_active_btn.clicked.connect(self.handle_toggle_active_status)
        if hasattr(self, "create_link_owner_btn"):
            self.create_link_owner_btn.clicked.connect(
                self.handle_create_and_link_owner
            )
        if hasattr(self, "link_existing_owner_btn"):
            self.link_existing_owner_btn.clicked.connect(
                self.handle_link_existing_owner
            )
        if hasattr(self, "remove_horse_owner_btn"):
            self.remove_horse_owner_btn.clicked.connect(
                self.handle_remove_owner_from_horse
            )
        if hasattr(self, "save_owner_percentage_btn"):
            self.save_owner_percentage_btn.clicked.connect(
                self.handle_save_owner_percentage
            )
        self.logger.debug("Signal connections established.")

    def handle_setup_icon_click(self):  # Unchanged
        self.logger.info("Setup icon clicked, emitting setup_requested signal.")
        self.setup_requested.emit()

    def handle_create_and_link_owner(self):  # Unchanged
        if not self.current_horse:
            self.show_warning("Add Owner", "Please select a horse first.")
            return
        dialog = CreateAndLinkOwnerDialog(self, self.current_horse.horse_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                owner_details = data["owner_details"]
                percentage = data["percentage"]
                self.logger.info(
                    f"Attempting to create new master owner: {owner_details.get('owner_name')}"
                )
                create_success, create_message, new_owner_obj = (
                    self.owner_controller.create_master_owner(
                        owner_details, self.current_user
                    )
                )
                if create_success and new_owner_obj:
                    self.show_info("Master Owner Created", create_message)
                    self.logger.info(
                        f"Attempting to link new owner ID {new_owner_obj.owner_id} with {percentage}% to horse ID {self.current_horse.horse_id}"
                    )
                    link_success, link_message = (
                        self.horse_controller.add_owner_to_horse(
                            self.current_horse.horse_id,
                            new_owner_obj.owner_id,
                            percentage,
                            self.current_user,
                        )
                    )
                    if link_success:
                        self.show_info("Owner Linked to Horse", link_message)
                        self.populate_horse_owners_list(self.current_horse.horse_id)
                    else:
                        self.show_error("Failed to Link Owner", link_message)
                else:
                    self.show_error("Failed to Create Master Owner", create_message)
        else:
            self.logger.info("Create and link owner dialog cancelled.")

    def handle_link_existing_owner(self):  # Unchanged
        if not self.current_horse:
            self.show_warning("Link Existing Owner", "Please select a horse first.")
            return
        dialog = LinkExistingOwnerDialog(self, self.current_horse.horse_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                owner_id = data["owner_id"]
                percentage = data["percentage"]
                self.logger.info(
                    f"Attempting to link existing owner ID {owner_id} with {percentage}% to horse ID {self.current_horse.horse_id}"
                )
                success, message = self.horse_controller.add_owner_to_horse(
                    self.current_horse.horse_id, owner_id, percentage, self.current_user
                )
                if success:
                    self.show_info("Owner Linked", message)
                    self.populate_horse_owners_list(self.current_horse.horse_id)
                else:
                    self.show_error("Failed to Link Owner", message)
        else:
            self.logger.info("Link existing owner dialog cancelled.")

    def handle_remove_owner_from_horse(self):  # Unchanged
        if not self.current_horse or self.selected_horse_owner_id is None:
            self.show_warning(
                "Remove Owner",
                "Please select a horse and then an owner from its list to remove.",
            )
            return
        owner_display_name = "Selected Owner"
        for item_data in self.current_horse_owners:
            if item_data["owner_id"] == self.selected_horse_owner_id:
                owner_display_name = item_data["display_name"]
                break
        reply = self.show_question(
            "Confirm Removal",
            f"Are you sure you want to remove owner '{owner_display_name}' from horse '{self.current_horse.horse_name}'?",
        )
        if reply:
            self.logger.info(
                f"Attempting to remove owner ID {self.selected_horse_owner_id} from horse ID {self.current_horse.horse_id}"
            )
            success, message = self.horse_controller.remove_owner_from_horse(
                self.current_horse.horse_id,
                self.selected_horse_owner_id,
                self.current_user,
            )
            if success:
                self.show_info("Owner Removed", message)
                self.populate_horse_owners_list(self.current_horse.horse_id)
            else:
                self.show_error("Failed to Remove Owner", message)
        else:
            self.logger.info("Remove owner from horse cancelled.")

    def handle_save_owner_percentage(self):  # Unchanged
        if not self.current_horse or self.selected_horse_owner_id is None:
            self.show_warning(
                "Save Percentage", "No horse or owner selected to update percentage."
            )
            return

        new_percentage = self.edit_owner_percentage_spinbox.value()
        if not (0 < new_percentage <= 100):
            self.show_error(
                "Invalid Percentage",
                "Ownership percentage must be between 0 (exclusive) and 100.",
            )
            for owner_assoc in self.current_horse_owners:
                if owner_assoc["owner_id"] == self.selected_horse_owner_id:
                    self.edit_owner_percentage_spinbox.setValue(
                        owner_assoc["percentage"]
                    )
                    break
            return

        self.logger.info(
            f"Attempting to update percentage for owner ID {self.selected_horse_owner_id} on horse ID {self.current_horse.horse_id} to {new_percentage}%"
        )
        success, message = self.horse_controller.update_horse_owner_percentage(
            self.current_horse.horse_id,
            self.selected_horse_owner_id,
            new_percentage,
            self.current_user,
        )
        if success:
            self.show_info("Percentage Updated", message)
            self.populate_horse_owners_list(self.current_horse.horse_id)
        else:
            self.show_error("Update Failed", message)
            for owner_assoc in self.current_horse_owners:
                if owner_assoc["owner_id"] == self.selected_horse_owner_id:
                    self.edit_owner_percentage_spinbox.setValue(
                        owner_assoc["percentage"]
                    )
                    break
