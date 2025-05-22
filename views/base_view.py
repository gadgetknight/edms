# views/base_view.py

"""
EDSI Veterinary Management System - Base View
Version: 1.1.5
Purpose: Base class for all application windows using PySide6.
         Added logging to setup_ui to track layout management.
Last Updated: May 21, 2025
Author: Claude Assistant

Changelog:
- v1.1.5 (2025-05-21):
    - Added detailed logging in setup_ui() to trace layout initialization
      on self.central_widget.
- v1.1.4 (2025-05-18):
    - Modified __init__ to call self.setup_ui() before
      self.apply_dark_theme_palette_and_global_styles(), aligning
      with user's original BaseView structure for initialization order.
- v1.1.3 (2025-05-18):
    - Updated imports and styling methods to use DARK_... theme constants.
- v1.1.2 (2025-05-18):
    - (Previous attempt to fix imports)
- v1.1.1 (2025-05-12): User's provided version.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QScreen,
)

from config.app_config import (
    APP_NAME,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    SMALL_FONT_SIZE,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    DARK_BACKGROUND,
    DARK_WIDGET_BACKGROUND,
    DARK_HEADER_FOOTER,
    DARK_BORDER,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DARK_TEXT_TERTIARY,
    DARK_PRIMARY_ACTION,
    DARK_BUTTON_BG,
    DARK_BUTTON_HOVER,
    DARK_ITEM_HOVER,
    DARK_TOOLTIP_BASE,
    DARK_TOOLTIP_TEXT,
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_INPUT_FIELD_BACKGROUND,
)


class BaseView(QMainWindow):
    """Base class for all application windows using PySide6."""

    closing = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.logger.info(
            f"BaseView __init__ for {self.__class__.__name__}: central_widget created."
        )

        if hasattr(self, "setup_ui") and callable(self.setup_ui):
            self.logger.info(
                f"BaseView __init__ for {self.__class__.__name__}: Calling overridden setup_ui()."
            )
            self.setup_ui()  # This will call the subclass's setup_ui if overridden
        else:
            # This else block should ideally not be hit if subclasses always define setup_ui
            self.logger.warning(
                f"BaseView __init__ for {self.__class__.__name__}: No setup_ui defined or not callable. Applying default layout logic."
            )
            if not self.central_widget.layout():
                base_layout = QVBoxLayout(self.central_widget)
                # self.central_widget.setLayout(base_layout) # QVBoxLayout(parent) already sets it.
                self.logger.info(
                    f"BaseView __init__ (fallback): Applied default QVBoxLayout to central_widget for {self.__class__.__name__}."
                )
            else:
                self.logger.info(
                    f"BaseView __init__ (fallback): central_widget for {self.__class__.__name__} already had a layout."
                )

        self.apply_dark_theme_palette_and_global_styles()

    def setup_ui(self):
        """
        Intended to be overridden by subclasses to set their own layouts and widgets.
        If a subclass calls super().setup_ui() or doesn't override, this default runs.
        """
        self.logger.info(f"BaseView.setup_ui() CALLED for {self.__class__.__name__}.")
        # Default implementation: if subclass calls super().setup_ui() or doesn't override,
        # ensure central_widget has a layout.
        if not self.central_widget.layout():
            base_layout = QVBoxLayout(self.central_widget)
            # self.central_widget.setLayout(base_layout) # QVBoxLayout(parent) constructor already sets the layout
            self.logger.info(
                f"BaseView.setup_ui(): Applied new default QVBoxLayout to central_widget for {self.__class__.__name__} because it had no layout."
            )
        else:
            self.logger.info(
                f"BaseView.setup_ui(): central_widget for {self.__class__.__name__} ALREADY HAS a layout ({type(self.central_widget.layout())}). No new default layout applied by BaseView.setup_ui."
            )

    def apply_dark_theme_palette_and_global_styles(self):
        """Applies a dark theme palette and global stylesheet settings."""
        self.logger.debug(
            f"Applying dark theme and global styles for {self.__class__.__name__}"
        )

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(DARK_WIDGET_BACKGROUND))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK_ITEM_HOVER))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DARK_TOOLTIP_BASE))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DARK_TOOLTIP_TEXT))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(DARK_BUTTON_BG))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK_TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(DARK_PRIMARY_ACTION))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(DARK_HIGHLIGHT_BG))
        dark_palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(DARK_HIGHLIGHT_TEXT)
        )
        dark_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(DARK_TEXT_TERTIARY)
        )

        disabled_text_color = QColor(DARK_TEXT_TERTIARY)
        disabled_bg_color = QColor(DARK_HEADER_FOOTER)
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
        dark_palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            disabled_text_color,
        )

        self.setPalette(dark_palette)
        QApplication.instance().setPalette(dark_palette)

        if self.central_widget:
            self.central_widget.setPalette(dark_palette)
            self.central_widget.setAutoFillBackground(True)
        self.setAutoFillBackground(True)

        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        app_font = QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE)
        QApplication.setFont(app_font)
        self.setFont(app_font)

        try:
            self.setStyleSheet(
                f"""
                QMainWindow, QDialog, QWidget {{
                    font-family: "{DEFAULT_FONT_FAMILY}";
                    font-size: {DEFAULT_FONT_SIZE}pt;
                    background-color: {DARK_BACKGROUND};
                    color: {DARK_TEXT_PRIMARY};
                }}
                QFrame {{ }}
                QLabel {{
                    color: {DARK_TEXT_PRIMARY};
                    background-color: transparent;
                    padding: 1px;
                }}
                QPushButton {{
                    background-color: {DARK_BUTTON_BG};
                    color: {DARK_TEXT_PRIMARY};
                    border: 1px solid {DARK_BORDER};
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                    min-height: 30px;
                }}
                QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }}
                QPushButton:pressed {{ background-color: {QColor(DARK_BUTTON_HOVER).darker(110).name()}; }}
                QPushButton:disabled {{
                    background-color: {DARK_HEADER_FOOTER};
                    color: {DARK_TEXT_TERTIARY};
                    border-color: {DARK_BORDER};
                }}
                QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
                    background-color: {DARK_INPUT_FIELD_BACKGROUND};
                    border: 1px solid {DARK_BORDER};
                    border-radius: 4px;
                    padding: 6px 8px;
                    color: {DARK_TEXT_PRIMARY};
                    min-height: 20px;
                }}
                QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
                    border-color: {DARK_PRIMARY_ACTION};
                }}
                QLineEdit:read-only {{
                    background-color: {QColor(DARK_INPUT_FIELD_BACKGROUND).darker(110).name()};
                    color: {DARK_TEXT_TERTIARY};
                }}
                QComboBox::drop-down {{ border: none; }}
                QComboBox QAbstractItemView {{
                    background-color: {DARK_WIDGET_BACKGROUND};
                    color: {DARK_TEXT_PRIMARY};
                    border: 1px solid {DARK_BORDER};
                    selection-background-color: {DARK_HIGHLIGHT_BG};
                    selection-color: {DARK_HIGHLIGHT_TEXT};
                }}
                QStatusBar {{
                    font-size: {SMALL_FONT_SIZE}pt;
                    color: {DARK_TEXT_SECONDARY};
                    background-color: {DARK_HEADER_FOOTER};
                    border-top: 1px solid {DARK_BORDER};
                }}
                QHeaderView::section {{
                    background-color: {DARK_HEADER_FOOTER};
                    color: {DARK_TEXT_PRIMARY};
                    padding: 5px;
                    border: 1px solid {DARK_BORDER};
                    font-size: {DEFAULT_FONT_SIZE}pt;
                    font-weight: 500;
                }}
                QTableWidget {{
                    gridline-color: {DARK_BORDER};
                    background-color: {DARK_WIDGET_BACKGROUND};
                    color: {DARK_TEXT_PRIMARY};
                    border: 1px solid {DARK_BORDER};
                }}
                QTableWidget::item {{ padding: 5px; }}
                QTableWidget::item:selected {{
                    background-color: {DARK_HIGHLIGHT_BG};
                    color: {DARK_HIGHLIGHT_TEXT};
                }}
                QListWidget {{
                     background-color: {DARK_WIDGET_BACKGROUND};
                     color: {DARK_TEXT_PRIMARY};
                     border: 1px solid {DARK_BORDER};
                }}
                QListWidget::item {{ padding: 5px; }}
                QListWidget::item:selected {{
                    background-color: {DARK_HIGHLIGHT_BG};
                    color: {DARK_HIGHLIGHT_TEXT};
                }}
                QListWidget::item:hover:!selected {{ background-color: {DARK_ITEM_HOVER}; }}
                QToolTip {{
                    background-color: {DARK_TOOLTIP_BASE};
                    color: {DARK_TOOLTIP_TEXT};
                    border: 1px solid {DARK_BORDER};
                    padding: 4px;
                    border-radius: 3px;
                }}
            """
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error applying global stylesheet in BaseView: {e}",
                exc_info=True,
            )
            self.setStyleSheet(
                "QMainWindow { background-color: #1A202C; } QLabel { color: #E2E8F0; }"
            )

    def set_title(self, title: str):
        self.setWindowTitle(f"{APP_NAME} - {title}")

    def show_error(self, title: str, message: str):
        self.logger.error(f"Displaying Error: {title} - {message}")
        QMessageBox.critical(self, title, str(message))

    def show_warning(self, title: str, message: str):
        self.logger.warning(f"Displaying Warning: {title} - {message}")
        QMessageBox.warning(self, title, str(message))

    def show_info(self, title: str, message: str):
        self.logger.info(f"Displaying Info: {title} - {message}")
        QMessageBox.information(self, title, str(message))

    def show_question(self, title: str, message: str) -> bool:
        self.logger.info(f"Asking Question: {title} - {message}")
        reply = QMessageBox.question(
            self,
            title,
            str(message),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def center_on_screen(self):
        try:
            primary_screen = QApplication.primaryScreen()
            if primary_screen:
                screen_geometry = primary_screen.availableGeometry()
                self.move(screen_geometry.center() - self.rect().center())
            else:
                self.logger.warning("Could not detect primary screen for centering.")
                self.move(100, 100)
        except Exception as e:
            self.logger.error(f"Could not center window: {e}", exc_info=True)
            self.move(100, 100)

    def closeEvent(self, event):
        self.logger.debug(f"Close event triggered for {self.__class__.__name__}")
        self.closing.emit()
        super().closeEvent(event)
