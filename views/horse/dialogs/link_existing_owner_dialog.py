# views/horse/dialogs/link_existing_owner_dialog.py

"""
EDSI Veterinary Management System - Link Existing Owner Dialog
Version: 1.0.2
Purpose: Dialog to search for an existing owner and link them to a horse.
         Allows 0% ownership.
Last Updated: May 17, 2025
Author: Claude Assistant

Changelog:
- v1.0.2 (2025-05-17):
    - Changed percentage_spinbox minimum to 0.00 to allow 0% ownership.
    - Updated percentage validation in `get_data` to allow 0%.
- v1.0.1 (2025-05-17):
    - Imported HorseOwnerListWidget from ..widgets for consistent styling.
- v1.0.0 (2025-05-16): Initial extraction. Used temporary style.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QDoubleSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from config.app_config import AppConfig
from controllers.owner_controller import OwnerController
from ..widgets.horse_owner_list_widget import HorseOwnerListWidget


class LinkExistingOwnerDialog(QDialog):
    """Dialog to link an existing owner to a horse."""

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
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        self.setStyleSheet(
            f"QLabel {{ color: {AppConfig.DARK_TEXT_SECONDARY}; background-color:transparent; padding-top:3px;}}"
        )
        input_style = self.parent_screen.get_form_input_style()
        list_widget_style = HorseOwnerListWidget().styleSheet()

        search_layout = QHBoxLayout()
        search_label = QLabel("Search Existing Owner:")
        self.owner_search_input = QLineEdit()
        self.owner_search_input.setPlaceholderText("Name or Account #")
        self.owner_search_input.setStyleSheet(input_style)
        self.owner_search_input.textChanged.connect(self.search_owners)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.owner_search_input, 1)
        layout.addLayout(search_layout)

        self.owner_results_list = QListWidget()
        self.owner_results_list.setStyleSheet(list_widget_style)
        self.owner_results_list.setFixedHeight(150)
        self.owner_results_list.itemClicked.connect(self.on_owner_selected_from_search)
        layout.addWidget(self.owner_results_list)

        self.selected_owner_display = QLineEdit()
        self.selected_owner_display.setPlaceholderText("No owner selected")
        self.selected_owner_display.setReadOnly(True)
        self.selected_owner_display.setStyleSheet(
            input_style
            + f"QLineEdit:read-only {{ background-color: #404040; color: {AppConfig.DARK_TEXT_TERTIARY}; }}"
        )
        layout.addWidget(QLabel(f"Selected Owner (to link to {self.horse_name}):"))
        layout.addWidget(self.selected_owner_display)

        percentage_layout = QHBoxLayout()
        percentage_label = QLabel("Ownership Percentage (%):*")
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setRange(0.00, 100.00)  # Allow 0.00
        self.percentage_spinbox.setDecimals(2)
        self.percentage_spinbox.setValue(100.00)  # Default to 100
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setStyleSheet(input_style)
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

        generic_button_style = self.parent_screen.get_generic_button_style()
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(generic_button_style)
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
                    .replace(AppConfig.DARK_BUTTON_BG, ok_bg_color)
                    .replace(f"color: {AppConfig.DARK_TEXT_PRIMARY}", "color: white;")
                )
        layout.addWidget(self.button_box)
        self.search_owners()

    def search_owners(self):
        search_term = self.owner_search_input.text()
        owners = self.owner_controller.get_all_owners_for_lookup(search_term)
        self.owner_results_list.clear()
        for o_data in owners:
            item = QListWidgetItem(o_data["name_account"])
            item.setData(Qt.ItemDataRole.UserRole, o_data["id"])
            self.owner_results_list.addItem(item)
        self.selected_owner_id = None
        self.selected_owner_display.clear()
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def on_owner_selected_from_search(self, item: QListWidgetItem):
        self.selected_owner_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_owner_display.setText(item.text())
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def get_data(self) -> Optional[dict]:
        if self.result() != QDialog.DialogCode.Accepted:
            return None
        if self.selected_owner_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select an owner.")
            return None
        percentage = self.percentage_spinbox.value()
        if not (0 <= percentage <= 100):  # Allow 0%
            QMessageBox.warning(
                self, "Input Error", "Ownership percentage must be between 0 and 100."
            )
            return None
        return {"owner_id": self.selected_owner_id, "percentage": percentage}
