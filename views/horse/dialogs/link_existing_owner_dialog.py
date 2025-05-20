# views/horse/dialogs/link_existing_owner_dialog.py
"""
EDSI Veterinary Management System - Link Existing Owner Dialog
Version: 1.0.4
Purpose: Dialog for selecting an existing owner and linking them to a horse.
         Allows 0% ownership and ensures dialog stays open on validation error.
Last Updated: May 19, 2025
Author: Claude Assistant

Changelog:
- v1.0.4 (2025-05-19):
    - Changed percentage_input range and validation to allow 0.00%.
    - Ensured dialog validation logic explicitly keeps dialog open on error.
- v1.0.3 (2025-05-19):
    - Resolved AppConfig constant AttributeError by importing constants directly.
    - Removed import of UserManagementScreen and localized style helper methods.
    - Added missing `from typing import Optional, Dict, List`.
    - Improved UI consistency, label alignment, and QComboBox population logic.
    - Ensured setAutoFillBackground(True) is called after setPalette.
    - Set a base stylesheet for the dialog to ensure `QLabel` color is consistent.
- v1.0.2 (User's May 17th version):
    - Changed percentage_spinbox minimum to 0.00 to allow 0% ownership.
    - Updated percentage validation in `get_data` to allow 0%.
"""
import logging
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from controllers.owner_controller import OwnerController
from models import Owner as OwnerModel

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


class LinkExistingOwnerDialog(QDialog):
    def __init__(self, parent_view_or_dialog, horse_name: str):
        super().__init__(parent_view_or_dialog)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.horse_name = horse_name
        self.owner_controller = OwnerController()
        self.owners_list: List[OwnerModel] = []
        self.selected_owner_id: Optional[int] = None

        self.setWindowTitle(f"Link Existing Owner to {self.horse_name}")
        self.setMinimumWidth(500)

        self._setup_palette()
        self._setup_ui()
        self._load_owners_and_search()

    def _get_dialog_specific_input_field_style(self) -> str:
        return f"""
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox {{
                background-color: {DARK_INPUT_FIELD_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px; min-height: 20px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent; subcontrol-position: right center; width: 15px; }}
            QComboBox::down-arrow {{ image: url(none); }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY};
                border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_HIGHLIGHT_BG};
                selection-color: {DARK_HIGHLIGHT_TEXT};
            }} """

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
            QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }} """

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
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet(
            f"QLabel {{ color: {DARK_TEXT_SECONDARY}; background-color: transparent; padding-top: 3px; }}"
        )
        instruction_label = QLabel(
            f"Search for an existing owner to link to <b>{self.horse_name}</b>, select them from the list, then specify their ownership percentage."
        )
        instruction_label.setWordWrap(True)
        instruction_label.setStyleSheet(
            f"color: {DARK_TEXT_SECONDARY}; margin-bottom: 8px; background-color: transparent;"
        )
        layout.addWidget(instruction_label)
        input_style = self._get_dialog_specific_input_field_style()
        list_widget_style = self._get_dialog_list_widget_style()
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Owner:")
        self.owner_search_input = QLineEdit()
        self.owner_search_input.setPlaceholderText("Name or Account #")
        self.owner_search_input.setStyleSheet(input_style)
        self.owner_search_input.textChanged.connect(self._load_owners_and_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.owner_search_input, 1)
        layout.addLayout(search_layout)
        self.owner_results_list = QListWidget()
        self.owner_results_list.setStyleSheet(list_widget_style)
        self.owner_results_list.setFixedHeight(150)
        self.owner_results_list.itemClicked.connect(self._on_owner_selected_from_search)
        layout.addWidget(self.owner_results_list)
        self.selected_owner_label = QLabel("Selected Owner:")
        self.selected_owner_display_text = QLabel("<i>No owner selected</i>")
        self.selected_owner_display_text.setStyleSheet(
            f"color: {DARK_TEXT_PRIMARY}; font-style: italic; border: 1px solid {DARK_BORDER}; background-color: {DARK_INPUT_FIELD_BACKGROUND}; padding: 6px; border-radius: 4px;"
        )
        self.selected_owner_display_text.setMinimumHeight(20 + 12)
        layout.addWidget(self.selected_owner_label)
        layout.addWidget(self.selected_owner_display_text)
        percentage_layout = QHBoxLayout()
        percentage_label = QLabel("Ownership %:*")
        percentage_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.percentage_spinbox = QDoubleSpinBox()
        self.percentage_spinbox.setStyleSheet(input_style)
        self.percentage_spinbox.setRange(0.00, 100.00)  # MODIFIED: Allow 0.00
        self.percentage_spinbox.setDecimals(2)
        self.percentage_spinbox.setSuffix(" %")
        self.percentage_spinbox.setValue(100.00)
        percentage_layout.addWidget(percentage_label)
        percentage_layout.addWidget(self.percentage_spinbox)
        percentage_layout.addStretch()
        layout.addLayout(percentage_layout)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Link Owner")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.button_box.accepted.connect(self._validate_and_accept)
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

    def _load_owners_and_search(self):
        search_term = (
            self.owner_search_input.text()
            if hasattr(self, "owner_search_input")
            else ""
        )
        try:
            self.owners_list = self.owner_controller.get_all_owners_for_lookup(
                search_term
            )
            self.owner_results_list.blockSignals(True)
            self.owner_results_list.clear()
            if self.owners_list:
                for o_data in self.owners_list:
                    item = QListWidgetItem(o_data["name_account"])
                    item.setData(Qt.ItemDataRole.UserRole, o_data["id"])
                    self.owner_results_list.addItem(item)
            else:
                self.owner_results_list.addItem(
                    "No owners found matching search."
                    if search_term
                    else "No active owners available."
                )
            self.owner_results_list.blockSignals(False)
        except Exception as e:
            self.logger.error(f"Error loading/searching owners: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Load Error", "Could not load existing owners for search."
            )
            self.owner_results_list.blockSignals(True)
            self.owner_results_list.clear()
            self.owner_results_list.addItem("Error loading owners")
            self.owner_results_list.blockSignals(False)
        self._clear_selection_state()

    def _on_owner_selected_from_search(self, item: QListWidgetItem):
        owner_id = item.data(Qt.ItemDataRole.UserRole)
        if owner_id is not None:
            self.selected_owner_id = owner_id
            self.selected_owner_display_text.setText(item.text())
            self.selected_owner_display_text.setStyleSheet(
                f"color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; background-color: {DARK_INPUT_FIELD_BACKGROUND}; padding: 6px; border-radius: 4px;"
            )
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            self.logger.info(
                f"Owner selected from search: ID {self.selected_owner_id}, Display: {item.text()}"
            )
        else:
            self._clear_selection_state()

    def _clear_selection_state(self):
        self.selected_owner_id = None
        self.selected_owner_display_text.setText("<i>No owner selected</i>")
        self.selected_owner_display_text.setStyleSheet(
            f"color: {DARK_TEXT_TERTIARY}; font-style: italic; border: 1px solid {DARK_BORDER}; background-color: {DARK_INPUT_FIELD_BACKGROUND}; padding: 6px; border-radius: 4px;"
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def _validate_and_accept(self):
        if self.selected_owner_id is None:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please search for and select an owner from the list.",
            )
            return  # Keep dialog open
        percentage = self.percentage_spinbox.value()
        if not (0.00 <= percentage <= 100.00):  # MODIFIED: Allow 0.00
            QMessageBox.warning(
                self,
                "Input Error",
                "Ownership percentage must be between 0.00 and 100.00.",
            )
            return  # Keep dialog open
        self.logger.debug("LinkExistingOwnerDialog validation successful, accepting.")
        super().accept()  # Close dialog with Accepted result

    def get_data(self) -> Optional[Dict]:
        if self.selected_owner_id is None:
            return None
        return {
            "owner_id": self.selected_owner_id,
            "percentage": self.percentage_spinbox.value(),
        }
