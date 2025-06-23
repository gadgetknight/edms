# views/admin/tabs/backup_restore_tab.py

"""
EDSI Veterinary Management System - Backup and Restore Tab
Version: 1.0.7
Purpose: UI for managing application data backups and restores.
         Now receives BackupManager via dependency injection.
Last Updated: June 23, 2025
Author: Gemini

Changelog:
- v1.0.7 (2025-06-23):
    - **CRITICAL BUG FIX (Finalizing Dependency Injection):** Removed all direct
      imports of `sys`, `os`, and `backup_manager` from this file.
    - Modified `__init__` to accept `backup_manager_instance` as an argument
      and store it as `self._backup_manager`.
    - All calls to `backup_manager.create_backup` and `backup_manager.restore_backup`
      now use `self._backup_manager`.
    - This completes the dependency injection for `BackupRestoreTab`,
      eliminating the `ModuleNotFoundError` by ensuring the manager is passed,
      not imported locally.
- v1.0.6 (2025-06-23):
    - **CRITICAL BUG FIX (Final Attempt for ModuleNotFoundError):** Ensured `sys.path` manipulation
      is the *very first operation* in this module to guarantee the project root is added
      before *any* other imports are processed. This should definitively resolve the
      `ModuleNotFoundError: No module named 'services'`.
- v1.0.5 (2025-06-23):
    - **CRITICAL BUG FIX:** Re-introduced explicit `sys.path` manipulation at the
      very top of this file to ensure the project root is always discoverable
      before any imports.
# ... (previous changelog entries)
"""

# Removed local sys.path manipulation
import logging
import os  # Added import for 'os'
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer, QCoreApplication
from PySide6.QtGui import QFont, QPalette, QColor

from config.app_config import AppConfig

# REMOVED: Direct import of backup_manager - now injected
# from services.backup_manager import backup_manager


class BackupRestoreTab(QWidget):
    """
    A tab widget for the UserManagementScreen allowing users to perform
    backup and restore operations.
    """

    # Signal emitted when a significant backup/restore action completes
    operation_completed = Signal(str)

    def __init__(
        self, parent_view: Optional[QWidget] = None, backup_manager_instance=None
    ):  # NEW: Accept instance
        super().__init__(parent_view)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_view = parent_view

        self._backup_manager = backup_manager_instance  # NEW: Store injected instance

        self.create_backup_btn: QPushButton
        self.restore_backup_btn: QPushButton

        self.current_user_id = "UNKNOWN_USER"

        self._setup_ui()
        self._apply_styles()
        self._setup_connections()
        self.update_button_states()

    def _get_button_style(self, btn_type: str = "standard") -> str:
        base_style = (
            f"QPushButton {{ background-color: {AppConfig.DARK_BUTTON_BG}; "
            f"color: {AppConfig.DARK_TEXT_PRIMARY}; border: 1px solid {AppConfig.DARK_BORDER}; "
            f"border-radius: 4px; padding: 8px 15px; font-size: 12px; font-weight: 500; "
            f"min-height: 36px; }}"
            f"QPushButton:hover {{ background-color: {AppConfig.DARK_BUTTON_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {AppConfig.DARK_HEADER_FOOTER}; "
            f"color: {AppConfig.DARK_TEXT_TERTIARY}; border-color: {AppConfig.DARK_HEADER_FOOTER}; }}"
        )
        if btn_type == "primary":
            return (
                f"{base_style} QPushButton {{ background-color: {AppConfig.DARK_PRIMARY_ACTION}; "
                f"color: white; border-color: {AppConfig.DARK_PRIMARY_ACTION}; }}"
                f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_PRIMARY_ACTION).lighter(115).name()}; }}"
            )
        elif btn_type == "danger":
            return (
                f"{base_style} QPushButton {{ background-color: {AppConfig.DARK_DANGER_ACTION}; "
                f"color: white; border-color: {AppConfig.DARK_DANGER_ACTION}; }}"
                f"QPushButton:hover {{ background-color: {QColor(AppConfig.DARK_DANGER_ACTION).lighter(115).name()}; }}"
            )
        return base_style

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        description_label = QLabel(
            "Manage your application's data by creating backups or restoring from a previous backup. "
            "Backups include your database, invoices, statements, logs, and application settings."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet(
            f"color: {AppConfig.DARK_TEXT_SECONDARY}; margin-bottom: 10px;"
        )
        main_layout.addWidget(description_label)

        backup_group_layout = QVBoxLayout()
        backup_group_layout.setContentsMargins(0, 0, 0, 0)

        self.create_backup_btn = QPushButton("📦 Create New Backup")
        backup_group_layout.addWidget(self.create_backup_btn)

        main_layout.addLayout(backup_group_layout)

        main_layout.addSpacing(20)

        restore_group_layout = QVBoxLayout()
        restore_group_layout.setContentsMargins(0, 0, 0, 0)

        self.restore_backup_btn = QPushButton("↩️ Restore from Backup")
        restore_group_layout.addWidget(self.restore_backup_btn)

        main_layout.addLayout(restore_group_layout)

        main_layout.addStretch(1)

    def _apply_styles(self):
        for label in self.findChildren(QLabel):
            label.setStyleSheet(f"color: {AppConfig.DARK_TEXT_PRIMARY};")
            label.setFont(QFont(AppConfig.DEFAULT_FONT_FAMILY, 10))

        self.create_backup_btn.setStyleSheet(self._get_button_style("primary"))
        self.restore_backup_btn.setStyleSheet(self._get_button_style("danger"))

    def _setup_connections(self):
        self.create_backup_btn.clicked.connect(self._handle_create_backup)
        self.restore_backup_btn.clicked.connect(self._handle_restore_backup)

    def update_button_states(self):
        self.create_backup_btn.setEnabled(True)
        self.restore_backup_btn.setEnabled(True)

    def _get_current_user_id(self) -> str:
        if (
            self.parent_view
            and hasattr(self.parent_view, "current_user_id")
            and self.parent_view.current_user_id
        ):
            return self.parent_view.current_user_id
        self.logger.warning(
            "Could not retrieve current_user_id from parent view. Using 'system'."
        )
        return "system"

    def _handle_create_backup(self):
        self.logger.info("Initiating backup creation process.")

        default_backup_dir = os.path.join(  # `os` is now imported
            os.path.expanduser("~"), "Documents", "EDMS_Backups"
        )
        os.makedirs(default_backup_dir, exist_ok=True)

        backup_destination_root = QFileDialog.getExistingDirectory(
            self, "Select Destination for Backup", default_backup_dir
        )

        if not backup_destination_root:
            self.logger.info("Backup destination selection cancelled by user.")
            self._show_message(
                "Backup Cancelled",
                "Backup operation was cancelled.",
                QMessageBox.Information,
            )
            return

        self._show_message(
            "Backup In Progress",
            "Creating backup... This may take a moment. The application may become unresponsive.",
            QMessageBox.Information,
        )
        QCoreApplication.processEvents()

        current_user_id = self._get_current_user_id()
        # Use the injected _backup_manager
        success, message = self._backup_manager.create_backup(
            backup_destination_root, current_user_id
        )

        if success:
            self._show_message("Backup Successful", message, QMessageBox.Information)
            self.operation_completed.emit("backup_success")
        else:
            self._show_message("Backup Failed", message, QMessageBox.Critical)
            self.operation_completed.emit("backup_failed")

    def _handle_restore_backup(self):
        self.logger.info("Initiating restore from backup process.")

        confirmation = self._show_message(
            "Confirm Data Restore",
            "WARNING: Restoring from a backup will OVERWRITE ALL CURRENT APPLICATION DATA (database, invoices, statements, logs, and settings).\n\n"
            "This action is IRREVERSIBLE. It is highly recommended to create a fresh backup BEFORE proceeding with a restore.\n\n"
            "Do you wish to continue?",
            QMessageBox.Warning,
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirmation == QMessageBox.StandardButton.No:
            self.logger.info("Restore operation cancelled by user.")
            self._show_message(
                "Restore Cancelled",
                "Restore operation was cancelled.",
                QMessageBox.Information,
            )
            return

        default_backup_dir = os.path.join(
            os.path.expanduser("~"), "Documents", "EDMS_Backups"
        )

        backup_source_path = QFileDialog.getExistingDirectory(
            self, "Select Backup Folder to Restore From", default_backup_dir
        )

        if not backup_source_path:
            self.logger.info("Backup source selection cancelled by user.")
            self._show_message(
                "Restore Cancelled",
                "Restore operation was cancelled.",
                QMessageBox.Information,
            )
            return

        self._show_message(
            "Restore In Progress",
            "Restoring data... This may take a moment. The application will restart automatically after completion.",
            QMessageBox.Information,
        )
        QCoreApplication.processEvents()

        current_user_id = self._get_current_user_id()
        # Use the injected _backup_manager
        success, message = self._backup_manager.restore_backup(
            backup_source_path, current_user_id
        )

        if success:
            self._show_message("Restore Successful", message, QMessageBox.Information)
            self.operation_completed.emit("restore_success")
            self.logger.info("Restore successful. Initiating application restart.")
            QMessageBox.information(
                None,
                "Application Restart Required",
                "Data restore complete. The application will now restart for changes to take full effect.",
            )
            QApplication.instance().quit()
        else:
            self._show_message("Restore Failed", message, QMessageBox.Critical)
            self.operation_completed.emit("restore_failed")

    def _show_message(
        self,
        title: str,
        message: str,
        icon: QMessageBox.Icon,
        buttons: QMessageBox.StandardButtons = QMessageBox.StandardButton.Ok,
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
            return QMessageBox.StandardButton.Ok
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(icon)
            msg_box.setStandardButtons(buttons)
            return msg_box.exec()
