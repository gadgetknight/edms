# views/horse/dialogs/select_existing_location_dialog.py
"""
EDSI Veterinary Management System - Select Existing Location Dialog
Version: 1.0.0
Purpose: Dialog for searching and selecting an existing active location.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-05-20):
    - Initial implementation.
    - UI with search input (QLineEdit) and results list (QListWidget).
    - Fetches active locations using LocationController.
    - Search functionality filters locations by name (case-insensitive).
    - "Select Location" (OK) button enabled only when a location is selected.
    - Provides get_selected_location_id() method.
    - Styled for dark theme.
"""

import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QApplication,  # For clipboard
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QTimer

from controllers.location_controller import LocationController
from models import Location as LocationModel  # Import the model

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


class SelectExistingLocationDialog(QDialog):
    """Dialog to search and select an existing active location."""

    def __init__(self, parent_view, horse_name: str):
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse_name = horse_name
        self.location_controller = LocationController()
        self.all_active_locations: List[LocationModel] = []
        self.selected_location_id: Optional[int] = None

        self.setWindowTitle(f"Select Location for {self.horse_name}")
        self.setMinimumWidth(450)
        self.setMinimumHeight(350)

        self._setup_palette()
        self._setup_ui()
        self._load_initial_locations()

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_locations_list)

    def _get_dialog_specific_input_field_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px; min-height: 20px;
            }}
            QLineEdit:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
        """

    def _get_dialog_generic_button_style(self) -> str:
        return (
            f"QPushButton {{background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; "
            f"font-size: 12px; font-weight: 500; min-height: 28px;}} "
            f"QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} "
            f"QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}"
        )

    def _get_dialog_list_widget_style(self) -> str:
        return f"""
            QListWidget {{
                border: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND};
                color: {DARK_TEXT_PRIMARY}; outline: none; border-radius: 4px;
            }}
            QListWidget::item {{ padding: 8px 12px; border-bottom: 1px solid {DARK_BORDER}; background-color: {DARK_WIDGET_BACKGROUND}; }}
            QListWidget::item:selected {{ background-color: {DARK_PRIMARY_ACTION}4D; color: #ffffff; border-left: 3px solid {DARK_PRIMARY_ACTION}; }}
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
        """

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
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet(
            f"QLabel {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
        )

        instruction_label = QLabel(
            f"Search for and select a location to assign to <b>{self.horse_name}</b>."
        )
        instruction_label.setWordWrap(True)
        instruction_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-bottom: 5px; background-color: transparent;"
        )
        layout.addWidget(instruction_label)

        input_style = self._get_dialog_specific_input_field_style()
        list_widget_style = self._get_dialog_list_widget_style()

        search_layout = QHBoxLayout()
        search_label = QLabel("Search Location:")
        self.location_search_input = QLineEdit()
        self.location_search_input.setPlaceholderText(
            "Enter location name to search..."
        )
        self.location_search_input.setStyleSheet(input_style)
        self.location_search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.location_search_input, 1)
        layout.addLayout(search_layout)

        self.locations_results_list = QListWidget()
        self.locations_results_list.setStyleSheet(list_widget_style)
        self.locations_results_list.itemClicked.connect(self._on_location_selected)
        layout.addWidget(self.locations_results_list, 1)  # Give stretch factor

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Select Location")
        self.ok_button.setEnabled(False)  # Disabled until a location is selected

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        generic_button_style = self._get_dialog_generic_button_style()
        for button in self.button_box.buttons():
            button.setMinimumHeight(30)
            button.setStyleSheet(generic_button_style)
            if button == self.ok_button:
                ok_bg_color = DARK_SUCCESS_ACTION
                if len(ok_bg_color) == 4 and ok_bg_color.startswith(
                    "#"
                ):  # Expand 3-digit hex
                    ok_bg_color = (
                        f"#{ok_bg_color[1]*2}{ok_bg_color[2]*2}{ok_bg_color[3]*2}"
                    )
                button.setStyleSheet(
                    generic_button_style
                    + f"QPushButton {{ background-color: {ok_bg_color}; color: white; }}"
                )
        layout.addWidget(self.button_box)

    def _load_initial_locations(self):
        try:
            self.all_active_locations = self.location_controller.get_all_locations(
                status_filter="active"
            )
            self._filter_locations_list()  # Populate initially with all active
            self.logger.info(
                f"Loaded {len(self.all_active_locations)} active locations initially."
            )
        except Exception as e:
            self.logger.error(
                f"Error loading initial active locations: {e}", exc_info=True
            )
            QMessageBox.critical(self, "Load Error", "Could not load active locations.")
            self.locations_results_list.addItem("Error loading locations.")

    def _on_search_text_changed(self):
        self.search_timer.start(300)  # Debounce search

    def _filter_locations_list(self):
        search_term = self.location_search_input.text().strip().lower()
        self.locations_results_list.clear()
        self.selected_location_id = None  # Clear selection on new search
        self.ok_button.setEnabled(False)

        found_any = False
        for loc in self.all_active_locations:
            if search_term in loc.location_name.lower():
                item_text = f"{loc.location_name}"
                if loc.city and loc.state_code:
                    item_text += f" ({loc.city}, {loc.state_code})"
                elif loc.city:
                    item_text += f" ({loc.city})"

                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, loc.location_id)
                self.locations_results_list.addItem(list_item)
                found_any = True

        if not found_any:
            self.locations_results_list.addItem(
                "No locations match your search."
                if search_term
                else "No active locations found."
            )

    def _on_location_selected(self, item: QListWidgetItem):
        location_id = item.data(Qt.ItemDataRole.UserRole)
        if location_id is not None:
            self.selected_location_id = location_id
            self.ok_button.setEnabled(True)
            self.logger.info(
                f"Location selected: ID {self.selected_location_id}, Display: {item.text()}"
            )
        else:
            self.selected_location_id = None
            self.ok_button.setEnabled(False)
            self.logger.info("Location selection cleared or invalid item clicked.")

    def get_selected_location_id(self) -> Optional[int]:
        """Returns the ID of the selected location if the dialog was accepted."""
        if self.result() == QDialog.DialogCode.Accepted:
            return self.selected_location_id
        return None
