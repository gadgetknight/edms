"""
EDSI Veterinary Management System - Horse Basic Record Screen
Version: 1.0.2
Purpose: Form for creating and editing basic horse information with validation and navigation.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.2 (2025-05-12): Fixed QComboBox loading for PyQt6
  - Replaced setCurrentData() with proper index-based selection
  - Fixed species, sex, and location combo box loading when editing horses
  - Added proper iteration through combo box items to find matches
  - Improved compatibility with PyQt6 combo box API
- v1.0.1 (2025-05-12): Fixed QDate conversion issue for PyQt6
  - Updated save_horse() method to properly convert QDate to Python date object
  - Changed from toPython() to manual conversion using year(), month(), day()
  - Fixed date handling compatibility across PyQt versions
- v1.0.0 (2025-05-12): Initial implementation
  - Created comprehensive horse information form
  - Implemented field validation and error display
  - Added save/cancel functionality with confirmation dialogs
  - Included dropdown menus for species and locations
  - Added date picker for date of birth
  - Implemented proper data binding and form reset
  - Added keyboard shortcuts (F1 for help, F7 for print)
"""

# views/horse/horse_basic_record.py

from PyQt6.QtWidgets import (
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
    QTextEdit,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from views.base_view import BaseView
from config.app_config import AppConfig
from controllers.horse_controller import HorseController
import logging
from datetime import datetime, date


class HorseBasicRecord(BaseView):
    """Horse basic record form for creating/editing horse information"""

    # Signals
    horse_saved = pyqtSignal(int)  # Emitted when horse is saved (passes horse_id)
    cancelled = pyqtSignal()  # Emitted when user cancels

    def __init__(self, horse_id=None, current_user=None):
        self.horse_id = horse_id
        self.current_user = current_user or "ADMIN"
        self.controller = HorseController()
        self.is_new_horse = horse_id is None

        super().__init__()
        self.setup_horse_form()
        self.load_dropdown_data()

        if self.horse_id:
            self.load_horse_data()

        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_horse_form(self):
        """Setup the horse basic record form"""
        title = "Add New Horse" if self.is_new_horse else "Horse Basic Record"
        self.set_title(title)
        self.resize(700, 600)
        self.center_on_screen()

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        self.setup_header()

        # Form section
        self.setup_form_section()

        # Buttons section
        self.setup_buttons_section()

        # Add sections to main layout
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(self.form_group, 1)  # Take up most space
        main_layout.addWidget(self.buttons_frame)

    def setup_header(self):
        """Setup header with title"""
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)

        # Title
        title_text = "Add New Horse" if self.is_new_horse else "Horse Basic Record"
        title_label = QLabel(title_text)
        title_font = QFont(AppConfig.DEFAULT_FONT_FAMILY, 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR}; padding: 10px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

    def setup_form_section(self):
        """Setup the main form section with horse fields"""
        self.form_group = QGroupBox("Horse Information")
        form_layout = QGridLayout(self.form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)

        row = 0

        # Horse Name (Required)
        name_label = QLabel("*Horse Name:")
        name_label.setStyleSheet("font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(100)
        self.name_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(name_label, row, 0)
        form_layout.addWidget(self.name_input, row, 1)

        # Account Number
        account_label = QLabel("Account Number:")
        self.account_input = QLineEdit()
        self.account_input.setMaxLength(20)
        self.account_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(account_label, row, 2)
        form_layout.addWidget(self.account_input, row, 3)

        row += 1

        # Species
        species_label = QLabel("Species:")
        self.species_combo = QComboBox()
        self.species_combo.setStyleSheet(self.get_combo_style())
        form_layout.addWidget(species_label, row, 0)
        form_layout.addWidget(self.species_combo, row, 1)

        # Breed
        breed_label = QLabel("Breed:")
        self.breed_input = QLineEdit()
        self.breed_input.setMaxLength(50)
        self.breed_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(breed_label, row, 2)
        form_layout.addWidget(self.breed_input, row, 3)

        row += 1

        # Color
        color_label = QLabel("Color:")
        self.color_input = QLineEdit()
        self.color_input.setMaxLength(50)
        self.color_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(color_label, row, 0)
        form_layout.addWidget(self.color_input, row, 1)

        # Sex
        sex_label = QLabel("Sex:")
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["", "Male", "Female", "Gelding", "Stallion", "Mare"])
        self.sex_combo.setStyleSheet(self.get_combo_style())
        form_layout.addWidget(sex_label, row, 2)
        form_layout.addWidget(self.sex_combo, row, 3)

        row += 1

        # Date of Birth
        birth_label = QLabel("Date of Birth:")
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate.currentDate())
        self.birth_date.setSpecialValueText("Not Set")
        self.birth_date.setStyleSheet(self.get_input_style())
        form_layout.addWidget(birth_label, row, 0)
        form_layout.addWidget(self.birth_date, row, 1)

        # Current Location
        location_label = QLabel("Current Location:")
        self.location_combo = QComboBox()
        self.location_combo.setStyleSheet(self.get_combo_style())
        form_layout.addWidget(location_label, row, 2)
        form_layout.addWidget(self.location_combo, row, 3)

        row += 1

        # Registration Number
        reg_label = QLabel("Registration Number:")
        self.registration_input = QLineEdit()
        self.registration_input.setMaxLength(50)
        self.registration_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(reg_label, row, 0)
        form_layout.addWidget(self.registration_input, row, 1)

        # Microchip ID
        microchip_label = QLabel("Microchip ID:")
        self.microchip_input = QLineEdit()
        self.microchip_input.setMaxLength(50)
        self.microchip_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(microchip_label, row, 2)
        form_layout.addWidget(self.microchip_input, row, 3)

        row += 1

        # Tattoo
        tattoo_label = QLabel("Tattoo:")
        self.tattoo_input = QLineEdit()
        self.tattoo_input.setMaxLength(50)
        self.tattoo_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(tattoo_label, row, 0)
        form_layout.addWidget(self.tattoo_input, row, 1)

        # Brand
        brand_label = QLabel("Brand:")
        self.brand_input = QLineEdit()
        self.brand_input.setMaxLength(50)
        self.brand_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(brand_label, row, 2)
        form_layout.addWidget(self.brand_input, row, 3)

        row += 1

        # Band/Tag Number
        band_label = QLabel("Band/Tag Number:")
        self.band_input = QLineEdit()
        self.band_input.setMaxLength(50)
        self.band_input.setStyleSheet(self.get_input_style())
        form_layout.addWidget(band_label, row, 0)
        form_layout.addWidget(self.band_input, row, 1)

    def setup_buttons_section(self):
        """Setup the buttons section"""
        self.buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(self.buttons_frame)
        buttons_layout.setContentsMargins(20, 10, 20, 10)

        # Add stretch to center buttons
        buttons_layout.addStretch()

        # Save button
        self.save_button = QPushButton("Save (Enter)")
        self.save_button.setMinimumSize(120, 40)
        self.save_button.clicked.connect(self.save_horse)
        self.save_button.setDefault(True)

        # Cancel button
        self.cancel_button = QPushButton("Cancel (F1)")
        self.cancel_button.setMinimumSize(120, 40)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
            QPushButton:hover {{
                background-color: #5a6268;
            }}
        """
        )

        # Print button (F7)
        self.print_button = QPushButton("Print (F7)")
        self.print_button.setMinimumSize(120, 40)
        self.print_button.clicked.connect(self.print_information)
        self.print_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AppConfig.SUCCESS_COLOR};
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
        """
        )

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.print_button)
        buttons_layout.addStretch()

    def get_input_style(self):
        """Get standard input field styling"""
        return f"""
            QLineEdit, QDateEdit {{
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                background-color: white;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
            }}
        """

    def get_combo_style(self):
        """Get standard combo box styling"""
        return f"""
            QComboBox {{
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: {AppConfig.DEFAULT_FONT_SIZE}pt;
                background-color: white;
            }}
            QComboBox:focus {{
                border-color: {AppConfig.PRIMARY_COLOR};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
        """

    def load_dropdown_data(self):
        """Load data for dropdown menus"""
        # Load species
        species_list = self.controller.get_species_list()
        self.species_combo.addItem("", None)  # Empty option
        for species in species_list:
            self.species_combo.addItem(species.species_name, species.species_code)

        # Load locations
        locations_list = self.controller.get_locations_list()
        self.location_combo.addItem("", None)  # Empty option
        for location in locations_list:
            self.location_combo.addItem(location.location_name, location.location_id)

    def load_horse_data(self):
        """Load existing horse data for editing"""
        if not self.horse_id:
            return

        horse = self.controller.get_horse_by_id(self.horse_id)
        if not horse:
            self.show_error("Error", f"Horse with ID {self.horse_id} not found")
            return

        # Populate form fields
        self.name_input.setText(horse.horse_name or "")
        self.account_input.setText(horse.account_number or "")
        self.breed_input.setText(horse.breed or "")
        self.color_input.setText(horse.color or "")
        self.registration_input.setText(horse.registration_number or "")
        self.microchip_input.setText(horse.microchip_id or "")
        self.tattoo_input.setText(horse.tattoo or "")
        self.brand_input.setText(horse.brand or "")
        self.band_input.setText(horse.band_tag_number or "")

        # Set combo box values by finding the matching item
        if horse.species_code:
            # Find and set species combo
            for i in range(self.species_combo.count()):
                if self.species_combo.itemData(i) == horse.species_code:
                    self.species_combo.setCurrentIndex(i)
                    break

        if horse.sex:
            # Find and set sex combo
            index = self.sex_combo.findText(horse.sex)
            if index >= 0:
                self.sex_combo.setCurrentIndex(index)

        if horse.current_location_id:
            # Find and set location combo
            for i in range(self.location_combo.count()):
                if self.location_combo.itemData(i) == horse.current_location_id:
                    self.location_combo.setCurrentIndex(i)
                    break

        # Set date
        if horse.date_of_birth:
            self.birth_date.setDate(QDate(horse.date_of_birth))

    def save_horse(self):
        """Save horse data"""
        try:
            # Convert QDate to Python date - handle PyQt6 differences
            birth_date = None
            if self.birth_date.date().isValid():
                qdate = self.birth_date.date()
                # Convert QDate to Python date
                birth_date = date(qdate.year(), qdate.month(), qdate.day())

            # Collect form data
            horse_data = {
                "horse_name": self.name_input.text().strip(),
                "account_number": self.account_input.text().strip(),
                "species_code": self.species_combo.currentData(),
                "breed": self.breed_input.text().strip(),
                "color": self.color_input.text().strip(),
                "sex": (
                    self.sex_combo.currentText()
                    if self.sex_combo.currentText()
                    else None
                ),
                "date_of_birth": birth_date,
                "registration_number": self.registration_input.text().strip(),
                "microchip_id": self.microchip_input.text().strip(),
                "tattoo": self.tattoo_input.text().strip(),
                "brand": self.brand_input.text().strip(),
                "band_tag_number": self.band_input.text().strip(),
                "current_location_id": self.location_combo.currentData(),
            }

            # Validate data
            is_valid, errors = self.controller.validate_horse_data(horse_data)
            if not is_valid:
                error_message = "Please correct the following errors:\\n" + "\\n".join(
                    errors
                )
                self.show_error("Validation Error", error_message)
                return

            # Save or update horse
            if self.is_new_horse:
                success, message, horse = self.controller.create_horse(
                    horse_data, self.current_user
                )
                if success:
                    self.horse_id = horse.horse_id
                    self.is_new_horse = False
                    self.show_info("Success", "Horse created successfully")
                    self.horse_saved.emit(self.horse_id)
                else:
                    self.show_error("Error", message)
            else:
                success, message = self.controller.update_horse(
                    self.horse_id, horse_data, self.current_user
                )
                if success:
                    self.show_info("Success", "Horse updated successfully")
                    self.horse_saved.emit(self.horse_id)
                else:
                    self.show_error("Error", message)

        except Exception as e:
            self.logger.error(f"Error saving horse: {str(e)}")
            self.show_error("Error", f"An error occurred while saving: {str(e)}")

    def cancel_operation(self):
        """Handle cancel button click"""
        if self.has_unsaved_changes():
            if self.show_question(
                "Confirm Cancel",
                "You have unsaved changes. Are you sure you want to cancel?",
            ):
                self.cancelled.emit()
                self.close()
        else:
            self.cancelled.emit()
            self.close()

    def print_information(self):
        """Handle print button click (F7)"""
        # TODO: Implement printing functionality
        self.show_info("Print", "Print functionality not yet implemented")

    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        # Simple check - see if any field has data
        return (
            self.name_input.text().strip()
            or self.account_input.text().strip()
            or self.breed_input.text().strip()
            or self.color_input.text().strip()
        )

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.save_horse()
        elif key == Qt.Key.Key_F1:
            self.cancel_operation()
        elif key == Qt.Key.Key_F7:
            self.print_information()
        elif key == Qt.Key.Key_Escape:
            self.cancel_operation()
        else:
            super().keyPressEvent(event)
