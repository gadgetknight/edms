# scripts/add_initial_data.py

"""
EDSI Veterinary Management System - Initial Data Setup
Version: 1.2.3
Purpose: Adds initial reference data with more robust commits and detailed logging
         for each data type to help diagnose population issues. Corrects Owner
         instantiation by removing direct country_name argument.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.2.3 (2025-05-20):
    - Removed `country_name` as a direct keyword argument when creating `Owner`
      instances in `add_sample_owners_data` to align with the `Owner` model
      definition, which derives country information via `StateProvince`.
- v1.2.2 (2025-05-20):
    - Refactored data adding functions (species, states, locations, charge_codes,
      veterinarian, horses, owners) to include more detailed logging within
      their loops and to attempt their own session.commit().
    - This makes each data section more atomic and improves error reporting if
      a specific section fails to populate.
- v1.2.1 (2025-05-20):
    - Updated sample data for Locations, Charge Codes, Veterinarian (single entry),
      Horses, and Owners based on user-provided lists.
    - Species data addition simplified to ensure only "Equine" exists.
- v1.2.0 (2025-05-20):
    - Removed multiple species population; now adds a single "Equine" species.
    - Updated sample locations to use new detailed address fields and provided data.
"""

import sys
import os
import hashlib
import logging
from datetime import date
from decimal import Decimal

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager
from models import (
    Species,
    StateProvince,
    ChargeCode,
    Veterinarian,
    Location,
    User,
    Role,
    UserRole,
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
    OwnerPayment,
)
from config.app_config import LOG_DIR, APP_LOG_FILE, LOGGING_LEVEL

logger = logging.getLogger("add_initial_data_script")
if not logger.hasHandlers():
    log_file_path = os.path.join(LOG_DIR, "add_initial_data.log")
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = logging.FileHandler(
        log_file_path, mode="w"
    )  # Overwrite log each run for clarity
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(LOGGING_LEVEL)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.lower().encode("utf-8")).hexdigest()


def add_default_admin_user(session):
    logger.info("Processing default admin user...")
    admin_user_id = "ADMIN"
    admin_username = "System Administrator"
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
                created_by="SCRIPT",
                modified_by="SCRIPT",
            )
            session.add(admin_user)
            session.commit()
            logger.info(f"Default admin user '{admin_user_id}' created successfully.")
        else:
            logger.info(f"Admin user '{admin_user_id}' already exists.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default admin user: {e}", exc_info=True)


def add_species_data(session):
    logger.info("Processing species data (Equine only)...")
    equine_species_name = "Equine"
    items_added_count = 0
    try:
        existing_species = (
            session.query(Species).filter(Species.name == equine_species_name).first()
        )
        if not existing_species:
            equine = Species(
                name=equine_species_name,
                description="Horses",
                created_by="SCRIPT",
                modified_by="SCRIPT",
            )
            session.add(equine)
            items_added_count += 1
            logger.info(f"Staged species '{equine_species_name}'.")
        else:
            logger.info(f"Species '{equine_species_name}' already exists.")

        if items_added_count > 0:
            session.commit()
            logger.info(f"Committed {items_added_count} species item(s).")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing species data: {e}", exc_info=True)


def add_states_provinces_data(session):
    logger.info("Adding states/provinces data...")
    states_data = [
        ("NJ", "New Jersey", "USA", True),
        ("NY", "New York", "USA", True),
        ("PA", "Pennsylvania", "USA", True),
        ("DE", "Delaware", "USA", True),
        ("MD", "Maryland", "USA", True),
        ("AL", "Alabama", "USA", True),
        ("AK", "Alaska", "USA", True),
        ("AZ", "Arizona", "USA", True),
        ("AR", "Arkansas", "USA", True),
        ("CA", "California", "USA", True),
        ("CO", "Colorado", "USA", True),
        ("CT", "Connecticut", "USA", True),
        ("FL", "Florida", "USA", True),
        ("GA", "Georgia", "USA", True),
        ("HI", "Hawaii", "USA", True),
        ("ID", "Idaho", "USA", True),
        ("IL", "Illinois", "USA", True),
        ("IN", "Indiana", "USA", True),
        ("IA", "Iowa", "USA", True),
        ("KS", "Kansas", "USA", True),
        ("KY", "Kentucky", "USA", True),
        ("LA", "Louisiana", "USA", True),
        ("ME", "Maine", "USA", True),
        ("MA", "Massachusetts", "USA", True),
        ("MI", "Michigan", "USA", True),
        ("MN", "Minnesota", "USA", True),
        ("MS", "Mississippi", "USA", True),
        ("MO", "Missouri", "USA", True),
        ("MT", "Montana", "USA", True),
        ("NE", "Nebraska", "USA", True),
        ("NV", "Nevada", "USA", True),
        ("NH", "New Hampshire", "USA", True),
        ("NM", "New Mexico", "USA", True),
        ("NC", "North Carolina", "USA", True),
        ("ND", "North Dakota", "USA", True),
        ("OH", "Ohio", "USA", True),
        ("OK", "Oklahoma", "USA", True),
        ("OR", "Oregon", "USA", True),
        ("RI", "Rhode Island", "USA", True),
        ("SC", "South Carolina", "USA", True),
        ("SD", "South Dakota", "USA", True),
        ("TN", "Tennessee", "USA", True),
        ("TX", "Texas", "USA", True),
        ("UT", "Utah", "USA", True),
        ("VT", "Vermont", "USA", True),
        ("VA", "Virginia", "USA", True),
        ("WA", "Washington", "USA", True),
        ("WV", "West Virginia", "USA", True),
        ("WI", "Wisconsin", "USA", True),
        ("WY", "Wyoming", "USA", True),
        ("ON", "Ontario", "CAN", True),
        ("QC", "Quebec", "CAN", True),
    ]
    items_to_add = []
    try:
        for code, name, country, is_active_val in states_data:
            if (
                not session.query(StateProvince)
                .filter(StateProvince.state_code == code)
                .first()
            ):
                state = StateProvince(
                    state_code=code,
                    state_name=name,
                    country_code=country,
                    is_active=is_active_val,
                    created_by="SCRIPT",
                    modified_by="SCRIPT",
                )
                items_to_add.append(state)
                logger.info(f"Staging State/Province: {code} - {name}")
            else:
                logger.info(f"State/Province {code} - {name} already exists. Skipping.")
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Committed {len(items_to_add)} new states/provinces.")
        else:
            logger.info("No new states/provinces to add.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing states/provinces data: {e}", exc_info=True)


def add_sample_locations_data(session):
    logger.info("Adding sample locations data...")
    locations_data = [
        (
            "Gaited Farms",
            "204 Carranza Rd.",
            None,
            "Tabernacle",
            "NJ",
            "08088",
            "Amy Redman",
            "609-785-1634",
            True,
            None,
            "USA",
        ),
        (
            "Beacon Hill",
            "55 Laird Rd.",
            None,
            "Colts Neck",
            "NJ",
            "07722",
            "George Wilson",
            "732-332-0880",
            True,
            None,
            "USA",
        ),
        (
            "Hayfever Farms",
            "334 Tom Brown Rd.",
            None,
            "Moorestown",
            "NJ",
            "08057",
            "Ralph Hayes",
            "856-789-1286",
            True,
            None,
            "USA",
        ),
    ]
    items_to_add = []
    try:
        for (
            name,
            addr1,
            addr2,
            city,
            state_code_loc,
            zip_code,
            contact,
            phone,
            active,
            email,
            country,
        ) in locations_data:
            if (
                not session.query(Location)
                .filter(Location.location_name == name)
                .first()
            ):
                state_obj = (
                    session.query(StateProvince)
                    .filter(StateProvince.state_code == state_code_loc)
                    .first()
                )
                if not state_obj:
                    logger.warning(
                        f"State code '{state_code_loc}' for location '{name}' not found. Skipping this location."
                    )
                    continue
                location = Location(
                    location_name=name,
                    address_line1=addr1,
                    address_line2=addr2,
                    city=city,
                    state_code=state_code_loc,
                    zip_code=zip_code,
                    country_code=country if country else state_obj.country_code,
                    phone=phone,
                    email=email,
                    contact_person=contact,
                    is_active=active,
                    description=f"{name} at {addr1}",
                    created_by="SCRIPT",
                    modified_by="SCRIPT",
                )
                items_to_add.append(location)
                logger.info(f"Staging Location: {name}")
            else:
                logger.info(f"Location {name} already exists. Skipping.")
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Committed {len(items_to_add)} new locations.")
        else:
            logger.info("No new locations to add.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing sample locations data: {e}", exc_info=True)


def add_sample_charge_codes_data(session):
    logger.info("Adding sample charge codes data...")
    charge_codes_data = [
        (
            "413",
            "PWBEN",
            "Paste Worm with Benzelmin",
            "Veterinary Anthelmintics Administered",
            14.00,
            True,
        ),
        ("650", "AF", "Attend Foaling", "Veterinary Call Fees", 100.00, True),
        (
            "100",
            "FC",
            "Farm Call",
            "Veterinary Call Fees",
            100.00,
            True,
        ),  # Note: PDF/CSV differ for this. Using script's value.
        (
            "32",
            "BLBS",
            "Diagnostic Basisesmoid Nerve Block",
            "Veterinary Diagnostic Procedures Nerve Blocks",
            50.00,
            True,
        ),
    ]
    items_to_add = []
    try:
        for code, alt_code, desc, category, charge, active in charge_codes_data:
            if not session.query(ChargeCode).filter(ChargeCode.code == code).first():
                charge_item = ChargeCode(
                    code=code,
                    alternate_code=alt_code,
                    description=desc,
                    category=category,
                    standard_charge=Decimal(str(charge)),
                    is_active=active,
                    created_by="SCRIPT",
                    modified_by="SCRIPT",
                )
                items_to_add.append(charge_item)
                logger.info(f"Staging ChargeCode: {code}")
            else:
                logger.info(f"ChargeCode {code} already exists. Skipping.")
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Committed {len(items_to_add)} new charge codes.")
        else:
            logger.info("No new charge codes to add.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing sample charge codes data: {e}", exc_info=True)


def add_sample_veterinarian_data(session):
    logger.info("Adding single veterinarian data...")
    vet_data = {
        "first_name": "Michael",
        "last_name": "Williams",
        "license_number": "DVM002",
        "phone": "856-555-0102",
        "email": "m.williams@example.com",
        "is_active": True,
    }
    items_added_count = 0
    try:
        existing_vet = (
            session.query(Veterinarian)
            .filter(Veterinarian.license_number == vet_data["license_number"])
            .first()
        )
        if not existing_vet:
            vet = Veterinarian(
                first_name=vet_data["first_name"],
                last_name=vet_data["last_name"],
                license_number=vet_data["license_number"],
                phone=vet_data["phone"],
                email=vet_data["email"],
                is_active=vet_data["is_active"],
                created_by="SCRIPT",
                modified_by="SCRIPT",
            )
            session.add(vet)
            items_added_count += 1
            logger.info(
                f"Staging Veterinarian: {vet_data['first_name']} {vet_data['last_name']}"
            )
        else:
            logger.info(
                f"Veterinarian with license '{vet_data['license_number']}' already exists."
            )

        if items_added_count > 0:
            session.commit()
            logger.info(f"Committed {items_added_count} veterinarian item(s).")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing veterinarian data: {e}", exc_info=True)


def add_sample_horses_data(session):
    logger.info("Adding sample horses data...")
    equine_species = session.query(Species).filter(Species.name == "Equine").first()
    if not equine_species:
        logger.error("Could not find 'Equine' species. Skipping horse creation.")
        return
    equine_species_id = equine_species.species_id

    horses_data = [
        ("Donatello", "011884"),
        ("Lorena 90", "006345"),
        ("Soul Rebel", "002356"),
        ("Daisy", "008243"),
        ("Thunder", "009456"),
        ("Thunderblade", "886302"),
        ("Ironheart", "330291"),
    ]
    items_to_add = []
    try:
        for name, acc_num in horses_data:
            if (
                not session.query(Horse)
                .filter(Horse.horse_name == name, Horse.account_number == acc_num)
                .first()
            ):
                horse = Horse(
                    horse_name=name,
                    account_number=acc_num,
                    species_id=equine_species_id,
                    is_active=True,
                    created_by="SCRIPT",
                    modified_by="SCRIPT",
                )
                items_to_add.append(horse)
                logger.info(f"Staging Horse: {name}")
            else:
                logger.info(
                    f"Horse {name} with account {acc_num} already exists. Skipping."
                )
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Committed {len(items_to_add)} new horses.")
        else:
            logger.info("No new horses to add.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing sample horses data: {e}", exc_info=True)


def add_sample_owners_data(session):
    logger.info("Adding sample owners data...")
    owners_data = [
        {
            "full_name": "Amy Reed",
            "address1": "22 Carrigan Rd.",
            "city_state_zip": "Medford, NJ 08055",
            # "country": "USA", # Country is derived from StateProvince
            "phone": "609-640-9823",
        },
        {
            "full_name": "Brian Walsh",
            "address1": "301 Westminster Blvd",
            "city_state_zip": "Colts Neck, NJ 07093",
            # "country": "USA",
            "phone": "732-983-3029",
        },
        {
            "full_name": "Sam White",
            "address1": "457 White Birch Rd",
            "city_state_zip": "Sewell, NJ 08002",
            # "country": "USA",
            "phone": "609-823-0923",
        },
        {
            "full_name": "John Hill",
            "address1": "30 Laird Rd",
            "city_state_zip": "Moorestown, NJ 08057",
            # "country": "USA",
            "phone": "856-302-9899",
        },
    ]
    items_to_add = []
    try:
        for owner_entry in owners_data:
            name_parts = owner_entry["full_name"].split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else None

            city_state_zip_parts = owner_entry["city_state_zip"].split(",")
            city = (
                city_state_zip_parts[0].strip() if len(city_state_zip_parts) > 0 else ""
            )
            state_code = ""
            zip_code = ""
            if len(city_state_zip_parts) > 1:
                state_zip_part = city_state_zip_parts[1].strip().split(" ")
                state_code = state_zip_part[0].strip()
                zip_code = state_zip_part[1].strip() if len(state_zip_part) > 1 else ""

            query = session.query(Owner).filter(Owner.phone == owner_entry["phone"])
            if first_name:
                query = query.filter(Owner.first_name == first_name)
            if last_name:
                query = query.filter(Owner.last_name == last_name)

            if not query.first():
                if not state_code:
                    logger.warning(
                        f"Could not parse state code for owner '{owner_entry['full_name']}'. Skipping this owner."
                    )
                    continue
                state_obj = (
                    session.query(StateProvince)
                    .filter(StateProvince.state_code == state_code)
                    .first()
                )
                if not state_obj:
                    logger.warning(
                        f"State code '{state_code}' for owner '{owner_entry['full_name']}' not found. Skipping this owner."
                    )
                    continue

                owner = Owner(
                    first_name=first_name,
                    last_name=last_name,
                    address_line1=owner_entry["address1"],
                    city=city,
                    state_code=state_code,  # This links to StateProvince, which has country_code
                    zip_code=zip_code,
                    # Removed country_name=owner_entry["country"],
                    phone=owner_entry["phone"],
                    is_active=True,
                    created_by="SCRIPT",
                    modified_by="SCRIPT",
                )
                items_to_add.append(owner)
                logger.info(f"Staging Owner: {owner_entry['full_name']}")
            else:
                logger.info(
                    f"Owner {owner_entry['full_name']} with phone {owner_entry['phone']} already exists. Skipping."
                )
        if items_to_add:
            session.add_all(items_to_add)
            session.commit()
            logger.info(f"Committed {len(items_to_add)} new owners.")
        else:
            logger.info("No new owners to add.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing sample owners data: {e}", exc_info=True)


def add_initial_data():
    logger.info("Starting to add initial reference data...")
    try:
        db_manager.initialize_database()  # This also calls create_tables if DB doesn't exist
        logger.info("Database initialized by db_manager.")
    except Exception as e:
        logger.critical(
            f"Failed to initialize database via db_manager: {e}", exc_info=True
        )
        print(
            f"CRITICAL: Database initialization failed: {e}. Cannot proceed.",
            file=sys.stderr,
        )
        return

    session = None
    try:
        session = db_manager.get_session()
        logger.info("Database session obtained.")

        # Each function now handles its own commit/rollback for its specific data type
        add_default_admin_user(session)
        add_species_data(session)
        add_states_provinces_data(session)
        add_sample_locations_data(session)
        add_sample_charge_codes_data(session)
        add_sample_veterinarian_data(session)
        add_sample_horses_data(session)
        add_sample_owners_data(session)

        logger.info("All initial data processing functions called.")

    except Exception as e:
        # This broad exception is a fallback if something outside the helper functions fails
        # or if a helper re-raises an exception (which they currently don't).
        if session:  # Ensure session exists before trying to rollback
            session.rollback()
        logger.error(
            f"Critical error during main initial data addition sequence: {e}",
            exc_info=True,
        )
        print(
            f"Critical error adding initial data: {e}. Check logs for details.",
            file=sys.stderr,
        )
    finally:
        if session:
            session.close()
            logger.info("Database session closed.")
    logger.info("Finished add_initial_data script.")


if __name__ == "__main__":
    print("Running script to add initial data to the database...")
    add_initial_data()
    print("Script execution finished. Check logs for details and potential warnings.")
