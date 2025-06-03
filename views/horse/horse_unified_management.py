# views/horse/horse_unified_management.py

"""
EDSI Veterinary Management System - Unified Horse Management Screen (Dark Theme)
Version: 1.7.37
Purpose: Unified interface for horse management.
         - Corrected AttributeError in load_horses method based on v1.7.34.
Last Updated: May 31, 2025
Author: Gemini (Further modified by Coding partner)

Changelog:
- v1.7.37 (2025-05-31):
    - Fixed AttributeError in `load_horses` method by removing invalid
      second argument `QListWidgetItem.SelectionOption.NoUpdate` from
      `self.horse_list.setCurrentRow(i, ...)`. This fix is applied
      to the user's baseline v1.7.34.
- v1.7.34 (2025-05-26) (User's baseline):
    - Original version provided by user. Known to be mostly stable.
# ... (Original changelog from v1.7.34 if any, or previous relevant entries like v1.7.33)
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QListWidgetItem,
    QTabWidget,
    QWidget,
    QSplitter,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QMenu,
    QDialog,
    QMessageBox,
    QStatusBar,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import (
    QFont,
    QPalette,
    QColor,
    QAction,
    QKeyEvent,
    QShowEvent,
    QCloseEvent,
    QDoubleValidator,
)
from sqlalchemy.orm.exc import DetachedInstanceError

from views.base_view import BaseView
from config.app_config import (
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
    DARK_HIGHLIGHT_BG,
    DARK_HIGHLIGHT_TEXT,
    DARK_INPUT_FIELD_BACKGROUND,
    DEFAULT_FONT_FAMILY,
    DARK_SUCCESS_ACTION,
    DARK_DANGER_ACTION,
)
from controllers.horse_controller import HorseController
from controllers.owner_controller import OwnerController
from controllers.location_controller import LocationController
from models import Horse, Location as LocationModel, Owner as OwnerModel

from .tabs.basic_info_tab import BasicInfoTab
from .tabs.owners_tab import OwnersTab
from .tabs.location_tab import LocationTab
from .widgets.horse_list_widget import HorseListWidget


class HorseUnifiedManagement(BaseView):
    horse_selection_changed = Signal(int)
    exit_requested = Signal()
    setup_requested = Signal()
    closing = Signal()

    def __init__(self, current_user=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"HorseUnifiedManagement __init__ started for user: {current_user}"
        )
        self.current_user = current_user or "ADMIN"
        self.horse_controller = HorseController()
        self.owner_controller = OwnerController()
        self.location_controller = LocationController()

        self.tab_widget: Optional[QTabWidget] = None
        self.basic_info_tab: Optional[BasicInfoTab] = None
        self.owners_tab: Optional[OwnersTab] = None
        self.location_tab: Optional[LocationTab] = None
        self.horse_list: Optional[HorseListWidget] = None
        self.empty_frame: Optional[QFrame] = None
        self.horse_details_content_widget: Optional[QWidget] = None
        self.horse_title: Optional[QLabel] = None
        self.horse_info_line: Optional[QLabel] = None
        self.add_horse_btn: Optional[QPushButton] = None
        self.edit_horse_btn: Optional[QPushButton] = None
        self.refresh_btn: Optional[QPushButton] = None
        self.help_btn: Optional[QPushButton] = None
        self.print_btn: Optional[QPushButton] = None
        self.setup_icon_btn: Optional[QPushButton] = None
        self.user_menu_button: Optional[QPushButton] = None
        self.user_menu: Optional[QMenu] = None
        self.active_only_radio: Optional[QRadioButton] = None
        self.all_horses_radio: Optional[QRadioButton] = None
        self.deactivated_radio: Optional[QRadioButton] = None
        self.filter_group: Optional[QButtonGroup] = None
        self.search_input: Optional[QLineEdit] = None
        self.splitter: Optional[QSplitter] = None
        self.list_widget_container: Optional[QWidget] = None
        self.details_widget: Optional[QWidget] = None
        self.details_layout: Optional[QVBoxLayout] = None
        self.status_bar: Optional[QStatusBar] = None
        self.status_label: Optional[QLabel] = None
        self.footer_horse_count_label: Optional[QLabel] = None
        self.shortcut_label: Optional[QLabel] = None

        super().__init__()

        self.horses_list_data: List[Horse] = []
        self.current_horse: Optional[Horse] = None
        self._has_changes_in_active_tab: bool = False
        self._is_new_mode: bool = False

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.logger.debug("Scheduling load_initial_data with QTimer.singleShot(0).")
        QTimer.singleShot(0, self.load_initial_data)
        self.logger.info(
            "HorseUnifiedManagement screen __init__ finished (initial data load deferred)."
        )

    def setup_ui(self):  # Structure from user's v1.7.34
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! HORSEUNIFIEDMANAGEMENT.SETUP_UI IS BEING CALLED NOW !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        self.logger.info("HorseUnifiedManagement.setup_ui: EXECUTION CONFIRMED.")

        self.set_title("Horse Management")
        self.resize(1200, 800)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_header(main_layout)
        self.setup_action_bar(main_layout)
        self.setup_main_content(main_layout)
        self.setup_footer(main_layout)
        self.setup_connections()

        self.logger.info("HorseUnifiedManagement.setup_ui: All components initialized.")

    def showEvent(self, event: QShowEvent):  # Structure from user's v1.7.34
        self.logger.info("HorseUnifiedManagement showEvent: START")
        super().showEvent(event)

        self.logger.debug(
            "showEvent: Checking core UI elements (empty_frame, horse_details_content_widget)..."
        )
        if (
            not hasattr(self, "empty_frame")
            or not self.empty_frame
            or not hasattr(self, "horse_details_content_widget")
            or not self.horse_details_content_widget
        ):
            self.logger.error(
                "showEvent: Core UI elements for displaying state are NOT ready. UI setup might be incomplete. Aborting showEvent further processing."
            )
            return
        self.logger.debug("showEvent: Core UI elements check PASSED.")

        if self.current_horse:
            self.logger.debug(
                "showEvent: current_horse exists. Calling display_details_state."
            )
            self.display_details_state()
            self.logger.debug("showEvent: display_details_state call completed.")
            if (
                self.basic_info_tab
                and not self._is_new_mode
                and hasattr(self.basic_info_tab, "_is_editing")
                and not self.basic_info_tab._is_editing  # type: ignore
            ):
                self.logger.debug("showEvent: Setting basic_info_tab to read-only.")
                if hasattr(self.basic_info_tab, "set_form_read_only"):
                    self.basic_info_tab.set_form_read_only(True)
                self.logger.debug("showEvent: basic_info_tab set to read-only.")
        else:
            self.logger.debug(
                "showEvent: No current_horse. Calling display_empty_state."
            )
            self.display_empty_state()
            self.logger.debug("showEvent: display_empty_state call completed.")

        self.logger.debug("showEvent: Calling update_main_action_buttons_state.")
        self.update_main_action_buttons_state()
        self.logger.debug("showEvent: update_main_action_buttons_state call completed.")

        self.logger.info(
            "HorseUnifiedManagement showEvent: FINISHED - screen should be visible."
        )

    def display_empty_state(self):  # Structure from user's v1.7.34
        self.logger.debug("display_empty_state: START")

        if hasattr(self, "empty_frame") and self.empty_frame:
            self.logger.debug("display_empty_state: Showing empty_frame.")
            self.empty_frame.show()
        else:
            self.logger.warning(
                "display_empty_state: empty_frame not available or not valid."
            )

        if (
            hasattr(self, "horse_details_content_widget")
            and self.horse_details_content_widget
        ):
            self.logger.debug(
                "display_empty_state: Hiding horse_details_content_widget."
            )
            self.horse_details_content_widget.hide()
        else:
            self.logger.warning(
                "display_empty_state: horse_details_content_widget not available."
            )

        self.current_horse = None
        self._is_new_mode = False
        self._has_changes_in_active_tab = False
        self.logger.debug("display_empty_state: Basic state flags reset.")

        if self.basic_info_tab:
            self.logger.debug(
                "display_empty_state: Calling basic_info_tab.clear_fields()."
            )
            try:
                self.basic_info_tab.clear_fields()
                self.logger.debug(
                    "display_empty_state: basic_info_tab.clear_fields() successful."
                )
                if hasattr(self.basic_info_tab, "set_form_read_only"):
                    self.logger.debug(
                        "display_empty_state: Attempting basic_info_tab.set_form_read_only(True)."
                    )
                    self.basic_info_tab.set_form_read_only(True)
                    self.logger.debug(
                        "display_empty_state: basic_info_tab.set_form_read_only(True) done."
                    )
            except Exception as e:
                self.logger.error(
                    f"display_empty_state: Error in basic_info_tab.clear_fields or set_form_read_only: {e}",
                    exc_info=True,
                )

            if hasattr(self.basic_info_tab, "update_buttons_state"):
                self.logger.debug(
                    "display_empty_state: Calling basic_info_tab.update_buttons_state(...)."
                )
                try:
                    self.basic_info_tab.update_buttons_state(
                        is_editing_or_new=False, has_selection=False, has_changes=False
                    )
                    self.logger.debug(
                        "display_empty_state: basic_info_tab.update_buttons_state() successful."
                    )
                except Exception as e:
                    self.logger.error(
                        f"display_empty_state: Error in basic_info_tab.update_buttons_state: {e}",
                        exc_info=True,
                    )
        else:
            self.logger.error("display_empty_state: BasicInfoTab is None.")

        if self.owners_tab and hasattr(self.owners_tab, "load_owners_for_horse"):
            self.logger.debug(
                "display_empty_state: Calling owners_tab.load_owners_for_horse(None)."
            )
            try:
                self.owners_tab.load_owners_for_horse(None)
                self.logger.debug(
                    "display_empty_state: owners_tab.load_owners_for_horse(None) successful."
                )
            except Exception as e:
                self.logger.error(
                    f"display_empty_state: Error in owners_tab.load_owners_for_horse: {e}",
                    exc_info=True,
                )
        else:
            self.logger.warning(
                "display_empty_state: OwnersTab is None or missing method."
            )

        if self.location_tab and hasattr(self.location_tab, "load_location_for_horse"):
            self.logger.debug(
                "display_empty_state: Calling location_tab.load_location_for_horse(None)."
            )
            try:
                self.location_tab.load_location_for_horse(None)
                self.logger.debug(
                    "display_empty_state: location_tab.load_location_for_horse(None) successful."
                )
            except Exception as e:
                self.logger.error(
                    f"display_empty_state: Error in location_tab.load_location_for_horse: {e}",
                    exc_info=True,
                )
        else:
            self.logger.warning(
                "display_empty_state: LocationTab is None or missing method."
            )

        if hasattr(self, "horse_title") and self.horse_title:
            self.logger.debug("display_empty_state: Setting horse_title text.")
            self.horse_title.setText("No Horse Selected")
        else:
            self.logger.warning(
                "display_empty_state: horse_title QLabel not available."
            )

        self.logger.debug("display_empty_state: Calling _update_horse_info_line(None).")
        self._update_horse_info_line(None)
        self.logger.debug(
            "display_empty_state: _update_horse_info_line(None) call completed."
        )

        self.logger.debug("display_empty_state: Calling update_status.")
        self.update_status("No horse selected. Add a new horse or select from list.")
        self.logger.info("display_empty_state: FINISHED")

    def update_main_action_buttons_state(self):  # Structure from user's v1.7.34
        self.logger.debug("update_main_action_buttons_state: START")
        can_add_new = not self._is_new_mode and not self._has_changes_in_active_tab
        if hasattr(self, "add_horse_btn") and self.add_horse_btn:
            self.add_horse_btn.setEnabled(can_add_new)
            self.logger.debug(
                f"update_main_action_buttons_state: add_horse_btn enabled: {can_add_new}"
            )
        else:
            self.logger.warning(
                "add_horse_btn not initialized in update_main_action_buttons_state"
            )

        form_is_editable_by_tab = False
        if self.basic_info_tab and hasattr(self.basic_info_tab, "_is_editing"):
            form_is_editable_by_tab = self.basic_info_tab._is_editing  # type: ignore

        can_edit_selected = (
            self.current_horse is not None
            and not self._is_new_mode
            and not self._has_changes_in_active_tab
            and not form_is_editable_by_tab
        )

        if hasattr(self, "edit_horse_btn") and self.edit_horse_btn:
            self.edit_horse_btn.setEnabled(can_edit_selected)
            self.logger.debug(
                f"update_main_action_buttons_state: edit_horse_btn enabled: {can_edit_selected}"
            )
        else:
            self.logger.warning(
                "edit_horse_btn not initialized in update_main_action_buttons_state"
            )

        if self.basic_info_tab and hasattr(self.basic_info_tab, "update_buttons_state"):
            self.logger.debug(
                "update_main_action_buttons_state: Updating basic_info_tab buttons."
            )
            try:
                is_editing_or_new_val = self._is_new_mode or form_is_editable_by_tab
                has_selection_val = self.current_horse is not None
                has_changes_val = self._has_changes_in_active_tab
                self.basic_info_tab.update_buttons_state(
                    is_editing_or_new_val, has_selection_val, has_changes_val
                )
            except Exception as e:
                self.logger.error(
                    f"update_main_action_buttons_state: Error calling basic_info_tab.update_buttons_state: {e}",
                    exc_info=True,
                )
        if self.owners_tab and hasattr(self.owners_tab, "update_buttons_state"):
            self.logger.debug(
                "update_main_action_buttons_state: Updating owners_tab buttons."
            )
            try:
                self.owners_tab.update_buttons_state()
            except Exception as e:
                self.logger.error(
                    f"update_main_action_buttons_state: Error calling owners_tab.update_buttons_state: {e}",
                    exc_info=True,
                )

        if self.location_tab and hasattr(self.location_tab, "update_buttons_state"):
            self.logger.debug(
                "update_main_action_buttons_state: Updating location_tab buttons."
            )
            try:
                self.location_tab.update_buttons_state()
            except Exception as e:
                self.logger.error(
                    f"update_main_action_buttons_state: Error calling location_tab.update_buttons_state: {e}",
                    exc_info=True,
                )
        self.logger.debug("update_main_action_buttons_state: FINISHED")

    def discard_changes(self):  # Structure from user's v1.7.34
        self.logger.debug("discard_changes: START")
        if not self._is_new_mode and not self._has_changes_in_active_tab:
            if (
                self.current_horse
                and self.basic_info_tab
                and hasattr(self.basic_info_tab, "_is_editing")
                and self.basic_info_tab._is_editing  # type: ignore
            ):
                self.logger.info(
                    "discard_changes: Form in edit mode, no data changes. Reverting to read-only."
                )
                if hasattr(self.basic_info_tab, "set_form_read_only"):
                    self.basic_info_tab.set_form_read_only(True)
                self.update_main_action_buttons_state()
                self.update_status(
                    f"Viewing: {self.current_horse.horse_name or 'horse'}"
                )
                self.logger.debug("discard_changes: FINISHED (no actual changes)")
                return
            self.update_status("No changes to discard.")
            self.logger.debug("discard_changes: FINISHED (no changes to discard)")
            return

        if self.show_question("Confirm Discard", "Discard unsaved changes?"):
            self.logger.info("discard_changes: User confirmed discard.")
            was_in_new_mode = self._is_new_mode
            self._is_new_mode = False
            self._has_changes_in_active_tab = False
            if self.basic_info_tab:
                self.logger.debug("discard_changes: Clearing BasicInfoTab.")
                try:
                    self.basic_info_tab.clear_fields()
                    if hasattr(self.basic_info_tab, "set_form_read_only"):
                        self.basic_info_tab.set_form_read_only(True)
                except Exception as e:
                    self.logger.error(
                        f"discard_changes: Error in basic_info_tab.clear_fields/set_form_read_only: {e}",
                        exc_info=True,
                    )

            if self.current_horse and not was_in_new_mode:
                self.logger.debug(
                    f"discard_changes: Reloading horse ID {self.current_horse.horse_id}."
                )
                self.load_horse_details(self.current_horse.horse_id)
            else:
                self.logger.debug(
                    "discard_changes: Was new or no current horse. Selecting first in list or empty state."
                )
                if self.horse_list and self.horse_list.count() > 0:
                    self.horse_list.setCurrentRow(0)
                else:
                    self.display_empty_state()
            self.update_main_action_buttons_state()
            self.update_status("Changes discarded.")
        else:
            self.logger.info("discard_changes: User cancelled discard.")
        self.logger.debug("discard_changes: FINISHED")

    def load_initial_data(self):  # Structure from user's v1.7.34
        self.logger.info("load_initial_data: START - Attempting to load horses.")
        try:
            self.load_horses()
            self.logger.info(
                "load_initial_data: FINISHED - load_horses call completed."
            )
        except Exception as e:
            self.logger.error(
                f"load_initial_data: CRITICAL ERROR during load_horses: {e}",
                exc_info=True,
            )
            self.show_error(
                "Initial Data Load Failed", f"Could not load initial horse data: {e}"
            )

    def closeEvent(self, event: QCloseEvent):  # Structure from user's v1.7.34
        self.logger.warning(f"HorseUnifiedManagement closeEvent. Type: {event.type()}")  # type: ignore
        self.closing.emit()
        super().closeEvent(event)
        self.logger.warning("HorseUnifiedManagement finished processing closeEvent.")

    def get_form_input_style(
        self, base_bg=DARK_INPUT_FIELD_BACKGROUND
    ):  # Structure from user's v1.7.34
        return f"""
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{ background-color: {base_bg}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 6px 10px; font-size: 13px; }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{ border-color: {DARK_PRIMARY_ACTION}; }}
            QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QDoubleSpinBox:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; border-color: {DARK_HEADER_FOOTER}; }}
            QComboBox::drop-down {{ border: none; background-color: transparent; width: 15px; }} QComboBox::down-arrow {{ color: {DARK_TEXT_SECONDARY}; }}
            QDateEdit::up-button, QDateEdit::down-button {{ width: 18px; }}
            QComboBox QAbstractItemView {{ background-color: {DARK_WIDGET_BACKGROUND}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; selection-background-color: {DARK_HIGHLIGHT_BG}; selection-color: {DARK_HIGHLIGHT_TEXT}; }}
        """

    def get_generic_button_style(self):  # Structure from user's v1.7.34
        return f"""
            QPushButton {{ background-color: {DARK_BUTTON_BG}; color: {DARK_TEXT_PRIMARY}; border: 1px solid {DARK_BORDER}; border-radius: 4px; padding: 8px 12px; font-size: 12px; font-weight: 500; min-height: 28px; }} 
            QPushButton:hover {{ background-color: {DARK_BUTTON_HOVER}; }} 
            QPushButton:disabled {{ background-color: {DARK_HEADER_FOOTER}; color: {DARK_TEXT_TERTIARY}; }}
        """

    def get_toolbar_button_style(
        self, bg_color_hex, text_color_hex="#ffffff"
    ):  # Structure from user's v1.7.34
        if len(bg_color_hex) == 4 and bg_color_hex.startswith(
            "#"
        ):  # Ensure 6-digit hex for QColor
            bg_color_hex = f"#{bg_color_hex[1]*2}{bg_color_hex[2]*2}{bg_color_hex[3]*2}"
        try:
            # Using QColor for robust color manipulation
            base_qcolor = QColor(bg_color_hex)
            hover_bg = base_qcolor.lighter(115).name()  # Standard hover lightness
            pressed_bg = base_qcolor.darker(110).name()  # Standard pressed darkness
        except ValueError:  # Fallback if color string is invalid
            hover_bg, pressed_bg = DARK_BUTTON_HOVER, DARK_BUTTON_BG
            self.logger.warning(
                f"Could not parse color: {bg_color_hex} for button style."
            )
        return f"""
            QPushButton {{ background-color: {bg_color_hex}; color: {text_color_hex}; border: none; border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: 500; }} 
            QPushButton:hover {{ background-color: {hover_bg}; }} QPushButton:pressed {{ background-color: {pressed_bg}; }} 
            QPushButton:disabled {{ background-color: #adb5bd; color: #f8f9fa; }}
        """  # Example disabled style, adjust as needed

    def setup_header(self, parent_layout):  # Structure from user's v1.7.34
        self.logger.debug("setup_header: START")
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setFixedHeight(55)
        header_frame.setStyleSheet(f"""#HeaderFrame{{background-color:{DARK_HEADER_FOOTER};border:none;padding:0 20px;}} QLabel{{color:{DARK_TEXT_PRIMARY};background-color:transparent;}} QPushButton#UserMenuButton{{color:{DARK_TEXT_SECONDARY};font-size:12px;background-color:transparent;border:none;padding:5px;text-align:right;}} QPushButton#UserMenuButton::menu-indicator{{image:none;}} QPushButton#UserMenuButton:hover{{color:{DARK_TEXT_PRIMARY};background-color:{QColor(DARK_ITEM_HOVER).lighter(110).name(QColor.NameFormat.HexRgb)}33;}}""")  # type: ignore
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addStretch()
        title_label = QLabel("EDSI - Horse Management")
        title_label.setFont(QFont(DEFAULT_FONT_FAMILY, 15, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        breadcrumb_label = QLabel("🏠 Horse Management")
        breadcrumb_label.setStyleSheet(
            f"color:{DARK_TEXT_SECONDARY};font-size:11px;background:transparent;"
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
        header_button_style = f"""QPushButton{{background-color:{DARK_BUTTON_BG};color:{DARK_TEXT_PRIMARY};border:1px solid {DARK_BORDER};border-radius:4px;padding:5px;font-size:14px;min-width:28px;max-width:28px;min-height:28px;max-height:28px;}} QPushButton:hover{{background-color:{DARK_BUTTON_HOVER};}} QPushButton:pressed{{background-color:{DARK_BUTTON_BG};}}"""
        for btn in [
            self.refresh_btn,
            self.help_btn,
            self.print_btn,
            self.setup_icon_btn,
        ]:
            if btn:
                btn.setStyleSheet(header_button_style)
        self.user_menu_button = QPushButton(f"👤 User: {self.current_user}")
        self.user_menu_button.setObjectName("UserMenuButton")
        self.user_menu_button.setToolTip("User options")
        self.user_menu_button.setFlat(True)
        self.user_menu = QMenu(self)
        self.user_menu.setStyleSheet(
            f"""QMenu{{background-color:{DARK_WIDGET_BACKGROUND};color:{DARK_TEXT_PRIMARY};border:1px solid {DARK_BORDER};padding:5px;}} QMenu::item{{padding:5px 20px 5px 20px;min-width:100px;}} QMenu::item:selected{{background-color:{DARK_HIGHLIGHT_BG}70;color:{DARK_HIGHLIGHT_TEXT};}} QMenu::separator{{height:1px;background:{DARK_BORDER};margin-left:5px;margin-right:5px;}}"""
        )
        logout_action = QAction("Log Out", self)
        logout_action.triggered.connect(self.handle_logout_request_from_menu)
        self.user_menu.addAction(logout_action)
        self.user_menu_button.setMenu(self.user_menu)
        for btn in [
            self.refresh_btn,
            self.help_btn,
            self.print_btn,
            self.setup_icon_btn,
            self.user_menu_button,
        ]:
            if btn:
                right_layout.addWidget(btn)
        header_layout.addWidget(left_widget)
        header_layout.addStretch()
        header_layout.addWidget(right_widget)
        parent_layout.addWidget(header_frame)
        self.logger.debug("setup_header: END")

    def setup_action_bar(self, parent_layout):  # Structure from user's v1.7.34
        self.logger.debug("setup_action_bar: START")
        action_bar_frame = QFrame()
        action_bar_frame.setObjectName("ActionBarFrame")
        action_bar_frame.setFixedHeight(50)
        action_bar_frame.setStyleSheet(
            f"""#ActionBarFrame{{background-color:{DARK_BACKGROUND};border:none;border-bottom:1px solid {DARK_BORDER};padding:0 20px;}} QPushButton{{min-height:30px;}} QLabel{{color:{DARK_TEXT_SECONDARY};background:transparent;}} QRadioButton::indicator{{width:13px;height:13px;}} QRadioButton{{color:{DARK_TEXT_SECONDARY};background:transparent;padding:5px;}}"""
        )
        action_bar_layout = QHBoxLayout(action_bar_frame)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(12)
        action_bar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.add_horse_btn = QPushButton("➕ Add Horse")
        self.edit_horse_btn = QPushButton("✓ Edit Selected")
        action_button_style_str = self.get_generic_button_style()
        add_btn_bg_color = DARK_PRIMARY_ACTION
        if len(add_btn_bg_color) == 4:
            add_btn_bg_color = f"#{add_btn_bg_color[1]*2}{add_btn_bg_color[2]*2}{add_btn_bg_color[3]*2}"
        self.add_horse_btn.setStyleSheet(action_button_style_str.replace(DARK_BUTTON_BG, add_btn_bg_color + "B3").replace(f"color:{DARK_TEXT_PRIMARY}", "color:white;"))  # type: ignore
        self.edit_horse_btn.setStyleSheet(action_button_style_str)  # type: ignore
        action_bar_layout.addWidget(self.add_horse_btn)
        action_bar_layout.addWidget(self.edit_horse_btn)
        self.filter_group = QButtonGroup(self)
        self.active_only_radio = QRadioButton("Active Only")
        self.all_horses_radio = QRadioButton("All Horses")
        self.deactivated_radio = QRadioButton("Deactivated")
        for btn in [
            self.active_only_radio,
            self.all_horses_radio,
            self.deactivated_radio,
        ]:
            if btn:
                self.filter_group.addButton(btn)
                action_bar_layout.addWidget(btn)
        if self.active_only_radio:
            self.active_only_radio.setChecked(True)
        action_bar_layout.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(
            self.get_form_input_style(base_bg=DARK_HEADER_FOOTER)
        )
        action_bar_layout.addWidget(self.search_input)
        if self.edit_horse_btn:
            self.edit_horse_btn.setEnabled(False)
        parent_layout.addWidget(action_bar_frame)
        self.logger.debug("setup_action_bar: END")

    def setup_main_content(self, parent_layout):  # Structure from user's v1.7.34
        self.logger.debug("setup_main_content: START")
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(
            f"""QSplitter{{background-color:{DARK_BACKGROUND};border:none;}} QSplitter::handle{{background-color:{DARK_BORDER};}} QSplitter::handle:horizontal{{width:1px;}} QSplitter::handle:pressed{{background-color:{DARK_TEXT_SECONDARY};}}"""
        )
        self.setup_horse_list_panel()
        self.setup_horse_details_panel()
        self.splitter.setSizes([300, 850])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        parent_layout.addWidget(self.splitter, 1)
        self.logger.debug("setup_main_content: END")

    def setup_horse_list_panel(self):  # Structure from user's v1.7.34
        self.list_widget_container = QWidget()
        self.list_widget_container.setStyleSheet(
            f"background-color:{DARK_BACKGROUND};border:none;border-right:1px solid {DARK_BORDER};"
        )
        list_layout = QVBoxLayout(self.list_widget_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        self.horse_list = HorseListWidget()
        self.horse_list.setMinimumWidth(250)
        list_layout.addWidget(self.horse_list, 1)
        if self.splitter:
            self.splitter.addWidget(self.list_widget_container)

    def setup_horse_details_panel(self):  # Structure from user's v1.7.34
        self.logger.debug("setup_horse_details_panel: START")
        self.details_widget = QWidget()
        self.details_widget.setStyleSheet(
            f"background-color:{DARK_BACKGROUND};border:none;"
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
        if self.details_layout and self.empty_frame:
            self.details_layout.addWidget(self.empty_frame)
        if self.details_layout and self.horse_details_content_widget:
            self.details_layout.addWidget(self.horse_details_content_widget)
        if self.horse_details_content_widget:
            self.horse_details_content_widget.hide()
        if self.splitter:
            self.splitter.addWidget(self.details_widget)
        self.logger.debug("setup_horse_details_panel: END")

    def setup_empty_state(self):  # Structure from user's v1.7.34
        self.logger.debug("setup_empty_state (frame creation): START")
        self.empty_frame = QFrame()
        self.empty_frame.setObjectName("EmptyFrame")
        self.empty_frame.setStyleSheet(
            "#EmptyFrame{background-color:transparent;border:none;}"
        )
        empty_layout = QVBoxLayout(self.empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(15)
        empty_label = QLabel("Select a horse from the list, or click 'Add Horse'.")
        empty_label.setStyleSheet(
            f"color:{DARK_TEXT_SECONDARY};font-size:16px;background:transparent;"
        )
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.logger.debug("setup_empty_state (frame creation): FINISHED")

    def setup_horse_header_details(
        self, parent_layout
    ):  # Structure from user's v1.7.34
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)
        self.horse_title = QLabel("Horse Name")
        self.horse_title.setFont(QFont(DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold))
        self.horse_title.setStyleSheet(
            f"color:{DARK_TEXT_PRIMARY};background:transparent;"
        )
        self.horse_info_line = QLabel(
            "Acct: N/A | 👥 No Owner | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A | 📍 N/A"
        )
        self.horse_info_line.setStyleSheet(
            f"color:{DARK_TEXT_SECONDARY};font-size:12px;background:transparent;"
        )
        self.horse_info_line.setWordWrap(True)
        header_layout.addWidget(self.horse_title)
        header_layout.addWidget(self.horse_info_line)
        parent_layout.addWidget(header_widget)

    def setup_horse_tabs(self, parent_layout_for_tabs):  # Structure from user's v1.7.34
        self.logger.info("--- HORSEUNIFIEDMANAGEMENT.SETUP_HORSE_TABS START ---")
        try:
            self.tab_widget = QTabWidget()
            self.tab_widget.setObjectName("DetailsTabWidget")
            self.tab_widget.setStyleSheet(
                f"""QTabWidget#DetailsTabWidget::pane{{border:1px solid {DARK_BORDER};background-color:{DARK_WIDGET_BACKGROUND};border-radius:6px;margin-top:-1px;}} QTabBar::tab{{padding:8px 15px;margin-right:2px;background-color:{DARK_BUTTON_BG};color:{DARK_TEXT_SECONDARY};border:1px solid {DARK_BORDER};border-bottom:none;border-top-left-radius:5px;border-top-right-radius:5px;min-width:90px;font-size:13px;font-weight:500;}} QTabBar::tab:selected{{background-color:{DARK_WIDGET_BACKGROUND};color:{DARK_TEXT_PRIMARY};border-color:{DARK_BORDER};border-bottom-color:{DARK_WIDGET_BACKGROUND};}} QTabBar::tab:!selected:hover{{background-color:{DARK_BUTTON_HOVER};color:{DARK_TEXT_PRIMARY};}} QTabBar{{border:none;background-color:transparent;margin-bottom:0px;}}"""
            )
            self.logger.info("QTabWidget created and styled.")
            try:
                self.basic_info_tab = BasicInfoTab(
                    horse_controller=self.horse_controller, parent=self
                )
                self.tab_widget.addTab(self.basic_info_tab, "📋 Basic Info")
                self.logger.info("BasicInfoTab created.")
            except Exception as e_basic:
                self.logger.error(f"ERROR BasicInfoTab: {e_basic}", exc_info=True)
                self.basic_info_tab = None
            try:
                self.owners_tab = OwnersTab(
                    parent_view=self,
                    horse_controller=self.horse_controller,
                    owner_controller=self.owner_controller,
                )
                self.tab_widget.addTab(self.owners_tab, "👥 Owners")
                self.logger.info("OwnersTab created.")
            except Exception as e_owners:
                self.logger.error(f"ERROR OwnersTab: {e_owners}", exc_info=True)
                self.owners_tab = None
            try:
                self.location_tab = LocationTab(
                    parent_view=self,
                    horse_controller=self.horse_controller,
                    location_controller=self.location_controller,
                )
                self.tab_widget.addTab(self.location_tab, "📍 Location")
                self.logger.info("LocationTab created.")
            except Exception as e_location:
                self.logger.error(f"ERROR LocationTab: {e_location}", exc_info=True)
                self.location_tab = None
            placeholder_tabs = ["💰 Billing", "📊 History"]
            for name in placeholder_tabs:
                placeholder_widget = QWidget(
                    objectName=f"Placeholder_{name.replace(' ','')}Tab"
                )
                layout = QVBoxLayout(placeholder_widget)
                label = QLabel(f"{name} - Coming Soon")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
                self.tab_widget.addTab(placeholder_widget, name)
            parent_layout_for_tabs.addWidget(self.tab_widget, 1)
            self.logger.info("Tabs added.")
        except Exception as e:
            self.logger.error(f"ERROR setup_horse_tabs: {e}", exc_info=True)
            if hasattr(self, "tab_widget") and self.tab_widget:
                self.tab_widget.deleteLater()
            self.tab_widget = None
            self.basic_info_tab = None
            self.owners_tab = None
            self.location_tab = None

    def _handle_location_assignment_change(
        self, location_data: Dict
    ):  # Structure from user's v1.7.34
        self.logger.info(f"Received location_assignment_changed: {location_data}")
        if self.current_horse and self.current_horse.horse_id is not None:
            horse_id_that_changed = self.current_horse.horse_id
            self.logger.info(
                f"Location changed for horse ID {horse_id_that_changed}. Reloading details."
            )
            self.load_horse_details(
                horse_id_that_changed
            )  # Reload to get updated horse.location
            if self.current_horse:  # Re-check current_horse after reload
                current_loc_name = "[N/A - Error]"
                try:
                    current_loc_name = (
                        self.current_horse.location.location_name
                        if self.current_horse.location
                        and hasattr(self.current_horse.location, "location_name")
                        else "N/A"
                    )
                except DetachedInstanceError:
                    current_loc_name = "[Location N/A - Session Issue]"
                self.update_status(
                    f"Location updated to '{current_loc_name}' for {self.current_horse.horse_name or 'horse'}."
                )
        else:
            self.logger.warning(
                "Location assignment changed, but no current_horse or valid horse_id to refresh."
            )

    def _get_display_owner_name(
        self, horse: Optional[Horse]
    ) -> str:  # Structure from user's v1.7.34 (Restored)
        if not horse:
            return "No Owner"

        owner_name_display = "No Owner"
        try:
            if horse.owners and len(horse.owners) > 0:
                owner_model_assoc = horse.owners[0]
                if (
                    owner_model_assoc
                    and hasattr(owner_model_assoc, "owner")
                    and owner_model_assoc.owner
                ):
                    actual_owner = owner_model_assoc.owner
                    name_parts: List[str] = []
                    if (
                        hasattr(actual_owner, "farm_name")
                        and actual_owner.farm_name
                        and actual_owner.farm_name.strip()
                    ):
                        name_parts.append(actual_owner.farm_name.strip())
                    person_name_parts: List[str] = []
                    if (
                        hasattr(actual_owner, "first_name")
                        and actual_owner.first_name
                        and actual_owner.first_name.strip()
                    ):
                        person_name_parts.append(actual_owner.first_name.strip())
                    if (
                        hasattr(actual_owner, "last_name")
                        and actual_owner.last_name
                        and actual_owner.last_name.strip()
                    ):
                        person_name_parts.append(actual_owner.last_name.strip())
                    person_name_str = " ".join(person_name_parts).strip()
                    if person_name_str:
                        if name_parts:
                            name_parts.append(f"({person_name_str})")
                        else:
                            name_parts.append(person_name_str)

                    if name_parts:
                        owner_name_display = " ".join(name_parts)
                    elif hasattr(actual_owner, "owner_id"):
                        owner_name_display = f"Owner ID: {actual_owner.owner_id}"
                    else:
                        owner_name_display = "Owner Data Incomplete"
                else:
                    owner_name_display = "Owner Data Missing"
        except DetachedInstanceError:
            logger_obj = getattr(self, "logger", logging.getLogger(__name__))
            logger_obj.warning(
                f"Detached: horse.owners or owner.owner, Horse ID {horse.horse_id if horse else 'N/A'}."
            )
            owner_name_display = "[Own N/A - Detached]"
        except Exception as e:
            self.logger.error(
                f"Error constructing owner display name: {e}", exc_info=True
            )
            owner_name_display = "[Owner Display Error]"
        return owner_name_display

    def _get_display_location_name(
        self, horse: Optional[Horse]
    ) -> str:  # Structure from user's v1.7.34 (Restored)
        if not horse:
            return "N/A"

        location_name_str = "N/A"  # Initialize with default
        try:
            if horse.location and hasattr(horse.location, "location_name"):
                location_name_str = horse.location.location_name or "N/A"
        except DetachedInstanceError:
            logger_obj = getattr(self, "logger", logging.getLogger(__name__))
            logger_obj.warning(
                f"Detached: horse.location, ID {horse.horse_id if horse else 'N/A'}."
            )
            location_name_str = "[Loc N/A - Detached]"
        except Exception as e:
            self.logger.error(f"Error getting location name: {e}", exc_info=True)
            location_name_str = "[Location Error]"
        return location_name_str

    def _update_horse_info_line(
        self, horse: Optional[Horse]
    ):  # Structure from user's v1.7.34
        if not hasattr(self, "horse_info_line") or self.horse_info_line is None:
            self.logger.error(
                "_update_horse_info_line: horse_info_line QLabel is None."
            )
            return
        if not horse:
            self.horse_info_line.setText(
                "Acct: N/A | 👥 No Owner | Breed: N/A | Color: N/A | Sex: N/A | Age: N/A | 📍 N/A"
            )
            return

        age_str = "Age N/A"
        if self.horse_list and hasattr(
            self.horse_list, "_calculate_age"
        ):  # Ensure horse_list is not None
            age_str = self.horse_list._calculate_age(horse.date_of_birth)  # type: ignore

        owner_name = self._get_display_owner_name(horse)
        location_name_val = self._get_display_location_name(
            horse
        )  # Use the corrected variable name
        self.horse_info_line.setText(
            f"Acct: {horse.account_number or 'N/A'} | 👥 {owner_name} | Breed: {horse.breed or 'N/A'} | Color: {horse.color or 'N/A'} | Sex: {horse.sex or 'N/A'} | Age: {age_str} | 📍 {location_name_val}"
        )

    def load_horse_details(self, horse_id: int):  # Structure from user's v1.7.34
        self.logger.info(f"load_horse_details: START for horse ID: {horse_id}")
        horse = self.horse_controller.get_horse_by_id(horse_id)
        self.logger.debug(
            f"load_horse_details: Fetched horse object: {'Exists' if horse else 'None'}"
        )

        # Logging details from the fetched horse object
        if horse:
            self.logger.debug(
                f"load_horse_details: Horse {horse_id} - current_location_id: {horse.current_location_id}"
            )
            if hasattr(horse, "location") and horse.location:
                self.logger.debug(
                    f"load_horse_details: Horse {horse_id} - location: ID {horse.location.location_id}, Name: {horse.location.location_name}"
                )
            if (
                hasattr(horse, "owners")
                and horse.owners
                and len(horse.owners) > 0
                and hasattr(horse.owners[0], "owner")
                and horse.owners[0].owner
            ):
                self.logger.debug(
                    f"load_horse_details: Horse {horse_id} - first owner farm: {horse.owners[0].owner.farm_name}"
                )

        if not horse:
            self.show_error("Error", f"Could not load horse ID {horse_id}.")
            self.display_empty_state()
            self.logger.info("load_horse_details: FINISHED (horse not found)")
            return

        self.current_horse = horse
        self._is_new_mode = False
        self._has_changes_in_active_tab = (
            False  # Reset this flag when a new horse is loaded
        )

        if hasattr(self, "horse_title") and self.horse_title:
            self.horse_title.setText(horse.horse_name or "Unnamed Horse")

        self._update_horse_info_line(
            horse
        )  # This should now work due to fixes in helpers

        if self.basic_info_tab:
            self.logger.debug("load_horse_details: Populating BasicInfoTab")
            self.basic_info_tab.populate_form_data(horse)
        if self.owners_tab:
            self.logger.debug("load_horse_details: Loading OwnersTab")
            self.owners_tab.load_owners_for_horse(horse)
        if self.location_tab:
            self.logger.debug("load_horse_details: Loading LocationTab")
            self.location_tab.load_location_for_horse(horse)

        self.display_details_state()
        self.update_main_action_buttons_state()
        self.update_status(f"Viewing: {horse.horse_name or 'Unnamed Horse'}")
        self.logger.info(f"load_horse_details: FINISHED for horse ID: {horse_id}")

    def add_new_horse(self):  # Structure from user's v1.7.34
        self.logger.info("add_new_horse: START")
        if self._has_changes_in_active_tab and not self.show_question(
            "Unsaved Changes", "Discard current changes and start new horse record?"
        ):
            self.logger.info("add_new_horse: Aborted due to unsaved changes.")
            return

        self._is_new_mode = True
        self._has_changes_in_active_tab = False
        self.current_horse = None

        if self.horse_list and self.horse_list.selectionModel():
            self.logger.debug("add_new_horse: Clearing horse list selection.")
            self.horse_list.blockSignals(True)
            self.horse_list.selectionModel().clear()
            self.horse_list.blockSignals(False)

        if self.basic_info_tab and hasattr(self.basic_info_tab, "set_new_mode"):
            self.logger.debug("add_new_horse: Setting BasicInfoTab to new mode.")
            self.basic_info_tab.set_new_mode(is_new=True)
        else:
            self.logger.error("add_new_horse: BasicInfoTab missing or no set_new_mode.")
            self.show_error("UI Error", "Details form unavailable.")
            self._is_new_mode = False
            return

        if self.owners_tab:
            self.logger.debug("add_new_horse: Clearing OwnersTab.")
            self.owners_tab.load_owners_for_horse(None)
        if self.location_tab:
            self.logger.debug("add_new_horse: Clearing LocationTab.")
            self.location_tab.load_location_for_horse(None)

        if hasattr(self, "horse_title") and self.horse_title:
            self.horse_title.setText("New Horse Record")
        self._update_horse_info_line(None)
        self.display_details_state()

        if self.tab_widget and self.basic_info_tab:
            self.logger.debug("add_new_horse: Setting current tab to BasicInfoTab.")
            self.tab_widget.setCurrentWidget(self.basic_info_tab)

        self.update_main_action_buttons_state()
        self.update_status("Enter details for new horse.")
        self.logger.info("add_new_horse: FINISHED")

    def _on_tab_data_modified(self):  # Structure from user's v1.7.34
        if (
            self.basic_info_tab
            and hasattr(self.basic_info_tab, "horse_name_input")
            and self.basic_info_tab.horse_name_input
            and not self.basic_info_tab.horse_name_input.isReadOnly()
        ):  # type: ignore
            if not self._has_changes_in_active_tab:
                self._has_changes_in_active_tab = True
                self.logger.debug("_on_tab_data_modified: Change detected. Flag set.")
            self.update_main_action_buttons_state()
        else:
            self.logger.debug(
                "_on_tab_data_modified: Signal received, but form read-only or input missing."
            )

    def _on_owner_association_changed(
        self, message: str
    ):  # Structure from user's v1.7.34
        self.logger.info(f"_on_owner_association_changed: {message}")
        self.update_status(message)
        if self.current_horse and self.current_horse.horse_id is not None:
            self.load_horse_details(
                self.current_horse.horse_id
            )  # Reload to reflect changes
        self.update_main_action_buttons_state()

    def handle_toggle_active_status_from_tab(
        self, new_active_status_requested: bool
    ):  # Structure from user's v1.7.34
        self.logger.info(
            f"handle_toggle_active_status_from_tab: Requested: {new_active_status_requested}"
        )
        if self.current_horse:
            self.handle_toggle_active_status()  # This method will prompt and act
        else:
            self.logger.warning(
                "handle_toggle_active_status_from_tab: No current horse."
            )

    def setup_footer(self, parent_layout):  # Structure from user's v1.7.34
        self.logger.debug("setup_footer: START")
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(
            f"""QStatusBar{{background-color:{DARK_HEADER_FOOTER};color:{DARK_TEXT_SECONDARY};border:none;border-top:1px solid {DARK_BORDER};padding:0 15px;font-size:11px;}}QStatusBar::item{{border:none;}}QLabel{{color:{DARK_TEXT_SECONDARY};background:transparent;font-size:11px;}}"""
        )
        parent_layout.addWidget(self.status_bar)
        self.status_label = QLabel("Ready")
        self.footer_horse_count_label = QLabel("Showing 0 of 0 horses")
        self.shortcut_label = QLabel("F5=Refresh | Ctrl+N=New | Ctrl+S=Save")
        self.status_bar.addWidget(self.status_label, 1)  # Stretch factor
        self.status_bar.addPermanentWidget(self.footer_horse_count_label)
        separator_label = QLabel(" | ")
        separator_label.setStyleSheet(
            f"color:{DARK_BORDER};background:transparent;margin:0 5px;"
        )
        self.status_bar.addPermanentWidget(separator_label)
        self.status_bar.addPermanentWidget(self.shortcut_label)
        self.logger.debug("setup_footer: FINISHED")

    def save_changes(
        self,
    ):  # Structure from user's v1.7.34, with simplified reselection from v1.7.36
        self.logger.info("save_changes: START")
        if not self.basic_info_tab:
            self.logger.error("save_changes: BasicInfoTab missing.")
            self.show_error("Save Error", "UI component missing.")
            return

        if not self._has_changes_in_active_tab and not self._is_new_mode:
            self.update_status("No changes to save.")
            if (
                hasattr(self.basic_info_tab, "_is_editing")
                and self.basic_info_tab._is_editing  # type: ignore
                and hasattr(self.basic_info_tab, "set_form_read_only")
            ):
                self.basic_info_tab.set_form_read_only(True)  # type: ignore
                self.update_main_action_buttons_state()
            return

        horse_data = self.basic_info_tab.get_data_from_form()
        if (
            self.current_horse
            and self.current_horse.current_location_id is not None
            and not self._is_new_mode
        ):
            horse_data["current_location_id"] = self.current_horse.current_location_id
        elif "current_location_id" not in horse_data:
            horse_data["current_location_id"] = None

        self.logger.debug(
            f"save_changes: Validating data. New: {self._is_new_mode}. Data: {horse_data}"
        )
        is_valid, errors = self.horse_controller.validate_horse_data(
            horse_data,
            is_new=self._is_new_mode,
            horse_id_to_check_for_unique=(
                self.current_horse.horse_id
                if not self._is_new_mode and self.current_horse
                else None
            ),
        )
        if not is_valid:
            self.show_warning(
                "Validation Error", "Correct errors:\n\n- " + "\n- ".join(errors)
            )
            self.logger.info("save_changes: Validation failed.")
            return

        try:
            saved_id: Optional[int] = None
            success: bool = False
            msg: str = ""
            if not self._is_new_mode and self.current_horse:
                self.logger.debug(
                    f"save_changes: Updating horse ID {self.current_horse.horse_id}"
                )
                success, msg = self.horse_controller.update_horse(
                    self.current_horse.horse_id, horse_data, self.current_user
                )
                if success:
                    saved_id = self.current_horse.horse_id
            else:
                self.logger.debug("save_changes: Creating new horse")
                success, msg, new_horse_obj = self.horse_controller.create_horse(
                    horse_data, self.current_user
                )
                if success and new_horse_obj:
                    saved_id = new_horse_obj.horse_id
                elif success and not new_horse_obj:
                    self.logger.error(
                        f"save_changes: Horse creation success={success}, but new_horse_obj is None. Msg: {msg}"
                    )

            if success:
                self.logger.info(f"save_changes: Save successful. Message: {msg}")
                self.show_info("Success", msg)
                self._has_changes_in_active_tab = False
                if self.basic_info_tab and hasattr(
                    self.basic_info_tab, "mark_as_saved"
                ):
                    self.basic_info_tab.mark_as_saved()

                if (
                    self._is_new_mode and saved_id is not None
                ):  # If it was a new horse that was saved
                    newly_saved_horse = self.horse_controller.get_horse_by_id(saved_id)
                    if newly_saved_horse:
                        self.current_horse = (
                            newly_saved_horse  # Set current horse to the new one
                        )
                        self._is_new_mode = False  # No longer in "new mode"
                        self.logger.debug(
                            f"save_changes: New horse {saved_id} set as current."
                        )
                    else:
                        self.logger.error(
                            f"save_changes: Failed to re-fetch new horse {saved_id}."
                        )
                        self.display_empty_state()  # Go to empty state as we lost context
                        self.load_horses()  # Refresh list
                        return

                self.load_horses()  # This will repopulate and attempt reselection

                # Ensure the saved_id is actually selected, load_horses reselection logic can be complex
                if saved_id is not None and self.horse_list:
                    self.logger.debug(
                        f"save_changes: Verifying selection for horse ID {saved_id} in list after load_horses."
                    )
                    found_and_selected = False
                    for i in range(self.horse_list.count()):
                        item = self.horse_list.item(i)
                        if item and item.data(Qt.ItemDataRole.UserRole) == saved_id:
                            if (
                                self.horse_list.currentRow() != i
                            ):  # Only set if not already selected
                                self.horse_list.setCurrentRow(
                                    i
                                )  # This should trigger on_selection_changed
                            else:  # If already selected, ensure details are loaded for this ID
                                self.load_horse_details(saved_id)
                            found_and_selected = True
                            self.logger.debug(
                                f"save_changes: Verified/reselected row {i} for ID {saved_id}."
                            )
                            break
                    if not found_and_selected:
                        self.logger.debug(
                            f"save_changes: Horse ID {saved_id} not found in list after save/refresh for final reselection attempt."
                        )
                        if self.horse_list.count() > 0:
                            self.horse_list.setCurrentRow(0)  # Select first item
                        else:
                            self.display_empty_state()
                elif (
                    self.horse_list and self.horse_list.count() > 0
                ):  # No saved_id but list has items
                    self.horse_list.setCurrentRow(0)
                elif (
                    not self.horse_list or self.horse_list.count() == 0
                ):  # List is empty
                    self.display_empty_state()

            else:
                self.logger.error(f"save_changes: Save failed. Message: {msg}")
                self.show_error("Save Failed", msg or "Unknown error.")
        except Exception as e:
            self.logger.error(f"save_changes: Exception: {e}", exc_info=True)
            self.show_error("Save Error", f"Unexpected error: {e}")
        self.logger.info("save_changes: FINISHED")

    def populate_horse_list(self):  # Structure from user's v1.7.34
        self.logger.debug("populate_horse_list: START")
        if not hasattr(self, "horse_list") or not self.horse_list:
            self.logger.error("populate_horse_list: horse_list widget not ready.")
            return

        current_selected_id = None
        if self.horse_list.currentItem():
            current_selected_id = self.horse_list.currentItem().data(
                Qt.ItemDataRole.UserRole
            )

        self.logger.debug(
            f"populate_horse_list: Clearing list. Previously selected ID: {current_selected_id}"
        )
        self.horse_list.clear()

        for horse_obj in self.horses_list_data:  # Changed 'horse' to 'horse_obj'
            item = QListWidgetItem()
            item_widget = self.horse_list.create_horse_list_item_widget(horse_obj)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, horse_obj.horse_id)
            self.horse_list.addItem(item)
            self.horse_list.setItemWidget(item, item_widget)

        self.logger.debug(
            f"populate_horse_list: List populated with {len(self.horses_list_data)} items."
        )

        if hasattr(self, "footer_horse_count_label") and self.footer_horse_count_label:
            total_horses_in_db = len(
                self.horse_controller.search_horses(status="all", search_term="")
            )
            self.footer_horse_count_label.setText(
                f"Showing {self.horse_list.count()} of {total_horses_in_db} total horses"
            )

        if (
            current_selected_id is not None
        ):  # Try to reselect previous item if it still exists
            for i in range(self.horse_list.count()):
                if (
                    self.horse_list.item(i).data(Qt.ItemDataRole.UserRole)
                    == current_selected_id
                ):
                    self.horse_list.setCurrentRow(i)
                    self.logger.debug(
                        f"populate_horse_list: Reselected row {i} for ID {current_selected_id}"
                    )
                    break
        self.logger.debug("populate_horse_list: FINISHED")

    def load_horses(
        self,
    ):  # MODIFIED: Only the setCurrentRow line was changed from v1.7.34
        self.logger.debug("load_horses: START")
        try:
            if (
                not hasattr(self, "search_input")
                or self.search_input is None
                or not hasattr(self, "active_only_radio")
                or self.active_only_radio is None
                or not hasattr(self, "all_horses_radio")
                or self.all_horses_radio is None
                or not hasattr(self, "deactivated_radio")
                or self.deactivated_radio is None
            ):
                self.logger.error("load_horses: Search/filter UI elements not ready.")
                return

            search_term = self.search_input.text()
            status_filter = "active"
            if self.all_horses_radio.isChecked():
                status_filter = "all"
            elif self.deactivated_radio.isChecked():
                status_filter = "inactive"

            self.logger.info(
                f"load_horses: Filter status: '{status_filter}', Search: '{search_term}'"
            )

            previously_selected_id = None
            # Try to preserve selection across reloads
            if (
                self.current_horse and not self._is_new_mode
            ):  # If a horse is loaded and we are not in new mode
                previously_selected_id = self.current_horse.horse_id
            elif (
                self.horse_list and self.horse_list.currentItem()
            ):  # Fallback to current list selection
                current_item_data = self.horse_list.currentItem().data(
                    Qt.ItemDataRole.UserRole
                )
                if isinstance(current_item_data, int):
                    previously_selected_id = current_item_data

            self.logger.debug(
                f"load_horses: Previously selected ID to try and reselect: {previously_selected_id}"
            )

            self.horses_list_data = self.horse_controller.search_horses(
                search_term=search_term, status=status_filter
            )
            self.logger.debug(
                f"load_horses: {len(self.horses_list_data)} horses found by controller."
            )

            self.populate_horse_list()  # Clears and repopulates the QListWidget

            if not self.horses_list_data:
                self.logger.debug(
                    "load_horses: No horses found, displaying empty state."
                )
                self.display_empty_state()  # This will also update buttons via its own logic
                # self.update_main_action_buttons_state() # display_empty_state should handle this
                self.logger.debug("load_horses: FINISHED (no horses)")
                return

            reselected_successfully = False
            if previously_selected_id is not None and self.horse_list:
                for i in range(self.horse_list.count()):
                    item = self.horse_list.item(i)
                    if (
                        item
                        and item.data(Qt.ItemDataRole.UserRole)
                        == previously_selected_id
                    ):
                        self.logger.debug(
                            f"load_horses: Attempting to reselect ID {previously_selected_id} at row {i}."
                        )
                        self.horse_list.setCurrentRow(
                            i
                        )  # Corrected: removed invalid second argument
                        # on_selection_changed will be triggered if row is different or if it's the first selection
                        reselected_successfully = True
                        self.logger.debug(
                            "load_horses: Reselected row. on_selection_changed will handle details load."
                        )
                        break

            if (
                not reselected_successfully
                and self.horse_list
                and self.horse_list.count() > 0
            ):
                self.logger.debug(
                    "load_horses: No reselection or previous ID not found, selecting row 0."
                )
                self.horse_list.setCurrentRow(0)  # Trigger selection of the first item
            elif (
                not self.horse_list or self.horse_list.count() == 0
            ):  # Should be caught by earlier check
                self.logger.debug(
                    "load_horses: List is empty after populate, displaying empty state."
                )
                self.display_empty_state()

            # If after all this, no item is current (e.g. list was empty and then populated but setCurrentRow(0) failed or wasn't called)
            # ensure buttons are in a sensible state. on_selection_changed should handle most of this.
            if not (self.horse_list and self.horse_list.currentItem()):
                self.update_main_action_buttons_state()  # Ensure buttons are updated based on no selection

        except Exception as e:
            self.logger.error(f"load_horses: ERROR: {e}", exc_info=True)
            self.show_error("Load Horses Error", f"{e}")
            self.horses_list_data = []  # Clear data on error
            if hasattr(self, "horse_list") and self.horse_list:
                self.populate_horse_list()  # Show empty list
            self.display_empty_state()  # Go to empty state
        self.logger.debug("load_horses: FINISHED")

    def on_search_text_changed(self):  # Structure from user's v1.7.34
        if hasattr(self.search_timer, "isActive") and self.search_timer.isActive():  # type: ignore
            self.search_timer.stop()  # type: ignore
        self.search_timer.start(350)  # type: ignore

    def perform_search(self):  # Structure from user's v1.7.34
        self.logger.debug(
            f"perform_search: Term: '{self.search_input.text() if self.search_input else ''}'"
        )
        self.load_horses()

    def on_filter_changed(self):  # Structure from user's v1.7.34
        sender_widget = self.sender()
        if isinstance(sender_widget, QRadioButton) and sender_widget.isChecked():
            self.logger.info(f"on_filter_changed: To {sender_widget.text()}")
            self.load_horses()

    def on_selection_changed(self):  # Structure from user's v1.7.34
        self.logger.debug("on_selection_changed: START")
        if not self.horse_list:
            self.logger.warning("on_selection_changed: horse_list is None.")
            return

        selected_items = self.horse_list.selectedItems()
        if not selected_items:
            self.logger.debug("on_selection_changed: No items selected.")
            if not self._is_new_mode and not self._has_changes_in_active_tab:
                self.display_empty_state()
            return

        selected_item = selected_items[0]
        newly_selected_horse_id = selected_item.data(Qt.ItemDataRole.UserRole)
        self.logger.debug(
            f"on_selection_changed: Newly selected ID: {newly_selected_horse_id}"
        )

        current_horse_id = self.current_horse.horse_id if self.current_horse else None
        self.logger.debug(
            f"on_selection_changed: Current horse ID: {current_horse_id}, New mode: {self._is_new_mode}, Has changes: {self._has_changes_in_active_tab}"
        )

        if (self._has_changes_in_active_tab or self._is_new_mode) and (
            newly_selected_horse_id != current_horse_id
            or (self._is_new_mode and newly_selected_horse_id is not None)
        ):  # Also prompt if in new mode and any item is clicked
            self.logger.debug(
                "on_selection_changed: Unsaved changes detected. Prompting user."
            )
            if not self.show_question(
                "Unsaved Changes",
                f"Discard unsaved {'new horse record' if self._is_new_mode else 'changes to current horse'}?",
            ):
                self.logger.debug(
                    "on_selection_changed: User chose NOT to discard. Reverting selection."
                )
                self.horse_list.blockSignals(True)
                if current_horse_id is not None and not self._is_new_mode:
                    for i in range(self.horse_list.count()):
                        if (
                            self.horse_list.item(i).data(Qt.ItemDataRole.UserRole)
                            == current_horse_id
                        ):
                            self.horse_list.setCurrentRow(i)
                            break
                else:  # Was in new_mode or no current_horse_id to revert to
                    self.horse_list.clearSelection()  # Deselect the newly clicked item
                self.horse_list.blockSignals(False)
                self.logger.debug("on_selection_changed: FINISHED (reverted selection)")
                return
            # User chose to discard changes
            self.logger.debug("on_selection_changed: User chose to discard changes.")
            self._has_changes_in_active_tab = False
            self._is_new_mode = False
            self.logger.debug(
                "on_selection_changed: Flags reset (_has_changes_in_active_tab, _is_new_mode)."
            )
            # Fall through to load the newly selected horse

        if newly_selected_horse_id is not None:
            if (
                newly_selected_horse_id == current_horse_id and not self._is_new_mode
            ):  # If same horse re-selected and not after discarding a new entry
                self.logger.debug(
                    f"on_selection_changed: Same horse ID ({current_horse_id}) re-selected. Ensuring read-only state."
                )
                if (
                    self.basic_info_tab
                    and hasattr(self.basic_info_tab, "_is_editing")
                    and self.basic_info_tab._is_editing
                    and not self._has_changes_in_active_tab  # type: ignore
                    and hasattr(self.basic_info_tab, "set_form_read_only")
                ):
                    self.basic_info_tab.set_form_read_only(True)  # type: ignore
                self.update_main_action_buttons_state()
                self.logger.debug(
                    "on_selection_changed: FINISHED (same horse, no load unless it was new mode that got discarded)"
                )
                return
            self.load_horse_details(newly_selected_horse_id)
        else:  # newly_selected_horse_id is None (e.g. list cleared, no item selected)
            self.logger.debug(
                "on_selection_changed: newly_selected_horse_id is None, displaying empty state."
            )
            self.display_empty_state()
        self.logger.debug("on_selection_changed: FINISHED")

    def edit_selected_horse(self):  # Structure from user's v1.7.34
        self.logger.debug("edit_selected_horse: START")
        if self.current_horse and not self._is_new_mode:
            if not self.tab_widget:
                self.logger.error("edit_selected_horse: Tab widget missing.")
                self.show_error("UI Error", "Tabs unavailable.")
                return

            current_tab_widget = self.tab_widget.currentWidget()
            self.logger.debug(
                f"edit_selected_horse: Current tab: {current_tab_widget.objectName() if current_tab_widget else 'None'}"
            )

            if (
                current_tab_widget == self.basic_info_tab
                and self.basic_info_tab
                and hasattr(self.basic_info_tab, "set_edit_mode")
            ):
                self.logger.debug(
                    "edit_selected_horse: Setting BasicInfoTab to edit mode."
                )
                self.basic_info_tab.set_edit_mode(True)
                self._has_changes_in_active_tab = (
                    False  # Reset flag, changes will be tracked by tab
                )
            elif hasattr(
                current_tab_widget, "set_edit_mode"
            ):  # For other tabs if they implement it
                self.logger.debug(
                    f"edit_selected_horse: Setting current tab {current_tab_widget.objectName()} to edit mode."
                )
                current_tab_widget.set_edit_mode(True)  # type: ignore
                self._has_changes_in_active_tab = False
            else:  # Default to BasicInfoTab if current tab doesn't support edit_mode
                self.logger.info(
                    f"edit_selected_horse: Current tab does not support direct edit. Defaulting to BasicInfoTab edit mode."
                )
                if self.basic_info_tab and hasattr(
                    self.basic_info_tab, "set_edit_mode"
                ):
                    self.basic_info_tab.set_edit_mode(True)
                    self._has_changes_in_active_tab = False

            self.update_main_action_buttons_state()
            self.update_status(
                f"Editing details for: {self.current_horse.horse_name or 'Unnamed Horse'}"
            )
        elif self._is_new_mode:
            self.show_info(
                "Information", "Currently adding new. Save or discard first."
            )
        else:
            self.show_info("Edit Horse", "Select a horse to edit.")
        self.logger.debug("edit_selected_horse: FINISHED")

    def refresh_data(self):  # Structure from user's v1.7.34
        self.logger.debug("refresh_data: START")
        if (
            self._has_changes_in_active_tab or self._is_new_mode
        ) and not self.show_question("Unsaved Changes", "Discard and refresh?"):
            self.logger.debug("refresh_data: Aborted due to unsaved changes.")
            return

        self.logger.info("refresh_data: Proceeding with refresh.")
        self._has_changes_in_active_tab = False
        self._is_new_mode = False
        self.load_horses()  # This will reload the list and reselect or select first
        self.update_status("Data refreshed.")
        self.logger.debug("refresh_data: FINISHED")

    def show_help(self):  # Structure from user's v1.7.34
        self.logger.debug("show_help: Displaying help message.")
        QMessageBox.information(
            self,
            "EDSI Help",
            "Horse Management Screen:\n\n- Use the list on the left to select a horse.\n- Click 'Add Horse' or Ctrl+N to create a new record.\n- Click 'Edit Selected' to modify the current horse's basic info.\n- Tabs on the right show different aspects of the horse's data.\n- Use radio buttons to filter the list by status.\n- Search box filters by name, account, chip, etc.\n- F5 to refresh. Ctrl+S to save (when editing). Esc to discard (when editing).",
        )

    def display_details_state(self):  # Structure from user's v1.7.34
        self.logger.debug("display_details_state: START")
        if hasattr(self, "empty_frame") and self.empty_frame:
            self.empty_frame.hide()
        if (
            hasattr(self, "horse_details_content_widget")
            and self.horse_details_content_widget
        ):
            self.horse_details_content_widget.show()
        self.logger.debug("display_details_state: FINISHED")

    def update_status(self, message, timeout=4000):  # Structure from user's v1.7.34
        if hasattr(self, "status_label") and self.status_label:
            self.status_label.setText(message)
            if timeout > 0:
                QTimer.singleShot(
                    timeout, lambda: self.clear_status_if_matches(message)
                )

    def clear_status_if_matches(
        self, original_message
    ):  # Structure from user's v1.7.34
        if (
            hasattr(self, "status_label")
            and self.status_label
            and self.status_label.text() == original_message
        ):
            self.status_label.setText("Ready")

    def handle_toggle_active_status(self):  # Structure from user's v1.7.34
        self.logger.debug("handle_toggle_active_status: START")
        if not self.current_horse:
            self.logger.warning("handle_toggle_active_status: No current horse.")
            return

        action_verb = "activate" if not self.current_horse.is_active else "deactivate"
        horse_name_display = (
            self.current_horse.horse_name or f"ID {self.current_horse.horse_id}"
        )
        self.logger.debug(
            f"handle_toggle_active_status: Prompting to {action_verb} '{horse_name_display}'."
        )

        if self.show_question(
            f"Confirm {action_verb.capitalize()}",
            f"Are you sure you want to {action_verb} horse '{horse_name_display}'?",
        ):
            self.logger.info(
                f"handle_toggle_active_status: User confirmed. Calling controller to {action_verb}."
            )
            controller_method = (
                self.horse_controller.activate_horse
                if not self.current_horse.is_active
                else self.horse_controller.deactivate_horse
            )
            success, message = controller_method(
                self.current_horse.horse_id, self.current_user
            )

            if success:
                self.logger.info(
                    f"handle_toggle_active_status: {action_verb.capitalize()} successful. {message}"
                )
                self.show_info("Status Changed", message)
                # Reload details for the current horse to reflect status change in tabs
                self.load_horse_details(self.current_horse.horse_id)
                self.load_horses()  # Refresh the list (might change position or filter out)
                # BasicInfoTab might also need its active status checkbox updated if it's separate
                if self.basic_info_tab and hasattr(
                    self.basic_info_tab, "populate_form_data"
                ):
                    self.basic_info_tab.populate_form_data(
                        self.current_horse
                    )  # Re-populate to show new status

            else:
                self.logger.error(
                    f"handle_toggle_active_status: {action_verb.capitalize()} failed. {message}"
                )
                self.show_error(f"{action_verb.capitalize()} Failed", message)
        else:
            self.logger.info("handle_toggle_active_status: User cancelled.")
        self.logger.debug("handle_toggle_active_status: FINISHED")

    def handle_logout_request_from_menu(self):  # Structure from user's v1.7.34
        self.logger.info(
            f"handle_logout_request_from_menu: User '{self.current_user}' logout."
        )
        self.exit_requested.emit()

    def keyPressEvent(self, event: QKeyEvent):  # Structure from user's v1.7.34
        key = event.key()
        modifiers = QApplication.keyboardModifiers()
        self.logger.debug(f"keyPressEvent: Key {key}, Modifiers {modifiers}")

        if key == Qt.Key.Key_F5:
            self.refresh_data()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            if (
                hasattr(self, "add_horse_btn")
                and self.add_horse_btn
                and self.add_horse_btn.isEnabled()
            ):
                self.add_new_horse()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            if (
                self.tab_widget
                and self.basic_info_tab
                and self.tab_widget.currentWidget() == self.basic_info_tab
                and hasattr(self.basic_info_tab, "save_btn")
                and self.basic_info_tab.save_btn.isEnabled()
            ):  # type: ignore
                self.logger.info("keyPressEvent: Ctrl+S triggering BasicInfoTab save.")
                self.basic_info_tab.save_requested.emit()
            else:
                self.logger.info(
                    "keyPressEvent: Ctrl+S conditions not met for BasicInfoTab save."
                )
        elif key == Qt.Key.Key_F1:
            self.show_help()
        elif key == Qt.Key.Key_Escape:
            active_modal_widget = QApplication.activeModalWidget()
            if active_modal_widget and isinstance(active_modal_widget, QDialog):
                self.logger.debug(
                    "keyPressEvent: Escape rejecting active modal dialog."
                )
                active_modal_widget.reject()
            elif self._has_changes_in_active_tab or self._is_new_mode:
                self.logger.debug("keyPressEvent: Escape triggering discard_changes.")
                self.discard_changes()
            elif (
                self.basic_info_tab
                and hasattr(self.basic_info_tab, "_is_editing")
                and self.basic_info_tab._is_editing
            ):  # type: ignore
                self.logger.debug(
                    "keyPressEvent: Escape reverting BasicInfoTab to read-only."
                )
                self.discard_changes()  # This will set form to read-only if no data changes
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def setup_connections(self):  # Structure from user's v1.7.34
        self.logger.info("--- HORSEUNIFIEDMANAGEMENT.SETUP_CONNECTIONS START ---")
        if hasattr(self, "add_horse_btn") and self.add_horse_btn:
            self.add_horse_btn.clicked.connect(self.add_new_horse)
        if hasattr(self, "edit_horse_btn") and self.edit_horse_btn:
            self.edit_horse_btn.clicked.connect(self.edit_selected_horse)
        if hasattr(self, "refresh_btn") and self.refresh_btn:
            self.refresh_btn.clicked.connect(self.refresh_data)
        if hasattr(self, "help_btn") and self.help_btn:
            self.help_btn.clicked.connect(self.show_help)
        if hasattr(self, "setup_icon_btn") and self.setup_icon_btn:
            self.setup_icon_btn.clicked.connect(self.setup_requested.emit)

        if hasattr(self, "active_only_radio") and self.active_only_radio:
            self.active_only_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "all_horses_radio") and self.all_horses_radio:
            self.all_horses_radio.toggled.connect(self.on_filter_changed)
        if hasattr(self, "deactivated_radio") and self.deactivated_radio:
            self.deactivated_radio.toggled.connect(self.on_filter_changed)

        if hasattr(self, "search_input") and self.search_input:
            self.search_input.textChanged.connect(self.on_search_text_changed)
        if hasattr(self, "horse_list") and self.horse_list:
            self.horse_list.itemSelectionChanged.connect(self.on_selection_changed)

        if self.basic_info_tab:
            self.logger.info("Connecting BasicInfoTab signals.")
            if hasattr(self.basic_info_tab, "data_modified"):
                self.basic_info_tab.data_modified.connect(self._on_tab_data_modified)
            if hasattr(self.basic_info_tab, "save_requested"):
                self.basic_info_tab.save_requested.connect(self.save_changes)
            if hasattr(self.basic_info_tab, "discard_requested"):
                self.basic_info_tab.discard_requested.connect(self.discard_changes)
            if hasattr(self.basic_info_tab, "toggle_active_requested"):
                self.basic_info_tab.toggle_active_requested.connect(
                    self.handle_toggle_active_status_from_tab
                )
        else:
            self.logger.warning(
                "BasicInfoTab is None, its signals cannot be connected."
            )

        if self.owners_tab:
            self.logger.info("Connecting OwnersTab signals.")
            if hasattr(self.owners_tab, "owner_association_changed"):
                self.owners_tab.owner_association_changed.connect(
                    self._on_owner_association_changed
                )
        else:
            self.logger.warning("OwnersTab is None, its signals cannot be connected.")

        if self.location_tab:
            self.logger.info("Connecting LocationTab signals.")
            if hasattr(self.location_tab, "location_assignment_changed"):
                self.location_tab.location_assignment_changed.connect(
                    self._handle_location_assignment_change
                )
        else:
            self.logger.warning("LocationTab is None, its signals cannot be connected.")

        self.logger.info("--- HORSEUNIFIEDMANAGEMENT.SETUP_CONNECTIONS END ---")
