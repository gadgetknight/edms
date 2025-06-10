# views/widgets/custom_question_dialog.py
"""
EDSI Veterinary Management System - Custom Question Dialog
Version: 1.0.0
Purpose: A custom QDialog that mimics QMessageBox.question but allows for
         reliable and explicit styling of its buttons.
Last Updated: June 8, 2025
Author: Gemini
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPalette

from config.app_config import (
    DARK_WIDGET_BACKGROUND,
    DARK_TEXT_PRIMARY,
    DARK_SUCCESS_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DEFAULT_FONT_FAMILY,
    DARK_BORDER,
)


class CustomQuestionDialog(QDialog):
    """A custom dialog to ask a Yes/No question with fully styleable buttons."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(350)

        # --- Palette and Base Style ---
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(DARK_WIDGET_BACKGROUND))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Message Label ---
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont(DEFAULT_FONT_FAMILY, 10))
        self.message_label.setStyleSheet(f"color: {DARK_TEXT_PRIMARY};")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.message_label)

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        button_layout.addSpacerItem(spacer)

        self.no_button = QPushButton("No")
        self.yes_button = QPushButton("Yes")

        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.yes_button)

        main_layout.addLayout(button_layout)

        self.no_button.setDefault(True)
        self.yes_button.setAutoDefault(False)

        # --- Connections ---
        self.yes_button.clicked.connect(self.accept)
        self.no_button.clicked.connect(self.reject)

        # --- Apply Styles ---
        self._apply_button_styles()

    def _apply_button_styles(self):
        """Applies the 'boxed-in' style directly to the buttons."""
        base_style = """
            QPushButton {
                border: 1px solid white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
                font-weight: bold;
            }
        """

        self.yes_button.setStyleSheet(
            base_style
            + f"""
            QPushButton {{ background-color: {DARK_SUCCESS_ACTION}; color: white; }}
            QPushButton:hover {{ background-color: {QColor(DARK_SUCCESS_ACTION).lighter(115).name()}; }}
        """
        )

        self.no_button.setStyleSheet(
            base_style
            + f"""
            QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; }}
            QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
        """
        )
