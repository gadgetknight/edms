# views/reports/reports_screen.py
"""
EDSI Veterinary Management System - Main Reports Screen
Version: 1.0.0
Purpose: A central hub for selecting and running various application reports.
Last Updated: June 10, 2025
Author: Gemini
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QStackedWidget,
    QLabel,
    QPushButton,
    QFrame,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from views.base_view import BaseView
from config.app_config import AppConfig
from controllers import ReportsController


class ReportsScreen(BaseView):
    """The main screen for accessing all reports."""

    back_to_main_menu = Signal()

    def __init__(self, current_user_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_user_id = current_user_id
        self.reports_controller = ReportsController()

        self.setWindowTitle("Reports and Billing")
        self.resize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Panel: Report List
        left_panel = QFrame()
        left_panel.setFixedWidth(250)
        left_panel.setObjectName("LeftPanel")
        left_panel.setStyleSheet(
            f"""
            #LeftPanel {{
                background-color: {AppConfig.DARK_HEADER_FOOTER};
                border-right: 1px solid {AppConfig.DARK_BORDER};
            }}
        """
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)

        report_list_label = QLabel("Available Reports")
        report_list_label.setFont(
            QFont(AppConfig.DEFAULT_FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        report_list_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-bottom: 10px;"
        )

        self.report_list_widget = QListWidget()
        self.report_list_widget.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {AppConfig.DARK_BORDER};
                background-color: {AppConfig.DARK_WIDGET_BACKGROUND};
            }}
            QListWidget::item {{
                padding: 12px;
            }}
            QListWidget::item:selected {{
                background-color: {AppConfig.DARK_PRIMARY_ACTION};
                color: {AppConfig.DARK_HIGHLIGHT_TEXT};
                border: none;
            }}
            """
        )
        self.populate_report_list()

        left_layout.addWidget(report_list_label)
        left_layout.addWidget(self.report_list_widget, 1)

        # Right Panel: Options and Preview
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.options_stack = QStackedWidget()
        right_layout.addWidget(self.options_stack, 1)

        # Placeholder widget for when no report is selected
        placeholder_widget = QLabel("Select a report from the list to see options.")
        placeholder_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_widget.setStyleSheet(f"color: {AppConfig.DARK_TEXT_SECONDARY};")
        self.options_stack.addWidget(placeholder_widget)

        # Action Buttons
        action_layout = QHBoxLayout()
        self.back_button = QPushButton("Back to Main Menu")
        self.back_button.clicked.connect(self.back_to_main_menu.emit)

        self.run_report_button = QPushButton("Run Report")
        self.run_report_button.setEnabled(False)  # Disabled until a report is selected

        action_layout.addWidget(self.back_button)
        action_layout.addStretch()
        action_layout.addWidget(self.run_report_button)
        right_layout.addLayout(action_layout)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

    def populate_report_list(self):
        """Adds the report names to the list widget."""
        # These are placeholders for now. We will build each one.
        reports = [
            "Owner Statement",
            "A/R Aging",
            "Invoice Register",
            "Payment History",
            "Charge Code Usage",
            "Horse Transaction History",
        ]
        for report_name in reports:
            item = QListWidgetItem(report_name)
            item.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 11))
            self.report_list_widget.addItem(item)
