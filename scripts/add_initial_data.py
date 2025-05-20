# scripts/add_initial_data.py

"""
EDSI Veterinary Management System - Initial Data Setup
Version: 1.1.0
Purpose: Adds initial reference data and a default admin user to the database.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.0 (2025-05-18):
    - Added function to create a default admin user ('ADMIN' with a
      default password) if one does not already exist.
    - Imported User model and hashlib for password hashing.
    - Ensured all model imports are present for table creation checks by db_manager.
- v1.0.0 (2025-05-12): Initial implementation
  - Added sample species data
  - Added sample locations
  - Added sample charge codes
  - Added sample veterinarians
  - Added sample states/provinces
"""

import sys
import os
import hashlib  # Added for password hashing
import logging  # Added for better logging

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager

# Import all models that this script interacts with or that are needed for db setup
from models import (
    Species,
    StateProvince,
    ChargeCode,
    Veterinarian,
    Location,
    User,
    Role,
    UserRole,  # Added User, Role, UserRole
    Horse,
    Owner,
    HorseOwner,
    Transaction,
    TransactionDetail,
    Invoice,
    Procedure,
    Drug,
    TreatmentLog,
    CommunicationLog,
    Document,
    Reminder,
    Appointment,
    SystemConfig,
    HorseLocation,
    HorseBilling,
    OwnerBillingHistory,
    OwnerPayment,
)
from config.app_config import (
    LOG_DIR,
    APP_LOG_FILE,
    LOGGING_LEVEL,
)  # For direct logging setup if needed

# Setup basic logging for the script
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    log_file_path = os.path.join(LOG_DIR, "add_initial_data.log")
    handler = logging.FileHandler(log_file_path, mode="a")  # Append mode
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(LOGGING_LEVEL)  # Use level from app_config

    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def _hash_password(password: str) -> str:
    """Hashes a password using SHA-256. Matches UserController logic."""
    return hashlib.sha256(password.lower().encode("utf-8")).hexdigest()


def add_default_admin_user(session):
    """Adds a default admin user if one doesn't exist."""
    admin_user_id = "ADMIN"
    admin_username = "System Administrator"
    # IMPORTANT: This default password should be changed immediately after first login.
    admin_password = "admin1234"

    try:
        existing_admin = (
            session.query(User).filter(User.user_id == admin_user_id).first()
        )
        if not existing_admin:
            hashed_password = _hash_password(admin_password)
            admin_user = User(
                user_id=admin_user_id,
                user_name=admin_username,
                password_hash=hashed_password,
                is_active=True,
            )
            session.add(admin_user)
            session.commit()  # Commit user creation separately
            logger.info(f"Default admin user '{admin_user_id}' created successfully.")
        else:
            logger.info(
                f"Admin user '{admin_user_id}' already exists. No action taken for user creation."
            )
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default admin user: {e}", exc_info=True)
        # Do not re-raise here, allow other data addition to proceed if possible


def add_initial_data():
    """Add initial reference data to the database"""
    logger.info("Starting to add initial reference data...")

    try:
        # Initialize database (this will also call create_tables if db file doesn't exist or manager not init)
        db_manager.initialize_database()  # Uses DATABASE_URL from app_config
        logger.info("Database initialized by db_manager.")
    except Exception as e:
        logger.critical(
            f"Failed to initialize database via db_manager: {e}", exc_info=True
        )
        print(
            f"CRITICAL: Database initialization failed: {e}. Cannot proceed.",
            file=sys.stderr,
        )
        return  # Stop if DB can't be initialized

    session = None
    try:
        session = db_manager.get_session()
        logger.info("Database session obtained.")

        # 1. Add Default Admin User
        logger.info("Attempting to add/verify default admin user...")
        add_default_admin_user(session)  # session.commit() is inside this function

        # 2. Add species
        logger.info("Adding species data...")
        species_data = [
            ("EQ", "Equine"),
            ("BO", "Bovine"),
            ("CA", "Canine"),
            ("FE", "Feline"),
            ("OV", "Ovine"),
            ("PO", "Porcine"),
            ("AV", "Avian"),
        ]
        for code, name in species_data:
            # In models, Species PK is species_id (auto-increment), name is unique.
            # Let's assume 'name' is the primary way to check for existence here if code isn't a direct field.
            # Current Species model has species_id (auto), name (unique), description.
            # If the old COBOL system used 'code', this script needs adjustment or the model does.
            # For now, assuming 'name' is the key identifier for checking.
            # Let's assume the model has 'species_code' and 'species_name' for now as per original script intent.
            # If Species model is: species_id (PK), name, description
            # then:
            if not session.query(Species).filter(Species.name == name).first():
                # species = Species(name=name, description=f"Species code was {code}") # Example if code is just for description
                # Assuming the model is: species_id, species_code, species_name
                # The current model `reference_models.py` has `species_id, name, description`.
                # The original `add_initial_data.py` had `species_code`, `species_name` for `Species`.
                # Let's stick to the current model `Species(name=name, description=description)`.
                # The provided `species_data` has `code` and `name`. I will assume `name` is `Species.name`
                # and `code` could be part of the description or a separate (now non-existent) field.
                # For safety, I'll use the `name` field from `species_data` for `Species.name`.
                species = Species(
                    name=name, description=f"Original code reference: {code}"
                )
                session.add(species)
        logger.info("Species data processed.")

        # 3. Add states/provinces
        logger.info("Adding states/provinces data...")
        states_data = [
            ("AL", "Alabama", "USA"),
            ("AK", "Alaska", "USA"),
            ("AZ", "Arizona", "USA"),
            ("AR", "Arkansas", "USA"),
            ("CA", "California", "USA"),
            ("CO", "Colorado", "USA"),
            ("CT", "Connecticut", "USA"),
            ("DE", "Delaware", "USA"),
            ("FL", "Florida", "USA"),
            ("GA", "Georgia", "USA"),
            ("HI", "Hawaii", "USA"),
            ("ID", "Idaho", "USA"),
            ("IL", "Illinois", "USA"),
            ("IN", "Indiana", "USA"),
            ("IA", "Iowa", "USA"),
            ("KS", "Kansas", "USA"),
            ("KY", "Kentucky", "USA"),  # Add KY
            ("LA", "Louisiana", "USA"),
            ("ME", "Maine", "USA"),
            ("MD", "Maryland", "USA"),
            ("MA", "Massachusetts", "USA"),
            ("MI", "Michigan", "USA"),
            ("MN", "Minnesota", "USA"),
            ("MS", "Mississippi", "USA"),
            ("MO", "Missouri", "USA"),
            ("MT", "Montana", "USA"),
            ("NE", "Nebraska", "USA"),
            ("NV", "Nevada", "USA"),
            ("NH", "New Hampshire", "USA"),
            ("NJ", "New Jersey", "USA"),
            ("NM", "New Mexico", "USA"),
            ("NY", "New York", "USA"),
            ("NC", "North Carolina", "USA"),
            ("ND", "North Dakota", "USA"),
            ("OH", "Ohio", "USA"),
            ("OK", "Oklahoma", "USA"),
            ("OR", "Oregon", "USA"),
            ("PA", "Pennsylvania", "USA"),
            ("RI", "Rhode Island", "USA"),
            ("SC", "South Carolina", "USA"),
            ("SD", "South Dakota", "USA"),
            ("TN", "Tennessee", "USA"),
            ("TX", "Texas", "USA"),
            ("UT", "Utah", "USA"),
            ("VT", "Vermont", "USA"),
            ("VA", "Virginia", "USA"),
            ("WA", "Washington", "USA"),
            ("WV", "West Virginia", "USA"),
            ("WI", "Wisconsin", "USA"),
            ("WY", "Wyoming", "USA"),
            # Add Canadian provinces or other regions if needed
            ("ON", "Ontario", "CAN"),
            ("QC", "Quebec", "CAN"),
        ]

        for code, name, country in states_data:
            if (
                not session.query(StateProvince)
                .filter(StateProvince.state_code == code)
                .first()
            ):
                state = StateProvince(
                    state_code=code, state_name=name, country_code=country
                )
                session.add(state)
        logger.info("States/provinces data processed.")

        # 4. Add sample locations
        logger.info("Adding sample locations data...")
        locations_data = [
            # (name, addr1, addr2, city, state_code, zip_code, description, is_active)
            (
                "Main Barn",
                "123 Farm Road",
                "",
                "Lexington",
                "KY",
                "40508",
                "Primary stabling barn",
                True,
            ),
            (
                "Paddock A",
                "Front Pasture",
                "",
                "Lexington",
                "KY",
                "40508",
                "Turnout paddock A",
                True,
            ),
            (
                "Quarantine Barn",
                "Isolation Area",
                "",
                "Lexington",
                "KY",
                "40508",
                "For new or sick horses",
                True,
            ),
        ]
        for (
            name,
            addr1,
            addr2,
            city,
            state_code_loc,
            zip_code,
            desc,
            active,
        ) in locations_data:
            if (
                not session.query(Location)
                .filter(Location.location_name == name)
                .first()
            ):
                # The Location model now has a description field.
                # The original script did not provide values for description or is_active directly.
                # I'm adding them based on common sense for sample data.
                # State code for location needs to exist in StateProvince table.
                state_obj = (
                    session.query(StateProvince)
                    .filter(StateProvince.state_code == state_code_loc)
                    .first()
                )
                if not state_obj:
                    logger.warning(
                        f"State code '{state_code_loc}' for location '{name}' not found. Skipping location."
                    )
                    continue

                location = Location(
                    location_name=name,
                    # The model Location in reference_models.py does not have address fields.
                    # It has: location_id, location_name, description, is_active
                    # I will use addr1 as part of description.
                    description=f"{addr1} {addr2}, {city}, {state_code_loc} {zip_code}. {desc}".strip(
                        ", . "
                    ),
                    is_active=active,
                )
                session.add(location)
        logger.info("Sample locations data processed.")

        # 5. Add sample charge codes
        logger.info("Adding sample charge codes data...")
        charge_codes_data = [
            # code, alternate_code, description, category, standard_charge, is_active
            ("EXAM", "E001", "Routine Examination", "Veterinary", 75.00, True),
            ("VACC", "V001", "Standard Vaccination", "Veterinary", 45.00, True),
            ("BOARD", "B001", "Daily Boarding Fee", "Boarding", 35.00, True),
            (
                "FC",
                "FARMCL",
                "Farm Call - Standard",
                "Veterinary - Call Fees",
                60.00,
                True,
            ),
        ]
        for code, alt_code, desc, category, charge, active in charge_codes_data:
            if not session.query(ChargeCode).filter(ChargeCode.code == code).first():
                charge_item = ChargeCode(
                    code=code,
                    alternate_code=alt_code,
                    description=desc,
                    category=category,
                    standard_charge=charge,
                    is_active=active,
                )
                session.add(charge_item)
        logger.info("Sample charge codes data processed.")

        # 6. Add sample veterinarians
        logger.info("Adding sample veterinarians data...")
        vets_data = [
            # first_name, last_name, license_number, phone, email, is_active
            ("Sarah", "Johnson", "DVM001", "555-0101", "s.johnson@example.com", True),
            (
                "Michael",
                "Williams",
                "DVM002",
                "555-0102",
                "m.williams@example.com",
                True,
            ),
        ]
        for fname, lname, lic, phone, email, active in vets_data:
            # Veterinarian model has vet_id (auto), first_name, last_name, license_number, etc.
            if (
                not session.query(Veterinarian)
                .filter(Veterinarian.license_number == lic)
                .first()
            ):
                vet = Veterinarian(
                    first_name=fname,
                    last_name=lname,
                    license_number=lic,
                    phone=phone,
                    email=email,
                    is_active=active,
                )
                session.add(vet)
        logger.info("Sample veterinarians data processed.")

        # Commit all other data additions
        session.commit()
        logger.info(
            "Initial reference data (species, states, locations, charges, vets) committed."
        )

    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error adding initial data: {e}", exc_info=True)
        print(
            f"Error adding initial data: {e}. Check logs for details.", file=sys.stderr
        )
    finally:
        if session:
            session.close()
            logger.info("Database session closed.")
        # db_manager.close() # close method not defined on db_manager in provided code

    logger.info("Finished adding initial reference data.")


if __name__ == "__main__":
    print("Running script to add initial data to the database...")
    add_initial_data()
    print("Script execution finished. Check logs for details.")
