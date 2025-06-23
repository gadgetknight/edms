# views/admin/tabs/application_paths_tab.py

"""
EDSI Veterinary Management System - Application Paths Tab
Version: 1.0.3
Purpose: UI for configuring user-defined paths for the database, logs, invoices, and statements.
         Now receives ConfigManager via dependency injection.
Last Updated: June 23, 2025
Author: Gemini

Changelog:
- v1.0.3 (2025-06-23):
    - **CRITICAL BUG FIX (Finalizing Dependency Injection):** Removed all direct
      imports of `config_manager` and `ConfigManager` from this file.
    - Modified `__init__` to accept `config_manager_instance` as an argument
      and store it as `self._config_manager`.
    - All calls to `config_manager.get_path` and `config_manager.set_path`
      now use `self._config_manager`.
    - This completes the dependency injection for `ApplicationPathsTab`.
- v1.0.2 (2025-06-23):
    - **BUG FIX & UX IMPROVEMENT:** Modified `_browse_for_file` method.
      For the database file path, if the path in the QLineEdit already points
      to an existing file, it now uses `QFileDialog.getOpenFileName` to avoid
      the confusing "Do you want to replace it?" prompt.
- v1.0.1 (2025-06-23):
    - **BUG FIX:** Added `from typing import List` to resolve `NameError: name 'List' is not defined`
      in the `_validate_paths` method signature.
# ... (previous changelog entries)
"""

import os
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QApplication,  # For showing info/error via parent view
)
from PySide6.QtCore import Qt, Signal, QTimer, QCoreApplication
from PySide6.QtGui import QFont, QPalette, QColor

from config.app_config import AppConfig

# REMOVED: Direct import of config_manager and ConfigManager - now injected
# from config.config_manager import config_manager, ConfigManager


class ApplicationPathsTab(QWidget):
    """
    A tab widget for the UserManagementScreen allowing users to configure
    application-specific file and directory paths.
    """

    # Signal emitted when paths are successfully saved
    paths_saved = Signal()

    def __init__(
        self, parent_view: Optional[QWidget] = None, config_manager_instance=None
    ):  # NEW: Accept instance
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = (
            parent_view  # Reference to UserManagementScreen for message boxes
        )

        self._config_manager = config_manager_instance  # NEW: Store injected instance

        # Store initial paths to check for changes and for discard functionality
        self._initial_paths: Dict[str, str] = {}

        # UI Elements
        self.db_path_input: QLineEdit
        self.log_dir_input: QLineEdit
        self.invoices_dir_input: QLineEdit
        self.statements_dir_input: QLineEdit

        self.save_button: QPushButton
        self.discard_button: QPushButton

        self._has_unsaved_changes: bool = False
        self._suppress_data_changed_signal = (
            False  # To prevent signal emission during programmatic updates
        )

        self._setup_ui()
        self._apply_styles()
        self._setup_connections()
        self._load_current_paths()
        self.update_buttons_state()  # Initial state of buttons

    def _get_input_field_style(self) -> str:
        """Generates the standard style for input fields."""
        return (
            f"QLineEdit {{ background-color: {AppConfig.DARK_INPUT_FIELD_BACKGROUND}; "
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; "
            f"border: 1px solid {AppConfig.DARK_BORDER}; border-radius: 4px; "
            f"padding: 6px 10px; font-size: 13px; min-height: 22px; }}"
            f"QLineEdit:focus {{ border-color: {AppConfig.DARK_PRIMARY_ACTION}; }}"
            f"QLineEdit:read-only {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; "
            f"color: {AppConfig.DARK_TEXT_TERTIARY}; }}"
        )

    def _get_button_style(self, btn_type: str = "standard") -> str:
        """Generates button styles based on type."""
        base_style = (
            f"QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; "
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; "
            f"border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; "
            f"min-height: 28px; }}"
            f"QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; "
            f"color: {AppConfig.DARK_TEXT_TERTIARY}; border-color: {AppConfig.DARK_HEADER_FOOTER}; }}"
        )
        if btn_type == "save":
            return (
                f"{base_style} QPushButton {{ background-color: {AppConfig.DARK_SUCCESS_ACTION}; "
                f"color: white; border-color: {AppConfig.DARK_SUCCESS_ACTION}; }}"
                f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_SUCCESS_ACTION).lighter(115).name()}; }}"
            )
        elif btn_type == "browse":
            return (
                f"{base_style} QPushButton {{ background-color: {AppConfig.DARK_PRIMARY_ACTION}; "
                f"color: white; border-color: {AppConfig.DARK_PRIMARY_ACTION}; }}"
                f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_PRIMARY_ACTION).lighter(115).name()}; }}"
            )
        return base_style

    def _setup_ui(self):
        """Initializes and lays out the UI widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        description_label = QLabel(
            "Configure the main file and directory paths for the application data. "
            "Changing these paths will require an application restart to take full effect."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-bottom: 10px;"
        )
        main_layout.addWidget(description_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(0, 0, 0, 0)  # No extra margins for form

        # Database File Path
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("e.g., C:/EDMS_Data/edsi_database.db")
        self.db_browse_btn = QPushButton("Browse...")
        db_h_layout = QHBoxLayout()
        db_h_layout.addWidget(self.db_path_input)
        db_h_layout.addWidget(self.db_browse_btn)
        form_layout.addRow(QLabel("Database File:"), db_h_layout)

        # Log Directory
        self.log_dir_input = QLineEdit()
        self.log_dir_input.setPlaceholderText("e.g., C:/EDMS_Data/logs")
        self.log_browse_btn = QPushButton("Browse...")
        log_h_layout = QHBoxLayout()
        log_h_layout.addWidget(self.log_dir_input)
        log_h_layout.addWidget(self.log_browse_btn)
        form_layout.addRow(QLabel("Logs Directory:"), log_h_layout)

        # Invoices Directory
        self.invoices_dir_input = QLineEdit()
        self.invoices_dir_input.setPlaceholderText("e.g., C:/EDMS_Data/invoices")
        self.invoices_browse_btn = QPushButton("Browse...")
        invoices_h_layout = QHBoxLayout()
        invoices_h_layout.addWidget(self.invoices_dir_input)
        invoices_h_layout.addWidget(self.invoices_browse_btn)
        form_layout.addRow(QLabel("Invoices Directory:"), invoices_h_layout)

        # Statements Directory (NEW)
        self.statements_dir_input = QLineEdit()
        self.statements_dir_input.setPlaceholderText("e.g., C:/EDMS_Data/statements")
        self.statements_browse_btn = QPushButton("Browse...")
        statements_h_layout = QHBoxLayout()
        statements_h_layout.addWidget(self.statements_dir_input)
        statements_h_layout.addWidget(self.statements_browse_btn)
        form_layout.addRow(QLabel("Statements Directory:"), statements_h_layout)

        main_layout.addLayout(form_layout)

        # Spacer to push buttons to the bottom if content is sparse
        main_layout.addStretch(1)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Push buttons to the right

        self.discard_button = QPushButton("Discard Changes")
        self.save_button = QPushButton("Save Paths")

        button_layout.addWidget(self.discard_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

    def _apply_styles(self):
        """Applies consistent styling to the widgets."""
        # Labels
        for label in self.findChildren(QLabel):
            label.setStyleSheet(f"color: {AppConfig.DARK_TEXT_PRIMARY};")
            label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 10))

        # Line Edits
        for line_edit in self.findChildren(QLineEdit):
            line_edit.setStyleSheet(self._get_input_field_style())
            line_edit.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 10))

        # Buttons
        self.db_browse_btn.setStyleSheet(self._get_button_style("browse"))
        self.log_browse_btn.setStyleSheet(self._get_button_style("browse"))
        self.invoices_browse_btn.setStyleSheet(self._get_button_style("browse"))
        self.statements_browse_btn.setStyleSheet(self._get_button_style("browse"))

        self.save_button.setStyleSheet(self._get_button_style("save"))
        self.discard_button.setStyleSheet(self._get_button_style("standard"))

    def _setup_connections(self):
        """Connects signals to slots."""
        self.db_browse_btn.clicked.connect(
            lambda: self._browse_for_file(self.db_path_input, file_mode=True)
        )
        self.log_browse_btn.clicked.connect(
            lambda: self._browse_for_file(self.log_dir_input, file_mode=False)
        )
        self.invoices_browse_btn.clicked.connect(
            lambda: self._browse_for_file(self.invoices_dir_input, file_mode=False)
        )
        self.statements_browse_btn.clicked.connect(
            lambda: self._browse_for_file(self.statements_dir_input, file_mode=False)
        )

        # Connect textChanged signals for input fields to detect unsaved changes
        self.db_path_input.textChanged.connect(self._on_input_changed)
        self.log_dir_input.textChanged.connect(self._on_input_changed)
        self.invoices_dir_input.textChanged.connect(self._on_input_changed)
        self.statements_dir_input.textChanged.connect(self._on_input_changed)

        self.save_button.clicked.connect(self._save_paths)
        self.discard_button.clicked.connect(self._discard_changes)

    def _load_current_paths(self):
        """Loads the current paths from ConfigManager and populates inputs."""
        self._suppress_data_changed_signal = (
            True  # Suppress signals during programmatic update
        )

        # Use the injected _config_manager instance
        self.db_path_input.setText(
            self._config_manager.get_path(self._config_manager.DB_PATH_KEY) or ""
        )
        self.log_dir_input.setText(
            self._config_manager.get_path(self._config_manager.LOG_DIR_KEY) or ""
        )
        self.invoices_dir_input.setText(
            self._config_manager.get_path(self._config_manager.INVOICES_DIR_KEY) or ""
        )
        self.statements_dir_input.setText(
            self._config_manager.get_path(self._config_manager.STATEMENTS_DIR_KEY) or ""
        )

        # Store these as initial paths to check for changes
        self._initial_paths = self._get_current_input_paths()

        self._suppress_data_changed_signal = False
        self._has_unsaved_changes = False  # No changes immediately after loading
        self.update_buttons_state()

    def _get_current_input_paths(self) -> Dict[str, str]:
        """Helper to get current text from all input fields."""
        # Use the injected _config_manager instance for keys
        return {
            self._config_manager.DB_PATH_KEY: self.db_path_input.text().strip(),
            self._config_manager.LOG_DIR_KEY: self.log_dir_input.text().strip(),
            self._config_manager.INVOICES_DIR_KEY: self.invoices_dir_input.text().strip(),
            self._config_manager.STATEMENTS_DIR_KEY: self.statements_dir_input.text().strip(),
        }

    def _on_input_changed(self):
        """Slot to mark that there are unsaved changes."""
        if self._suppress_data_changed_signal:
            return

        current_paths = self._get_current_input_paths()
        # Compare current paths with initial paths to determine if there are actual changes
        if current_paths != self._initial_paths:
            if not self._has_unsaved_changes:
                self.logger.debug("Changes detected in path inputs.")
                self._has_unsaved_changes = True
                self.update_buttons_state()
        else:
            if self._has_unsaved_changes:
                self.logger.debug("Changes reverted in path inputs.")
                self._has_unsaved_changes = False
                self.update_buttons_state()

    def _browse_for_file(self, line_edit: QLineEdit, file_mode: bool = False):
        """
        Opens a file dialog for selecting a file or directory.
        For file selection (database), it now intelligently switches between
        getOpenFileName (if file exists) and getSaveFileName (if new file).
        """
        initial_path = line_edit.text() if line_edit.text() else os.path.expanduser("~")

        if file_mode:  # This is specifically for the database file
            selected_path = None

            # Check if the current path in the QLineEdit points to an existing file
            if os.path.exists(initial_path) and os.path.isfile(initial_path):
                self.logger.debug(
                    f"Browsing for existing database file at: {initial_path}"
                )
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Existing Database File",
                    initial_path,
                    "SQLite Database Files (*.db);;All Files (*.*)",
                )
                if file_path:
                    selected_path = file_path
            else:
                self.logger.debug(
                    f"Browsing to create/select new database file. Initial: {initial_path}"
                )
                # If the path is empty or does not exist, use getSaveFileName
                # This is where the "replace" prompt will appear if user types an existing name,
                # but it's appropriate for *creating* new files.
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Create or Select Database File",
                    initial_path,
                    "SQLite Database Files (*.db);;All Files (*.*)",
                )
                if file_path:
                    selected_path = file_path

            if selected_path:
                line_edit.setText(selected_path)

        else:  # This is for directory selection (logs, invoices, statements)
            self.logger.debug(f"Browsing for directory. Initial: {initial_path}")
            dir_path = QFileDialog.getExistingDirectory(
                self, "Select Directory", initial_path
            )
            if dir_path:
                line_edit.setText(dir_path)

    def _save_paths(self):
        """Validates and saves the configured paths."""
        paths_to_save = self._get_current_input_paths()
        errors = self._validate_paths(paths_to_save)

        if errors:
            self._show_message(
                "Validation Error", "\n".join(errors), QMessageBox.Warning
            )
            return

        try:
            # Use the injected _config_manager instance
            self._config_manager.set_path(
                self._config_manager.DB_PATH_KEY,
                paths_to_save[self._config_manager.DB_PATH_KEY],
            )
            self._config_manager.set_path(
                self._config_manager.LOG_DIR_KEY,
                paths_to_save[self._config_manager.LOG_DIR_KEY],
            )
            self._config_manager.set_path(
                self._config_manager.INVOICES_DIR_KEY,
                paths_to_save[self._config_manager.INVOICES_DIR_KEY],
            )
            self._config_manager.set_path(
                self._config_manager.STATEMENTS_DIR_KEY,
                paths_to_save[self._config_manager.STATEMENTS_DIR_KEY],
            )

            self._initial_paths = (
                paths_to_save  # Update initial paths after successful save
            )
            self._has_unsaved_changes = False
            self.update_buttons_state()
            self._show_message(
                "Paths Saved",
                "Application paths saved successfully. Restart the application for changes to take full effect.",
                QMessageBox.Information,
            )
            self.paths_saved.emit()  # Emit signal on successful save
        except Exception as e:
            self.logger.error(f"Error saving application paths: {e}", exc_info=True)
            self._show_message(
                "Save Error",
                f"An unexpected error occurred while saving paths: {e}",
                QMessageBox.Critical,
            )

    def _validate_paths(self, paths: Dict[str, str]) -> List[str]:
        """Performs basic validation on the paths."""
        validation_errors = []

        # Use the injected _config_manager instance for keys
        if not paths[self._config_manager.DB_PATH_KEY]:
            validation_errors.append("Database File path cannot be empty.")
        elif not os.path.isabs(paths[self._config_manager.DB_PATH_KEY]):
            validation_errors.append("Database File path must be an absolute path.")

        for key in [
            self._config_manager.LOG_DIR_KEY,
            self._config_manager.INVOICES_DIR_KEY,
            self._config_manager.STATEMENTS_DIR_KEY,
        ]:
            if not paths[key]:
                validation_errors.append(
                    f"{key.replace('_', ' ').title()} cannot be empty."
                )
            elif not os.path.isabs(paths[key]):
                validation_errors.append(
                    f"{key.replace('_', ' ').title()} must be an absolute path."
                )

        return validation_errors

    def _discard_changes(self):
        """Discards unsaved changes and reloads initial paths."""
        if self._has_unsaved_changes:
            reply = self._show_message(
                "Discard Changes",
                "Are you sure you want to discard all unsaved changes to paths?",
                QMessageBox.Question,
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.logger.info("Discarding changes to application paths.")
        self._load_current_paths()  # Reloads from config_manager or previous _initial_paths
        self.update_buttons_state()
        self._show_message(
            "Changes Discarded",
            "All unsaved changes to application paths have been discarded.",
            QMessageBox.Information,
        )

    def update_buttons_state(self):
        """Updates the enabled/disabled state of Save and Discard buttons."""
        self.save_button.setEnabled(self._has_unsaved_changes)
        self.discard_button.setEnabled(self._has_unsaved_changes)
        self.logger.debug(
            f"Buttons state updated: Save={self.save_button.isEnabled()}, Discard={self.discard_button.isEnabled()}"
        )

    def _show_message(
        self,
        title: str,
        message: str,
        icon: QMessageBox.Icon,
        buttons: QMessageBox.StandardButtons = QMessageBox.Ok,
    ) -> QMessageBox.StandardButton:
        if (
            self.parent_view
            and hasattr(self.parent_view, "show_info")
            and hasattr(self.parent_view, "show_warning")
            and hasattr(self.parent_view, "show_error")
            and hasattr(self.parent_view, "show_question")
        ):

            if icon == QMessageBox.Information:
                self.parent_view.show_info(title, message)
            elif icon == QMessageBox.Warning:
                self.parent_view.show_warning(title, message)
            elif icon == QMessageBox.Critical:
                self.parent_view.show_error(title, message)
            elif icon == QMessageBox.Question:
                result = self.parent_view.show_question(title, message)
                return QMessageBox.Yes if result else QMessageBox.No
            return QMessageBox.Ok
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(icon)
            msg_box.setStandardButtons(buttons)
            return msg_box.exec()
