# scripts/add_initial_data.py
"""
EDSI Veterinary Management System - Add Initial Data Script
Version: 1.2.10
Purpose: Populates the database with essential initial data for application setup.
         - Changed default admin password to 'admin1234'.
Last Updated: May 23, 2025
Author: Gemini

Changelog:
- v1.2.10 (2025-05-23):
    - Changed default admin password in `add_admin_user` to "admin1234".
      The username stored in the DB remains "ADMIN".
- v1.2.9 (2025-05-23):
    - Removed `Species` from model imports.
    - Removed `add_species` function entirely.
    - Removed the call to `add_species(session)` from `add_initial_data_main`.
- v1.2.8 (2025-05-23):
    - Modified `add_admin_user` to create User instance then call `user.set_password()`
      instead of attempting to use a non-existent static `User.hash_password()` method.
"""
import logging
import os
import sys
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from config.database_config import db_manager
    from models import (
        User,
        Role,
        UserRole,
        StateProvince,
        ChargeCode,
        Veterinarian,
        Location,
        Owner,
    )

    # user_models.py (v1.1.2) has the User class with set_password
except ImportError as e:
    print(f"Error importing modules in add_initial_data.py: {e}")
    print(
        "Please ensure all necessary model files exist and models/__init__.py is correct."
    )
    sys.exit(1)

log_file_path = os.path.join(project_root, "logs", "add_initial_data.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.FileHandler(log_file_path, mode="w"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def add_roles(session):
    roles_to_add = [
        {"name": "ADMIN", "description": "Administrator with full system access."},
        {"name": "MANAGER", "description": "Manager with operational oversight."},
        {
            "name": "VETERINARIAN",
            "description": "Veterinarian providing medical services.",
        },
        {
            "name": "TECHNICIAN",
            "description": "Veterinary technician assisting with procedures.",
        },
        {
            "name": "RECEPTIONIST",
            "description": "Receptionist handling front-desk operations.",
        },
        {
            "name": "CLIENT",
            "description": "Client/Owner accessing their animal's information (future).",
        },
    ]
    for role_data in roles_to_add:
        role_data.update({"created_by": "system_init", "modified_by": "system_init"})

    existing_roles = {role[0] for role in session.query(Role.name).all()}

    new_roles = []
    for role_data in roles_to_add:
        if role_data["name"] not in existing_roles:
            new_roles.append(Role(**role_data))
            logger.info(f"Prepared role: {role_data['name']}")
        else:
            logger.info(f"Role '{role_data['name']}' already exists, skipping.")

    if new_roles:
        session.add_all(new_roles)
        logger.info(f"Successfully prepared {len(new_roles)} new roles.")
    else:
        logger.info("No new roles to add.")
    return len(new_roles) > 0


def add_admin_user(session):
    admin_login_id = "ADMIN"  # Stored as uppercase "ADMIN"
    admin_exists = session.query(User).filter_by(user_id=admin_login_id).first()
    changes_made = False

    if not admin_exists:
        admin_role = session.query(Role).filter_by(name="ADMIN").first()
        if not admin_role:
            logger.error(
                "ADMIN role not found. Cannot create admin user. Please add roles first."
            )
            return False

        admin_user = User(
            user_id=admin_login_id,  # Stored as "ADMIN"
            user_name="System Administrator",
            email="admin@edsystem.com",
            is_active=True,
            created_by="system_init",
            modified_by="system_init",
        )
        # MODIFIED: Set password to "admin1234"
        admin_user.set_password("admin1234")

        admin_user.roles.append(admin_role)
        session.add(admin_user)
        changes_made = True
        logger.info(
            f"Admin user '{admin_login_id}' prepared with default password 'admin1234' and ADMIN role."
        )
    else:
        logger.info(f"Admin user '{admin_login_id}' already exists.")
        # Optionally, update existing admin's password if desired, or ensure role is set.
        # For now, just ensuring role assignment as before.
        # If you want to forcibly reset the password every time, you could add:
        # admin_exists.set_password("admin1234")
        # admin_exists.modified_by = "system_init_pwd_reset"
        # logger.info(f"Password for existing admin user '{admin_login_id}' reset to 'admin1234'.")
        # changes_made = True

        admin_role = session.query(Role).filter_by(name="ADMIN").first()
        if admin_role and admin_role not in admin_exists.roles:
            admin_exists.roles.append(admin_role)
            admin_exists.modified_by = "system_init_role_add"
            changes_made = True
            logger.info(f"ADMIN role assigned to existing user '{admin_login_id}'.")
    return changes_made


def add_state_provinces(session):
    states_provinces_data = [
        {
            "state_code": "AL",
            "state_name": "Alabama",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "AK",
            "state_name": "Alaska",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "AZ",
            "state_name": "Arizona",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "AR",
            "state_name": "Arkansas",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "CA",
            "state_name": "California",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "CO",
            "state_name": "Colorado",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "CT",
            "state_name": "Connecticut",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "DE",
            "state_name": "Delaware",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "FL",
            "state_name": "Florida",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "GA",
            "state_name": "Georgia",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "HI",
            "state_name": "Hawaii",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "ID",
            "state_name": "Idaho",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "IL",
            "state_name": "Illinois",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "IN",
            "state_name": "Indiana",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "IA",
            "state_name": "Iowa",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "KS",
            "state_name": "Kansas",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "KY",
            "state_name": "Kentucky",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "LA",
            "state_name": "Louisiana",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "ME",
            "state_name": "Maine",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MD",
            "state_name": "Maryland",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MA",
            "state_name": "Massachusetts",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MI",
            "state_name": "Michigan",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MN",
            "state_name": "Minnesota",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MS",
            "state_name": "Mississippi",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MO",
            "state_name": "Missouri",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "MT",
            "state_name": "Montana",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NE",
            "state_name": "Nebraska",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NV",
            "state_name": "Nevada",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NH",
            "state_name": "New Hampshire",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NJ",
            "state_name": "New Jersey",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NM",
            "state_name": "New Mexico",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NY",
            "state_name": "New York",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "NC",
            "state_name": "North Carolina",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "ND",
            "state_name": "North Dakota",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "OH",
            "state_name": "Ohio",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "OK",
            "state_name": "Oklahoma",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "OR",
            "state_name": "Oregon",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "PA",
            "state_name": "Pennsylvania",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "RI",
            "state_name": "Rhode Island",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "SC",
            "state_name": "South Carolina",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "SD",
            "state_name": "South Dakota",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "TN",
            "state_name": "Tennessee",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "TX",
            "state_name": "Texas",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "UT",
            "state_name": "Utah",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "VT",
            "state_name": "Vermont",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "VA",
            "state_name": "Virginia",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "WA",
            "state_name": "Washington",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "WV",
            "state_name": "West Virginia",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "WI",
            "state_name": "Wisconsin",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "WY",
            "state_name": "Wyoming",
            "country_code": "USA",
            "is_active": True,
        },
        {
            "state_code": "AB",
            "state_name": "Alberta",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "BC",
            "state_name": "British Columbia",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "MB",
            "state_name": "Manitoba",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "NB",
            "state_name": "New Brunswick",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "NL",
            "state_name": "Newfoundland and Labrador",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "NS",
            "state_name": "Nova Scotia",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "ON",
            "state_name": "Ontario",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "PE",
            "state_name": "Prince Edward Island",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "QC",
            "state_name": "Quebec",
            "country_code": "CAN",
            "is_active": True,
        },
        {
            "state_code": "SK",
            "state_name": "Saskatchewan",
            "country_code": "CAN",
            "is_active": True,
        },
    ]
    for sp_data in states_provinces_data:
        sp_data.update({"created_by": "system_init", "modified_by": "system_init"})

    existing_codes = {sp[0] for sp in session.query(StateProvince.state_code).all()}
    new_entries = []
    for sp_data in states_provinces_data:
        if sp_data["state_code"] not in existing_codes:
            new_entries.append(StateProvince(**sp_data))
            logger.info(f"Prepared state/province: {sp_data['state_name']}")
        else:
            logger.info(
                f"State/Province '{sp_data['state_name']}' ({sp_data['state_code']}) already exists."
            )
    if new_entries:
        session.add_all(new_entries)
    return len(new_entries) > 0


def add_initial_locations(session):
    locations_to_add = [
        {
            "location_name": "Main Stable",
            "address_line1": "123 Paddock Lane",
            "city": "Equineville",
            "state_code": "PA",
            "zip_code": "19355",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "location_name": "Quarantine Barn",
            "address_line1": "456 Quarantine Rd",
            "city": "Equineville",
            "state_code": "PA",
            "zip_code": "19355",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "location_name": "West Wing Stalls",
            "address_line1": "789 Derby Drive",
            "city": "Raceburg",
            "state_code": "KY",
            "zip_code": "40511",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_locations = {loc[0] for loc in session.query(Location.location_name).all()}
    new_locations = []
    for loc_data in locations_to_add:
        if (
            loc_data.get("state_code")
            and not session.query(StateProvince)
            .filter_by(state_code=loc_data["state_code"])
            .first()
        ):
            logger.warning(
                f"State code '{loc_data['state_code']}' for location '{loc_data['location_name']}' not found. Ensure states are added first."
            )
        if loc_data["location_name"] not in existing_locations:
            new_locations.append(Location(**loc_data))
            logger.info(f"Prepared location: {loc_data['location_name']}")
        else:
            logger.info(
                f"Location '{loc_data['location_name']}' already exists, skipping."
            )
    if new_locations:
        session.add_all(new_locations)
    return len(new_locations) > 0


def add_sample_owners(session):
    owners_to_add = [
        {
            "farm_name": "Willow Creek Stables",
            "first_name": "John",
            "last_name": "Smith",
            "address_line1": "100 Willow Creek Rd",
            "city": "Lexington",
            "state_code": "KY",
            "zip_code": "40502",
            "phone": "555-0101",
            "email": "john.smith@willowcreek.com",
            "is_active": True,
            "account_number": "WC001",
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "first_name": "Sarah",
            "last_name": "Davis",
            "address_line1": "25 Horseman's Way",
            "city": "Ocala",
            "state_code": "FL",
            "zip_code": "34470",
            "phone": "555-0202",
            "email": "sarah.davis@email.com",
            "is_active": True,
            "account_number": "SD001",
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "farm_name": "Blue Ribbon Equine",
            "first_name": "Michael",
            "last_name": "Chen",
            "address_line1": "77 Jockey Circle",
            "city": "Saratoga Springs",
            "state_code": "NY",
            "zip_code": "12866",
            "phone": "555-0303",
            "email": "mchen@blueribbon.com",
            "is_active": True,
            "account_number": "BR001",
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_account_numbers = {
        owner[0]
        for owner in session.query(Owner.account_number)
        .filter(Owner.account_number.isnot(None))
        .all()
    }
    new_owners = []
    for owner_data in owners_to_add:
        if (
            owner_data.get("state_code")
            and not session.query(StateProvince)
            .filter_by(state_code=owner_data["state_code"])
            .first()
        ):
            logger.warning(
                f"State code '{owner_data['state_code']}' for owner '{owner_data.get('farm_name', owner_data.get('last_name'))}' not found."
            )
        if owner_data.get("account_number") not in existing_account_numbers:
            new_owners.append(Owner(**owner_data))
            logger.info(
                f"Prepared owner: {owner_data.get('farm_name', owner_data.get('last_name'))}"
            )
        elif owner_data.get("account_number") is None:
            new_owners.append(Owner(**owner_data))
            logger.info(
                f"Prepared owner (no account number): {owner_data.get('farm_name', owner_data.get('last_name'))}"
            )
        else:
            logger.info(
                f"Owner with account number '{owner_data['account_number']}' already exists, skipping."
            )
    if new_owners:
        session.add_all(new_owners)
    return len(new_owners) > 0


def add_sample_charge_codes(session):
    charge_codes_data = [
        {
            "code": "EXAM001",
            "description": "Routine Examination",
            "category": "Veterinary Procedure",
            "standard_charge": Decimal("75.00"),
            "is_active": True,
        },
        {
            "code": "VACC001",
            "description": "Annual Vaccination Set (5-way + Rabies)",
            "category": "Veterinary Procedure",
            "standard_charge": Decimal("120.00"),
            "is_active": True,
        },
        {
            "code": "XRAY001",
            "description": "Radiograph - 2 views",
            "category": "Diagnostic Imaging",
            "standard_charge": Decimal("150.00"),
            "is_active": True,
        },
    ]
    for cc_data in charge_codes_data:
        cc_data.update({"created_by": "system_init", "modified_by": "system_init"})

    existing_codes = {cc[0] for cc in session.query(ChargeCode.code).all()}
    new_charge_codes = []
    for data in charge_codes_data:
        if data["code"] not in existing_codes:
            new_charge_codes.append(ChargeCode(**data))
            logger.info(f"Prepared charge code: {data['code']}")
        else:
            logger.info(f"Charge code '{data['code']}' already exists, skipping.")
    if new_charge_codes:
        session.add_all(new_charge_codes)
    return len(new_charge_codes) > 0


def add_initial_data_main():
    logger.info("Running script to add initial data to the database...")
    if not db_manager:
        logger.critical("Database manager (db_manager) is not available.")
        print("CRITICAL: Database manager not initialized. Cannot proceed.")
        return

    try:
        db_manager.initialize_database()
        logger.info("Database initialized and tables created (if they didn't exist).")
    except Exception as e:
        logger.critical(
            f"Failed to initialize database via db_manager: {e}", exc_info=True
        )
        print(
            f"CRITICAL: Database initialization failed: {e}. Cannot proceed with data addition."
        )
        return

    session = db_manager.get_session()
    try:
        logger.info("Starting to add initial reference data...")
        any_changes = False
        if add_roles(session):
            any_changes = True
        if any_changes:
            session.commit()
            any_changes = False

        if add_admin_user(session):
            any_changes = True
        if any_changes:
            session.commit()
            any_changes = False

        if add_state_provinces(session):
            any_changes = True
        if any_changes:
            session.commit()
            any_changes = False

        if add_initial_locations(session):
            any_changes = True
        if add_sample_owners(session):
            any_changes = True
        if add_sample_charge_codes(session):
            any_changes = True

        if any_changes:
            session.commit()
        logger.info("Initial data setup process completed and committed successfully.")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError during data population: {e}", exc_info=True)
        session.rollback()
        print(f"ERROR: A database error occurred during data population: {e}")
    except AttributeError as e:
        logger.error(f"AttributeError during data population: {e}", exc_info=True)
        session.rollback()
        print(f"ERROR: An AttributeError occurred: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during data population: {e}", exc_info=True
        )
        session.rollback()
        print(f"ERROR: An unexpected error occurred during data population: {e}")
    finally:
        session.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    if not db_manager:
        print(
            "CRITICAL: Database manager (db_manager) not initialized prior to main call."
        )
    else:
        add_initial_data_main()
    print("Script execution finished. Check logs for details and potential warnings.")
