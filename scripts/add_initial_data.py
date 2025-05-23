# scripts/add_initial_data.py
"""
EDSI Veterinary Management System - Add Initial Data Script
Version: 1.2.6
Purpose: Populates the database with essential initial data for application setup.
         - SystemConfig import removed to defer its implementation.
Last Updated: May 23, 2025
Author: Gemini (based on user's v1.2.4)

Changelog:
- v1.2.6 (2025-05-23):
    - Removed `SystemConfig` from the main model import block.
- v1.2.5 (2025-05-23): (Previous Gemini attempt)
    - Removed `SystemConfig` from the `from models import ...` line to defer its implementation
      and prevent ImportErrors.
- v1.2.4 (2025-05-21 - User Uploaded Version):
    - Removed the `add_sample_horses_data` function and its call.
    - Ensured User, Role, Species, StateProvince are added.
    - Added a few sample Locations and Owners.
"""
import logging
import os
import sys
from datetime import date  # Keep datetime if used by models when creating instances
from decimal import Decimal

# Adjust the Python path to include the root directory of the project
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from config.database_config import db_manager, Session

    # Import only the models that are defined and needed by this script
    from models import (
        User,
        Role,
        UserRole,
        Species,
        StateProvince,
        ChargeCode,
        Veterinarian,
        Location,
        Owner,  # OwnerBillingHistory, OwnerPayment, # Not used directly in this script's functions
        # Horse, HorseOwner, HorseLocation, # No sample horses being added
        # Transaction, TransactionDetail, Invoice, Procedure, Drug,
        # TreatmentLog, CommunicationLog, Document, Reminder, Appointment,
        # SystemConfig, # REMOVED
    )

    # Note: db_manager.initialize_database() will use models/__init__.py for create_all()
except ImportError as e:
    print(f"Error importing modules in add_initial_data.py: {e}")
    print(
        "Please ensure all necessary model files exist and models/__init__.py is correct."
    )
    sys.exit(1)

# Configure basic logging
log_file_path = os.path.join(project_root, "logs", "add_initial_data.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.FileHandler(log_file_path, mode="w"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def add_roles(session):
    """Adds predefined roles to the database."""
    roles_to_add = [
        {"role_name": "ADMIN", "description": "Administrator with full system access."},
        {"role_name": "MANAGER", "description": "Manager with operational oversight."},
        {
            "role_name": "VETERINARIAN",
            "description": "Veterinarian providing medical services.",
        },
        {
            "role_name": "TECHNICIAN",
            "description": "Veterinary technician assisting with procedures.",
        },
        {
            "role_name": "RECEPTIONIST",
            "description": "Receptionist handling front-desk operations.",
        },
        {
            "role_name": "CLIENT",
            "description": "Client/Owner accessing their animal's information (future).",
        },
    ]
    existing_roles = {role.role_name for role in session.query(Role.role_name).all()}

    new_roles = []
    for role_data in roles_to_add:
        if role_data["role_name"] not in existing_roles:
            new_roles.append(Role(**role_data))
            logger.info(f"Prepared role: {role_data['role_name']}")
        else:
            logger.info(f"Role '{role_data['role_name']}' already exists, skipping.")

    if new_roles:
        session.add_all(new_roles)
        # session.commit() # Commit per section or at the end
        logger.info(f"Successfully prepared {len(new_roles)} new roles.")
    else:
        logger.info("No new roles to add.")
    return len(new_roles) > 0  # Return if changes were made


def add_admin_user(session):
    """Adds a default admin user if one doesn't exist."""
    admin_username = "ADMIN"
    admin_exists = session.query(User).filter_by(login_id=admin_username).first()
    changes_made = False

    if not admin_exists:
        admin_role = session.query(Role).filter_by(role_name="ADMIN").first()
        if not admin_role:
            logger.error(
                "ADMIN role not found. Cannot create admin user. Please add roles first."
            )
            return False

        hashed_password = User.hash_password("ADMIN")
        admin_user = User(
            login_id=admin_username,
            hashed_password=hashed_password,
            full_name="System Administrator",
            email="admin@edsystem.com",
            is_active=True,
            created_by="system_init",
            modified_by="system_init",
        )
        session.add(admin_user)
        # session.commit() # Commit to get ID for UserRole if FK is on User.id (integer)
        # Assuming UserRole links by string IDs login_id and role_name directly for now

        user_role_link = UserRole(
            user_id=admin_user.login_id, role_id=admin_role.role_name
        )
        session.add(user_role_link)
        changes_made = True
        logger.info(
            f"Admin user '{admin_username}' prepared with default password 'ADMIN' and ADMIN role."
        )
    else:
        logger.info(f"Admin user '{admin_username}' already exists.")
        admin_role = session.query(Role).filter_by(role_name="ADMIN").first()
        if admin_role:
            assoc_exists = (
                session.query(UserRole)
                .filter_by(user_id=admin_exists.login_id, role_id=admin_role.role_name)
                .first()
            )
            if not assoc_exists:
                user_role_link = UserRole(
                    user_id=admin_exists.login_id, role_id=admin_role.role_name
                )
                session.add(user_role_link)
                changes_made = True
                logger.info(f"ADMIN role assigned to existing user '{admin_username}'.")
    return changes_made


def add_species(session):
    """Adds initial species data."""
    species_to_add = [
        {
            "name": "Horse",
            "description": "Equine species",
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_species = {spec.name for spec in session.query(Species.name).all()}
    new_species = []
    for spec_data in species_to_add:
        if spec_data["name"] not in existing_species:
            new_species.append(Species(**spec_data))
            logger.info(f"Prepared species: {spec_data['name']}")
        else:
            logger.info(f"Species '{spec_data['name']}' already exists, skipping.")
    if new_species:
        session.add_all(new_species)
    return len(new_species) > 0


def add_state_provinces(session):
    """Adds a sample list of US states and Canadian provinces."""
    # (Content from your v1.2.4, ensure BaseModel fields are included if StateProvince inherits it)
    states_provinces_data = [
        {
            "state_code": "AL",
            "state_name": "Alabama",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "state_code": "AK",
            "state_name": "Alaska",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "state_code": "AZ",
            "state_name": "Arizona",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        # ... (add more or use your existing list)
        {
            "state_code": "PA",
            "state_name": "Pennsylvania",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "state_code": "TX",
            "state_name": "Texas",
            "country_code": "USA",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_codes = {
        sp.state_code for sp in session.query(StateProvince.state_code).all()
    }
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
    """Adds a few sample locations."""
    # (Content from your v1.2.4, ensure BaseModel fields are included)
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
    ]
    existing_locations = {
        loc.location_name for loc in session.query(Location.location_name).all()
    }
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
            # Decide: skip, add without state, or ensure state exists. Location model's state_code is nullable.
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
    """Adds a few sample owners."""
    # (Content from your v1.2.4, ensure BaseModel fields are included)
    owners_to_add = [
        {
            "owner_name": "John Smith",
            "owner_type": "Individual",
            "email_primary": "john.smith@example.com",
            "phone_number_primary": "555-0101",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "owner_name": "Willow Creek Stables",
            "owner_type": "Business",
            "email_primary": "contact@willowcreek.com",
            "phone_number_primary": "555-0202",
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_owners = {
        owner.owner_name for owner in session.query(Owner.owner_name).all()
    }
    new_owners = []
    for owner_data in owners_to_add:
        if owner_data["owner_name"] not in existing_owners:
            new_owners.append(Owner(**owner_data))
            logger.info(f"Prepared owner: {owner_data['owner_name']}")
        else:
            logger.info(
                f"Owner '{owner_data['owner_name']}' already exists (by name), skipping."
            )
    if new_owners:
        session.add_all(new_owners)
    return len(new_owners) > 0


def add_sample_charge_codes(session):
    """Adds some sample charge codes."""
    # (Content from your v1.2.4, ensure BaseModel fields are included)
    charge_codes_data = [
        {
            "code": "PROC001",
            "description": "Routine Examination",
            "category": "Procedure",
            "standard_charge": Decimal("75.00"),
            "is_taxable": False,
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
        {
            "code": "DRUG001",
            "description": "Antibiotic Injection (per ml)",
            "category": "Pharmacy",
            "standard_charge": Decimal("15.00"),
            "is_taxable": True,
            "is_active": True,
            "created_by": "system_init",
            "modified_by": "system_init",
        },
    ]
    existing_codes = {cc.code for cc in session.query(ChargeCode.code).all()}
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
    """Main function to add all initial data sets and manage session."""
    logger.info("Running script to add initial data to the database...")

    if not db_manager:
        logger.critical(
            "Database manager (db_manager) is not available. Imports might be incorrect or db_manager failed to initialize."
        )
        print("CRITICAL: Database manager not initialized. Cannot proceed.")
        return

    try:
        db_manager.initialize_database()  # This calls create_tables which imports from models via models/__init__
        logger.info("Database initialized and tables created (if they didn't exist).")
    except Exception as e:
        logger.critical(
            f"Failed to initialize database via db_manager: {e}", exc_info=True
        )
        print(
            f"CRITICAL: Database initialization failed: {e}. Cannot proceed with data addition."
        )
        return

    session = Session()
    try:
        logger.info("Starting to add initial reference data...")
        # Call each data addition function
        # Committing after each major section or all at the end
        add_roles(session)
        session.commit()  # Commit roles before adding users that depend on them

        add_admin_user(session)  # Commits inside if user is new, or if role is assigned
        # session.commit() # Ensure admin user and its role link is committed

        add_species(session)
        add_state_provinces(session)
        add_initial_locations(session)
        add_sample_owners(session)
        add_sample_charge_codes(session)

        session.commit()  # Final commit for all data added in this session block
        logger.info("Initial data setup process completed and committed successfully.")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError during data population: {e}", exc_info=True)
        session.rollback()
        print(f"ERROR: A database error occurred during data population: {e}")
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
            "CRITICAL: Database manager (db_manager) not initialized prior to main call. Check imports at top of script."
        )
    else:
        print(f"Database URL set to: {db_manager.db_url if db_manager else 'UNKNOWN'}")
        add_initial_data_main()
    print("Script execution finished. Check logs for details and potential warnings.")
