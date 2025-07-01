# scripts/add_initial_data.py
"""
EDSI Veterinary Management System - Add Initial Data Script
Version: 1.3.4
Purpose: Populates the database with essential initial data, including a full
         charge code list extracted from the legacy system's report.
         Now directly initializes DatabaseManager, making it standalone.
Last Updated: June 23, 2025
Author: Gemini

Changelog:
- v1.3.4 (2025-06-23):
    - Modified `add_initial_data_main` to directly instantiate `DatabaseManager`
      using `AppConfig` and the global `config_manager`.
    - All database calls (`initialize_database`, `get_session`, `close`) now use
      this locally instantiated `_db_manager` object, eliminating reliance on
      the singleton setup from `main.py` and resolving `RuntimeError: DatabaseManager instance not set`.
- v1.3.3 (2025-06-23):
    - Corrected database access calls from `db_manager.get_session()` to `db_manager().get_session()`
      and `db_manager.close()` to `db_manager().close()` to align with the updated `DatabaseManager` singleton access pattern.
- v1.3.2 (2025-06-09):
    - Fix: Restored the full implementations for all helper functions.
    - Feature: Populated with the complete list of all 167 charge codes from the PDF.
- v1.3.1 (2025-06-09):
    - Added placeholder functions to be filled.
"""
import logging
import os
import sys
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Any

# Setup project path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import required modules
try:
    from config.database_config import DatabaseManager  # Import the class directly
    from config.app_config import AppConfig  # Import AppConfig
    from config.config_manager import (
        config_manager,
    )  # Import the global config_manager instance
    from models import (
        User,
        Role,
        UserRole,
        StateProvince,
        ChargeCodeCategory,
        ChargeCode,
        Veterinarian,
        Location,
        Owner,
    )
except ImportError as e:
    print(f"Error importing modules in add_initial_data.py: {e}")
    sys.exit(1)

# --- Logging Setup ---
# Assuming logs directory is set up by AppConfig in main.py, but for standalone script, ensure it exists.
log_file_path = os.path.join(project_root, "logs", "add_initial_data.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(os.path.basename(__file__))


def add_roles(session) -> bool:
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
    existing_roles = {role_tuple[0] for role_tuple in session.query(Role.name).all()}
    new_roles_instances = []
    for role_data in roles_to_add:
        if role_data["name"] not in existing_roles:
            new_roles_instances.append(Role(**role_data))
            logger.info(f"Prepared role: {role_data['name']}")
        else:
            logger.info(f"Role '{role_data['name']}' already exists, skipping.")
    if new_roles_instances:
        session.add_all(new_roles_instances)
        logger.info(f"Successfully prepared {len(new_roles_instances)} new roles.")
        return True
    logger.info("No new roles to add.")
    return False


def add_admin_user(session) -> bool:
    admin_login_id = "ADMIN"
    admin_exists = session.query(User).filter_by(user_id=admin_login_id).first()
    changes_made = False
    if not admin_exists:
        admin_role = session.query(Role).filter_by(name="ADMIN").first()
        if not admin_role:
            logger.error("ADMIN role not found. Cannot create admin user.")
            return False
        admin_user = User(
            user_id=admin_login_id,
            user_name="System Administrator",
            email="admin@edsystem.com",
            is_active=True,
            created_by="system_init",
            modified_by="system_init",
        )
        admin_user.set_password("admin1234")
        admin_user.roles.append(admin_role)
        session.add(admin_user)
        changes_made = True
        logger.info(
            f"Admin user '{admin_login_id}' prepared with default password and ADMIN role."
        )
    else:
        logger.info(f"Admin user '{admin_login_id}' already exists.")
        if not admin_exists.check_password("admin1234"):
            admin_exists.set_password("admin1234")
            logger.info(
                f"Password for existing ADMIN user '{admin_login_id}' reset to default (bcrypt)."
            )
            changes_made = True
        admin_role = session.query(Role).filter_by(name="ADMIN").first()
        if admin_role and admin_role not in admin_exists.roles:
            admin_exists.roles.append(admin_role)
            admin_exists.modified_by = "system_init_role_add"
            changes_made = True
            logger.info(f"ADMIN role assigned to existing user '{admin_login_id}'.")
    return changes_made


def add_charge_code_categories(session) -> bool:
    logger.info("Preparing charge code categories...")
    categories_structure = [
        {
            "name": "ANTHELMINTICS",
            "level": 1,
            "children": [
                {"name": "ADMINISTERED", "level": 2},
                {"name": "DISPENSED", "level": 2},
            ],
        },
        {"name": "CALL FEES", "level": 1, "children": []},
        {
            "name": "DIAGNOSTIC PROCEDURES",
            "level": 1,
            "children": [
                {"name": "NERVE BLOCKS", "level": 2},
                {"name": "JOINT BLOCKS", "level": 2},
                {"name": "RADIOLOGY - FRONT LEG", "level": 2},
                {"name": "RADIOLOGY - HIND LEG", "level": 2},
                {"name": "RADIOLOGY - OTHER", "level": 2},
                {"name": "ULTRASOUND EXAM OF EXTREMITIES", "level": 2},
                {"name": "OTHER", "level": 2},
            ],
        },
        {
            "name": "EXAMINATIONS",
            "level": 1,
            "children": [
                {"name": "SICK HORSE EXAMS", "level": 2},
                {"name": "OTHER EXAMS", "level": 2},
            ],
        },
        {
            "name": "IMMUNIZATIONS",
            "level": 1,
            "children": [{"name": "HORSE", "level": 2}],
        },
        {
            "name": "LABORATORY PROCEDURES",
            "level": 1,
            "children": [
                {"name": "BLOOD WORK", "level": 2},
                {"name": "OTHER", "level": 2},
            ],
        },
        {
            "name": "MEDICATION ADMINISTERED",
            "level": 1,
            "children": [
                {"name": "ANABOLIC STEROIDS", "level": 2},
                {"name": "ANTIBIOTICS", "level": 2},
                {"name": "DIURETICS", "level": 2},
                {"name": "FLUIDS ADMINISTERED", "level": 2},
                {"name": "GASTROINTESTINAL TREATMENTS", "level": 2},
                {"name": "INTRA-ARTICULAR INJECTIONS", "level": 2},
                {"name": "OTHER HORMONES", "level": 2},
                {"name": "NON-ARTICULAR INJECTIONS", "level": 2},
                {"name": "NSAID'S ANALGESICS", "level": 2},
                {"name": "TRANQUILIZERS & ANESTHETICS", "level": 2},
                {"name": "VITAMINS", "level": 2},
                {"name": "OTHER", "level": 2},
            ],
        },
        {
            "name": "MEDICATIONS DISPENSED",
            "level": 1,
            "children": [
                {"name": "OTHER HORMONES", "level": 2},
                {"name": "ANTIBIOTICS - PENICILLINS", "level": 2},
                {"name": "ANTIBIOTICS - OTHER", "level": 2},
                {"name": "BANDAGES & MATERIALS", "level": 2},
                {"name": "DERMATITIS/TOPICAL ANTISEPTICS", "level": 2},
                {"name": "DIURETICS", "level": 2},
                {"name": "FLUIDS", "level": 2},
                {"name": "G.I. MEDICATIONS", "level": 2},
                {"name": "INJECTABLE NSAID'S", "level": 2},
                {"name": "OTHER INJECTABLE ANTI-INFLAM.", "level": 2},
                {"name": "INTRA-ARTICULAR PRODUCTS", "level": 2},
                {"name": "LEG PREPARATIONS", "level": 2},
                {"name": "NEEDLES & SYRINGES", "level": 2},
                {"name": "ORAL NSAID'S", "level": 2},
                {"name": "OTHER ORAL ANTI-INFLAM.", "level": 2},
                {"name": "OPHTHALMIC DRUGS", "level": 2},
                {"name": "RESPIRATORY DRUGS", "level": 2},
                {"name": "TOPICAL MEDICATIONS", "level": 2},
                {"name": "TRANQUILIZERS & MUSCLE RELAX.", "level": 2},
                {"name": "VITAMINS", "level": 2},
                {"name": "NON-VITAMIN FEED SUPPLEMENTS", "level": 2},
                {"name": "OTHER", "level": 2},
            ],
        },
        {
            "name": "REPRODUCTIVE PROCEDURES",
            "level": 1,
            "children": [{"name": "GENERAL BROODMARE WORK", "level": 2}],
        },
        {"name": "SURGICAL PROCEDURES", "level": 1, "children": []},
        {
            "name": "VET. PROCEDURES & SERVICES",
            "level": 1,
            "children": [
                {"name": "BANDAGING", "level": 2},
                {"name": "OTHER", "level": 2},
            ],
        },
        {"name": "OTHER", "level": 1, "children": []},
    ]
    changes_made = False

    def _process_categories(
        categories_list: List[Dict[str, Any]], current_parent_id: Optional[int] = None
    ):
        nonlocal session  # Declare session as nonlocal to modify the outer scope's session variable
        nonlocal changes_made
        for cat_data in categories_list:
            existing_cat = (
                session.query(ChargeCodeCategory)
                .filter_by(
                    name=cat_data["name"],
                    level=cat_data["level"],
                    parent_id=current_parent_id,
                )
                .first()
            )
            if not existing_cat:
                new_cat = ChargeCodeCategory(
                    name=cat_data["name"],
                    level=cat_data["level"],
                    parent_id=current_parent_id,
                    is_active=True,
                    created_by="system_init",
                    modified_by="system_init",
                )
                session.add(new_cat)
                session.flush()
                logger.info(
                    f"Prepared category: {new_cat.name} (Level {new_cat.level}, Parent ID: {new_cat.parent_id}) with ID {new_cat.category_id}"
                )
                changes_made = True
                created_cat_id = new_cat.category_id
            else:
                logger.info(
                    f"Category '{cat_data['name']}' (Level {cat_data['level']}, Parent ID: {current_parent_id}) already exists, skipping creation."
                )
                created_cat_id = existing_cat.category_id
            if "children" in cat_data and cat_data["children"]:
                _process_categories(cat_data["children"], created_cat_id)

    _process_categories(categories_structure)
    if changes_made:
        logger.info("Successfully prepared new charge code categories.")
    else:
        logger.info("No new charge code categories to add or all existed.")
    return changes_made


def _get_category_id_by_path(session, path_list: List[str]) -> Optional[int]:
    if not path_list:
        return None
    parent_id, current_category_id, level = None, None, 1
    for category_name in path_list:
        category = (
            session.query(ChargeCodeCategory)
            .filter_by(name=category_name, level=level, parent_id=parent_id)
            .first()
        )
        if not category:
            logger.warning(
                f"Category not found in path: Name='{category_name}', Level={level}, ParentID={parent_id}. Full path: {path_list}"
            )
            return None
        current_category_id = category.category_id
        parent_id = current_category_id
        level += 1
    return current_category_id


def add_state_provinces(session) -> bool:
    full_states_list = [
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
    for sp_data in full_states_list:
        sp_data.update({"created_by": "system_init", "modified_by": "system_init"})
    existing_codes = {
        sp_tuple[0] for sp_tuple in session.query(StateProvince.state_code).all()
    }
    new_entries = [
        StateProvince(**sp_data)
        for sp_data in full_states_list
        if sp_data["state_code"] not in existing_codes
    ]
    for entry in new_entries:
        logger.info(f"Prepared state/province: {entry.state_name}")
    if new_entries:
        session.add_all(new_entries)
        logger.info(f"Added {len(new_entries)} new states/provinces.")
    else:
        logger.info("No new states/provinces to add or all existed.")
    return len(new_entries) > 0


def add_initial_locations(session) -> bool:
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
    existing_locations = {
        loc_tuple[0] for loc_tuple in session.query(Location.location_name).all()
    }
    new_locations_instances = []
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
            new_locations_instances.append(Location(**loc_data))
            logger.info(f"Prepared location: {loc_data['location_name']}")
        else:
            logger.info(
                f"Location '{loc_data['location_name']}' already exists, skipping."
            )
    if new_locations_instances:
        session.add_all(new_locations_instances)
    return len(new_locations_instances) > 0


def add_sample_owners(session) -> bool:
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
            "farm_name": "Quail Pond Farms",
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
    ]
    existing_account_numbers = {
        owner_tuple[0]
        for owner_tuple in session.query(Owner.account_number)
        .filter(Owner.account_number.isnot(None))
        .all()
    }
    new_owners_instances = []
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
            new_owners_instances.append(Owner(**owner_data))
            logger.info(
                f"Prepared owner: {owner_data.get('farm_name', owner_data.get('last_name'))}"
            )
        elif owner_data.get("account_number") is None:
            new_owners_instances.append(Owner(**owner_data))
            logger.info(
                f"Prepared owner (no account number): {owner_data.get('farm_name', owner_data.get('last_name'))}"
            )
        else:
            logger.info(
                f"Owner with account number '{owner_data['account_number']}' already exists, skipping."
            )
    if new_owners_instances:
        session.add_all(new_owners_instances)
    return len(new_owners_instances) > 0


def add_all_charge_codes(session) -> bool:
    """Populates the database with a comprehensive list of charge codes from the legacy report."""
    logger.info("Preparing complete charge code list...")
    charge_codes_data = [
        {
            "code": "9991",
            "alt": "IVO",
            "desc": "IVERMECTIN AND PRAZIQUANTEL",
            "price": "25.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "413",
            "alt": "PWBEN",
            "desc": "PASTE WORM WITH BENZELMIN",
            "price": "14.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "412",
            "alt": "PWPAN",
            "desc": "PASTE WORM WITH FENBENDAZOLE",
            "price": "24.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "414",
            "alt": "PWPP",
            "desc": "PASTE WORM WITH PYRANTAL PAMOATE",
            "price": "12.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "107",
            "alt": "PPP",
            "desc": "TREATMENT WITH PANACUR POWER PAC",
            "price": "90.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "576",
            "alt": "Q",
            "desc": "TREATMENT WITH QUEST",
            "price": "25.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "405",
            "alt": "TW2X",
            "desc": "TUBE WORM WITH DOUBLE DOSE OF PANACUR OR STRONGID T",
            "price": "60.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "400",
            "alt": "TWBQ",
            "desc": "TUBE WORM WITH EQUIZOLE A",
            "price": "18.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "403",
            "alt": "TWPAN",
            "desc": "TUBE WORM WITH FENBENDAZOLE",
            "price": "20.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "402",
            "alt": "TWPP",
            "desc": "TUBE WORM WITH PYRANTAL PAMOATE",
            "price": "20.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "406",
            "alt": "TW10X",
            "desc": "TUBE WORM WITH TEN TIMES DOSE OF PANACUR",
            "price": "70.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "420",
            "alt": "WORM",
            "desc": "WORM",
            "price": "20.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "109",
            "alt": "W2X",
            "desc": "WORM WITH DOUBLE DOSE STRONGID OR PANACUR",
            "price": "24.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "411",
            "alt": "PWIV",
            "desc": "WORM WITH IVERMECTIN",
            "price": "20.00",
            "path": ["ANTHELMINTICS", "ADMINISTERED"],
        },
        {
            "code": "9634",
            "alt": "STRC",
            "desc": "25 LB PAIL OF STRONGID C 2X PELLETS",
            "price": "100.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "424",
            "alt": "DBEN",
            "desc": "BENZELMIN PASTE",
            "price": "15.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "39",
            "alt": "STRC2X",
            "desc": "BUCKET OF STRONGID C 2X PELLETS",
            "price": "100.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "426",
            "alt": "DPANL",
            "desc": "DISPENSE PANACUR LIQUID 1000 ML",
            "price": "240.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "581",
            "alt": "DQUEST",
            "desc": "DISPENSE QUEST",
            "price": "200.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "429",
            "alt": "DWORM",
            "desc": "DISPENSE WORMER",
            "price": "11.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "425",
            "alt": "DEQV",
            "desc": "EQVALAN PASTE",
            "price": "15.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "423",
            "alt": "DPAN",
            "desc": "PANACUR PASTE",
            "price": "20.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "422",
            "alt": "PPPT",
            "desc": "PYRANTAL PAMOATE 1 PINT",
            "price": "40.00",
            "path": ["ANTHELMINTICS", "DISPENSED"],
        },
        {
            "code": "650",
            "alt": "AF",
            "desc": "ATTEND FOALING",
            "price": "100.00",
            "path": ["CALL FEES"],
        },
        {
            "code": "101",
            "alt": "EFC",
            "desc": "EMERGENCY FARM CALL",
            "price": "100.00",
            "path": ["CALL FEES"],
        },
        {
            "code": "100",
            "alt": "FC",
            "desc": "FARM CALL",
            "price": "60.00",
            "path": ["CALL FEES"],
        },
        {
            "code": "103",
            "alt": "NFC",
            "desc": "NO FARM CALL CHARGE",
            "price": "0.00",
            "path": ["CALL FEES"],
        },
        {
            "code": "102",
            "alt": "PFC",
            "desc": "PARTIAL FARM CALL",
            "price": "10.00",
            "path": ["CALL FEES"],
        },
        {
            "code": "32",
            "alt": "BLBS",
            "desc": "DIAGNOSTIC BASISESMOID NERVE BLOCK",
            "price": "50.00",
            "path": ["DIAGNOSTIC PROCEDURES", "NERVE BLOCKS"],
        },
        {
            "code": "33",
            "alt": "BLHV",
            "desc": "DIAGNOSTIC HIGH VOLAR NERVE BLOCK",
            "price": "50.00",
            "path": ["DIAGNOSTIC PROCEDURES", "NERVE BLOCKS"],
        },
        {
            "code": "35",
            "alt": "BLLV",
            "desc": "DIAGNOSTIC LOW VOLAR NERVE BLOCK",
            "price": "50.00",
            "path": ["DIAGNOSTIC PROCEDURES", "NERVE BLOCKS"],
        },
        {
            "code": "31",
            "alt": "BLN",
            "desc": "DIAGNOSTIC NERVE BLOCK",
            "price": "20.00",
            "path": ["DIAGNOSTIC PROCEDURES", "NERVE BLOCKS"],
        },
        {
            "code": "34",
            "alt": "BLIA",
            "desc": "DIAGNOSTIC INTRA-ARTICULAR BLOCK",
            "price": "50.00",
            "path": ["DIAGNOSTIC PROCEDURES", "JOINT BLOCKS"],
        },
        {
            "code": "3",
            "alt": "XLA",
            "desc": "RADIOGRAPH LEFT FRONT FETLOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "5",
            "alt": "XLC",
            "desc": "RADIOGRAPH LEFT FRONT CANNON BONE AND SPLINTS",
            "price": "60.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "1",
            "alt": "XLF",
            "desc": "RADIOGRAPH OF LEFT FRONT FOOT",
            "price": "80.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "7",
            "alt": "XLK",
            "desc": "RADIOGRAPH OF LEFT KNEE",
            "price": "90.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "8",
            "alt": "XRK",
            "desc": "RADIOGRAPH OF RIGHT KNEE",
            "price": "90.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "6",
            "alt": "XRC",
            "desc": "RADIOGRAPH RIGHT FRONT CANNON BONE AND SPLINTS",
            "price": "60.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "4",
            "alt": "XRA",
            "desc": "RADIOGRAPH RIGHT FRONT FETLOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "2",
            "alt": "XRF",
            "desc": "RADIOGRAPH RIGHT FRONT FOOT",
            "price": "80.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - FRONT LEG"],
        },
        {
            "code": "9",
            "alt": "XLHC",
            "desc": "RADIOGRAPH LEFT HIND CANNON AND SPLINTS",
            "price": "60.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "13",
            "alt": "XLHA",
            "desc": "RADIOGRAPH LEFT HIND FETLOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "15",
            "alt": "XLHF",
            "desc": "RADIOGRAPH LEFT HIND FOOT",
            "price": "80.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "11",
            "alt": "XLH",
            "desc": "RADIOGRAPH LEFT HOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "17",
            "alt": "XLS",
            "desc": "RADIOGRAPH LEFT STIFLE",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "10",
            "alt": "XRHC",
            "desc": "RADIOGRAPH RIGHT HIND CANNON AND SPLINTS",
            "price": "60.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "14",
            "alt": "XRHA",
            "desc": "RADIOGRAPH RIGHT HIND FETLOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "16",
            "alt": "XRHF",
            "desc": "RADIOGRAPH RIGHT HIND FOOT",
            "price": "80.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "12",
            "alt": "XRH",
            "desc": "RADIOGRAPH RIGHT HOCK",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "18",
            "alt": "XRS",
            "desc": "RADIOGRAPH RIGHT STIFLE",
            "price": "75.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - HIND LEG"],
        },
        {
            "code": "20",
            "alt": "X",
            "desc": "RADIOGRAPHS MULTIPLE VIEWS",
            "price": "15.00",
            "path": ["DIAGNOSTIC PROCEDURES", "RADIOLOGY - OTHER"],
        },
        {
            "code": "40",
            "alt": "UOTHER",
            "desc": "ULTRASOUND EXAM ON LEG",
            "price": "175.00",
            "path": ["DIAGNOSTIC PROCEDURES", "ULTRASOUND EXAM OF EXTREMITIES"],
        },
        {
            "code": "1017",
            "alt": "EPMT",
            "desc": "BLOOD FOR EPM TEST",
            "price": "150.00",
            "path": ["DIAGNOSTIC PROCEDURES", "OTHER"],
        },
        {
            "code": "41",
            "alt": "SCOPE",
            "desc": "ENDOSCOPIC EXAMINATION OF UPPER AIRWAY",
            "price": "50.00",
            "path": ["DIAGNOSTIC PROCEDURES", "OTHER"],
        },
        {
            "code": "7732",
            "alt": "FEC",
            "desc": "FECAL SCREEN FOR PARASITE OVA",
            "price": "20.00",
            "path": ["DIAGNOSTIC PROCEDURES", "OTHER"],
        },
        {
            "code": "7342",
            "alt": "GASTRO",
            "desc": "GASTROSCOPY WITH SEDATION",
            "price": "200.00",
            "path": ["DIAGNOSTIC PROCEDURES", "OTHER"],
        },
        {
            "code": "8801",
            "alt": "SA",
            "desc": "SERUM AMYLOID TEST",
            "price": "60.00",
            "path": ["DIAGNOSTIC PROCEDURES", "OTHER"],
        },
        {
            "code": "200",
            "alt": "DERMX",
            "desc": "DERMATOLOGICAL EXAMINATION",
            "price": "50.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "201",
            "alt": "GIX",
            "desc": "GASTRO-INTESTINAL EXAMINATION",
            "price": "50.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "204",
            "alt": "NEURX",
            "desc": "NEUROLOGIC EXAMINATION",
            "price": "35.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "205",
            "alt": "OPX",
            "desc": "OPTHALMIC EXAMINATION",
            "price": "40.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "209",
            "alt": "EXAM",
            "desc": "OTHER TYPES OF EXAMINATIONS",
            "price": "35.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "206",
            "alt": "PHX",
            "desc": "PHYSICAL EXAMINATION",
            "price": "50.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "215",
            "alt": "REEX",
            "desc": "RE-EXAMINATION",
            "price": "35.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "207",
            "alt": "RBCX",
            "desc": "RECTAL EXAMINATION",
            "price": "30.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "208",
            "alt": "RBSPX",
            "desc": "RESPIRATORY EXAMINATION",
            "price": "35.00",
            "path": ["EXAMINATIONS", "SICK HORSE EXAMS"],
        },
        {
            "code": "772",
            "alt": "BCJ",
            "desc": "BICARBONATE JUG 500 CC",
            "price": "30.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "213",
            "alt": "CHCH",
            "desc": "CANADIAN HEALTH CERTIFICATE",
            "price": "175.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "212",
            "alt": "HCH",
            "desc": "HEALTH CERTIFICATE",
            "price": "20.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "211",
            "alt": "INSX",
            "desc": "INSURANCE EXAM AND PAPERWORK",
            "price": "25.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "202",
            "alt": "LAMX",
            "desc": "LAMENESS EXAMINATION",
            "price": "50.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "210",
            "alt": "PPE",
            "desc": "PREPURCHASE EVALUATION",
            "price": "300.00",
            "path": ["EXAMINATIONS", "OTHER EXAMS"],
        },
        {
            "code": "4567",
            "alt": None,
            "desc": "ADMINISTER EQUINE RHINITIS A VACCINE",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "5588",
            "alt": "RHI",
            "desc": "ADMINISTER EQUINE RHINITIS A VACCINE",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "3120",
            "alt": "BOT",
            "desc": "BOTULISM TOXOID",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "300",
            "alt": "EWTFR",
            "desc": "E&W ENCEPHALITIS, TETANUS, INFLUENZA, RHINOPNEUMONITIS",
            "price": "60.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "302",
            "alt": "EW",
            "desc": "EASTERN AND WESTERN ENCEPHALITIS",
            "price": "20.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "305",
            "alt": "EWT",
            "desc": "EASTERN AND WESTERN ENCEPHALITIS AND TETANUS",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "303",
            "alt": "FR",
            "desc": "INFLUENZA AND RHINOPNEUMONITIS",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "7908",
            "alt": "F",
            "desc": "INFLUENZA VACCINE",
            "price": "10.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "311",
            "alt": "FRIN",
            "desc": "INTRANASAL INFLUENZA AND RHINOPNEUMONITIS VACCINATION",
            "price": "25.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "309",
            "alt": "PHF",
            "desc": "POTOMAC HORSE FEVER VACCINE",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "307",
            "alt": "RA",
            "desc": "RABIES VACCINATION",
            "price": "30.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "304",
            "alt": "R",
            "desc": "RHINOPNEUMONITIS",
            "price": "25.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "312",
            "alt": "EPMV",
            "desc": "SARCOSYSTIS NEURONA VACCINE",
            "price": "25.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "308",
            "alt": "STR",
            "desc": "STRANGLES",
            "price": "40.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "3125",
            "alt": "TAT",
            "desc": "TETANUS ANTITOXIN",
            "price": "20.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "301",
            "alt": "TVAC",
            "desc": "TETANUS INJECTION IM",
            "price": "10.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "5410",
            "alt": "WNVB",
            "desc": "WEST NILE VACCINATION BOOSTER",
            "price": "26.50",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "140",
            "alt": "WNV",
            "desc": "WEST NILES VACCINATION",
            "price": "35.00",
            "path": ["IMMUNIZATIONS", "HORSE"],
        },
        {
            "code": "69",
            "alt": "BLOOD",
            "desc": "BLOOD ANALYSIS",
            "price": "0.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "53",
            "alt": "COG",
            "desc": "COGGINS TEST FOR EIA",
            "price": "65.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "52",
            "alt": "CHEM",
            "desc": "COMPLETE BLOOD CHEMISTRY",
            "price": "65.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "50",
            "alt": "CBC",
            "desc": "COMPLETE BLOOD COUNT",
            "price": "35.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "51",
            "alt": "BTS",
            "desc": "COMPLETE BLOOD COUNT AND CHEMISTRY",
            "price": "100.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "9995",
            "alt": "DRUG",
            "desc": "DRUG SCREEN",
            "price": "300.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "9754",
            "alt": "PIRO",
            "desc": "PIROPLASMOSIS TESTING FOR EXPORT/TRAVEL PURPOSE",
            "price": "130.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "60",
            "alt": "FIB",
            "desc": "SERUM FIBRINOGEN",
            "price": "75.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "116",
            "alt": "SI",
            "desc": "SERUM IRON LEVEL",
            "price": "30.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "62",
            "alt": "SGOT",
            "desc": "SERUM SGOT AND CPK",
            "price": "35.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "55",
            "alt": "LYME",
            "desc": "SERUM TITER FOR LYMES DISEASE",
            "price": "60.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "9996",
            "alt": "T3T4",
            "desc": "THYROID ANALYSIS",
            "price": "100.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "61",
            "alt": "T3",
            "desc": "THYROID ASSAY T3 AND T4",
            "price": "100.00",
            "path": ["LABORATORY PROCEDURES", "BLOOD WORK"],
        },
        {
            "code": "70",
            "alt": "C/S",
            "desc": "BACTERIAL CULTURE AND SENSITIVITY",
            "price": "60.00",
            "path": ["LABORATORY PROCEDURES", "OTHER"],
        },
        {
            "code": "75",
            "alt": "CYT",
            "desc": "CYTOLOGY",
            "price": "65.00",
            "path": ["LABORATORY PROCEDURES", "OTHER"],
        },
        {
            "code": "71",
            "alt": "TTW",
            "desc": "TRANS TRACHAEL WASH",
            "price": "150.00",
            "path": ["LABORATORY PROCEDURES", "OTHER"],
        },
        {
            "code": "271",
            "alt": "COMBO",
            "desc": "BCP AND EQUIPOSE 3 ML",
            "price": "45.00",
            "path": ["MEDICATION ADMINISTERED", "ANABOLIC STEROIDS"],
        },
        {
            "code": "670",
            "alt": "B",
            "desc": "EQUIPOSE INJECTION",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "ANABOLIC STEROIDS"],
        },
        {
            "code": "674",
            "alt": "TEST",
            "desc": "TESTOSTERONE INJECTION IM",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "ANABOLIC STEROIDS"],
        },
        {
            "code": "676",
            "alt": "W",
            "desc": "WINSTROL INJECTION",
            "price": "42.00",
            "path": ["MEDICATION ADMINISTERED", "ANABOLIC STEROIDS"],
        },
        {
            "code": "8920",
            "alt": "EXC",
            "desc": "ADMINISTER 4 DAY TREATMENT WITH EXCEED",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "25",
            "alt": "BAYI",
            "desc": "BAYTRIL INJECTION IV",
            "price": "38.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "814",
            "alt": "DVGEN",
            "desc": "EXAM, DISPENSE BOTTLE OF GENTAMICIN SULFATE",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "998",
            "alt": "AMP",
            "desc": "INJECTION OF AMPICILLIN IV",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "607",
            "alt": "GEN",
            "desc": "INJECTION OF GENTAMYCIN SULFATE",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "600",
            "alt": "PPG",
            "desc": "INJECTION OF PROCAINE PENICILLIN G",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "608",
            "alt": "TET",
            "desc": "INJECTION OF TETRACYCLINE IV",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "610",
            "alt": "NAX",
            "desc": "NAXCEL INJECTION",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "ANTIBIOTICS"],
        },
        {
            "code": "22",
            "alt": "NAQI",
            "desc": "INJECTION OF NAQUASONE IV",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "DIURETICS"],
        },
        {
            "code": "760",
            "alt": "LAS",
            "desc": "LASIX INJECTION",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "DIURETICS"],
        },
        {
            "code": "892",
            "alt": "JUG6",
            "desc": "6 LITRES OF SALINE ADMINISTERED WITH VITAMINS",
            "price": "140.00",
            "path": ["MEDICATION ADMINISTERED", "FLUIDS ADMINISTERED"],
        },
        {
            "code": "770",
            "alt": "JUG",
            "desc": "ONE LITER OF LACTATED RINGERS",
            "price": "24.00",
            "path": ["MEDICATION ADMINISTERED", "FLUIDS ADMINISTERED"],
        },
        {
            "code": "778",
            "alt": "NAI",
            "desc": "SODIUM IODIDE JUG",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "FLUIDS ADMINISTERED"],
        },
        {
            "code": "703",
            "alt": "OIL",
            "desc": "TUBE WITH ONE GALLON MINERAL OIL",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "GASTROINTESTINAL TREATMENTS"],
        },
        {
            "code": "992",
            "alt": "KZ",
            "desc": "INTRA-ARTICULAR INJ. OF CARPAL JOINT WITH ZEEL & TRAUMBEL",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "991",
            "alt": "AZ",
            "desc": "INTRA-ARTICULAR INJ. OF FETLOCK JOINT WITH ZEEL & TRAUMEEL",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "993",
            "alt": "HZ",
            "desc": "INTRA-ARTICULAR INJ. OF HOCK JOINT WITH ZEEL & TRAUMBEL",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "994",
            "alt": "SZ",
            "desc": "INTRA-ARTICULAR INJ. OF STIFLE JOINT WITH ZEEL & TRAUMBEL",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "720",
            "alt": "KC",
            "desc": "INTRA-ARTICULAR INJECTION OF CARPAL JOINT",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "721",
            "alt": "KH",
            "desc": "INTRA-ARTICULAR INJECTION OF CARPAL JOINT WITH ACID",
            "price": "130.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "738",
            "alt": "CC",
            "desc": "INTRA-ARTICULAR INJECTION OF COFFIN JOINT",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "433",
            "alt": "CH",
            "desc": "INTRA-ARTICULAR INJECTION OF COFFIN JOINT WITH ACID",
            "price": "130.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "990",
            "alt": "CZ",
            "desc": "INTRA-ARTICULAR INJECTION OF COFFIN JOINT WITH ZEEL & TRAUMBEL",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "723",
            "alt": "AC",
            "desc": "INTRA-ARTICULAR INJECTION OF FETLOCK JOINT",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "724",
            "alt": "AH",
            "desc": "INTRA-ARTICULAR INJECTION OF FETLOCK JOINT WITH ACID",
            "price": "130.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "124",
            "alt": "SC",
            "desc": "INTRA-ARTICULAR INJECTION OF STIFLE",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "726",
            "alt": "HC",
            "desc": "INTRA-ARTICULAR INJECTION OF TARSAL JOINT",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "727",
            "alt": "HH",
            "desc": "INTRA-ARTICULAR INJECTION OF TARSAL JOINT WITH ACID",
            "price": "130.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "125",
            "alt": "SH",
            "desc": "INTRA-ARTICULAR INJECTION OF THE STIFLE JOINT WITH ACID",
            "price": "125.00",
            "path": ["MEDICATION ADMINISTERED", "INTRA-ARTICULAR INJECTIONS"],
        },
        {
            "code": "680",
            "alt": "ACTH",
            "desc": "ACTH INJECTION",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "681",
            "alt": "EST",
            "desc": "ESTRONE INJECTION",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "682",
            "alt": "HCG",
            "desc": "HCG INJECTION",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "1251",
            "alt": "DEPO",
            "desc": "INJECTION OF DEPO-PROVERA",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "683",
            "alt": "LEVO",
            "desc": "LEVOTHYROXINE INJECTION",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "404",
            "alt": "BCP",
            "desc": "TREATMENT WITH BCP",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER HORMONES"],
        },
        {
            "code": "733",
            "alt": "ADIM",
            "desc": "INJECTION OF ADEQUAN IM",
            "price": "70.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "700",
            "alt": "XP",
            "desc": "INJECTION OF DISTAL RADIAL PHYSES",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "742",
            "alt": "MGS",
            "desc": "INJECTION OF GLUTEAL MUSCLES, EPAXIAL MUSCLES AND STIFLES",
            "price": "90.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "1018",
            "alt": "HAIV",
            "desc": "INJECTION OF HYALURONIC ACID IV",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "740",
            "alt": "ZT",
            "desc": "INJECTION OF ZEEL AND TRAUMEEL",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "743",
            "alt": "S",
            "desc": "INTERNAL BLISTER OF STIFLE",
            "price": "80.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "792",
            "alt": "MG",
            "desc": "INTERNAL BLISTER OF THE BACK, STIFLE AND WHORL BONES",
            "price": "120.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "751",
            "alt": "LF",
            "desc": "NON-ARTICULAR INJECTION OF LEFT FRONT LEG",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "748",
            "alt": "LH",
            "desc": "NON-ARTICULAR INJECTION OF LEFT HIND LEG",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "750",
            "alt": "RF",
            "desc": "NON-ARTICULAR INJECTION OF RIGHT FRONT LEG",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "749",
            "alt": "RH",
            "desc": "NON-ARTICULAR INJECTION OF THE RIGHT HIND LEG",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "4876",
            "alt": "POLY",
            "desc": "POLYGLYCAN IV 5CC",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "741",
            "alt": "FBB",
            "desc": "PROFESSIONAL SERVICES FEET",
            "price": "100.00",
            "path": ["MEDICATION ADMINISTERED", "NON-ARTICULAR INJECTIONS"],
        },
        {
            "code": "640",
            "alt": "BAN",
            "desc": "BANAMINE INJECTION",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "641",
            "alt": "BUT",
            "desc": "BUTAZOLIDIN INJECTION",
            "price": "12.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "643",
            "alt": "DMSOJ",
            "desc": "DMSO INJECTION IN 1 LITER FLUIDS",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "138",
            "alt": "ADN",
            "desc": "INJECTION OF ADENOSINE IM",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "649",
            "alt": "ASA",
            "desc": "INJECTION OF ASPIRIN IV",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "660",
            "alt": "DEX",
            "desc": "INJECTION OF DEXAMETHASONE",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "642",
            "alt": "NOV",
            "desc": "INJECTION OF DIPYRONE",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "995",
            "alt": "DMSO",
            "desc": "INJECTION OF DMSO IV",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "663",
            "alt": "FLUC",
            "desc": "INJECTION OF FLUCORT",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "666",
            "alt": "VETA",
            "desc": "INJECTION OF VETALOG",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "621",
            "alt": "KET",
            "desc": "KETOFEN INJECTION",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "648",
            "alt": "ROB",
            "desc": "ROBAXIN INJECTION",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "553",
            "alt": "RVI",
            "desc": "RVI INJECTION",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "84",
            "alt": "VOR",
            "desc": "TREATMENT WITH VOREN",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "NSAID'S ANALGESICS"],
        },
        {
            "code": "688",
            "alt": "DET",
            "desc": "INJECTION OF DETOMIDINE HCL",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "1020",
            "alt": "PRO",
            "desc": "INJECTION OF PROLIXIN IM",
            "price": "45.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "693",
            "alt": "XYL",
            "desc": "INJECTION OF ROMPUN",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "549",
            "alt": "XY",
            "desc": "INJECTION OF XYLAZINE",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "699",
            "alt": "TO",
            "desc": "TRANQUILIZE",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "690",
            "alt": "ACB",
            "desc": "TRANQUILIZE WITH ACEPROMAZINE",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "692",
            "alt": "RES",
            "desc": "TRANQUILIZE WITH RESERPINE",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "1260",
            "alt": "RK",
            "desc": "TRANQUILIZE WITH ROMPUM AND KETAMINE",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "TRANQUILIZERS & ANESTHETICS"],
        },
        {
            "code": "5961",
            "alt": "BC2A",
            "desc": "BC2A PASTE 88 GRAM TUBE",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "9233",
            "alt": "FOL",
            "desc": "FOLIC ACID INJECTION",
            "price": "0.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "623",
            "alt": "BCOM",
            "desc": "INJECTION OF B-COMPLEX",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "222",
            "alt": "CIC",
            "desc": "INJECTION OF CACO IRON COPPER",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "671",
            "alt": "CAL",
            "desc": "INJECTION OF CALCIUM",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "220",
            "alt": "CA",
            "desc": "INJECTION OF CALCIUM",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "620",
            "alt": "CMPK",
            "desc": "INJECTION OF CALCIUM, MAGNESIUM AND PHOSPHORUS",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "555",
            "alt": "HIP",
            "desc": "INJECTION OF HIPIRON",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "536",
            "alt": "IAS",
            "desc": "INJECTION OF IRON ARSENIC AND STRYCHNINE",
            "price": "10.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "629",
            "alt": "VITC",
            "desc": "INJECTION OF VITAMIN C",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "626",
            "alt": "VITES",
            "desc": "INJECTION OF VITAMIN E AND SELENIUM",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "1261",
            "alt": "VR",
            "desc": "INJECTION OF VITAMIN RED",
            "price": "40.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "796",
            "alt": "PRDI",
            "desc": "POST RACE DRENCH WITH IRON AND VITAMINS",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "791",
            "alt": "PTD",
            "desc": "POST TRAINING DRENCH",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "794",
            "alt": "PTDI",
            "desc": "POST TRAINING DRENCH WITH ELECTROLYTES AND BLOODSHOT",
            "price": "70.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "630",
            "alt": "FA",
            "desc": "TREATMENT WITH FOLIC ACID SUPPLEMENT",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "628",
            "alt": "VBB",
            "desc": "VITAMIN BLOOD BUILDER",
            "price": "28.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "625",
            "alt": "BSB",
            "desc": "VITAMIN BSE INJECTION",
            "price": "120.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "632",
            "alt": "VIT",
            "desc": "VITAMIN INJECTION",
            "price": "0.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "619",
            "alt": "CMPKJ",
            "desc": "VITAMIN JUG WITH CALCIUM, MAGNISIUM AND PHOSPHORUS",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "VITAMINS"],
        },
        {
            "code": "9228",
            "alt": "AMI",
            "desc": "AMICAR INJECTION",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "6066",
            "alt": "BAYC",
            "desc": "BAYCOX (TOLAZATRIL PASTE-2 DOSES)",
            "price": "162.50",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "4019",
            "alt": "DBPENT",
            "desc": "EXAM, DISPENSE BOTTLE OF PENTOSAN",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "9876",
            "alt": "IMOD",
            "desc": "IMMUNOMODULATOR",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "996",
            "alt": "ACTL",
            "desc": "INJECTION OF ACETYLCYSTEINE",
            "price": "22.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "30",
            "alt": "CAM",
            "desc": "INJECTION OF CAMPHOR (GOMENOL)",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "790",
            "alt": "BS",
            "desc": "INJECTION OF EQUISTIM IV",
            "price": "30.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "2000",
            "alt": "GLU",
            "desc": "INJECTION OF GLUCOSAMINE",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "645",
            "alt": "LAC",
            "desc": "INJECTION OF LACTANASE IV",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "421",
            "alt": "LIPO",
            "desc": "INJECTION OF LIPOTROPES IV",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "85",
            "alt": "PB",
            "desc": "INJECTION OF P-BLOCK",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "7789",
            "alt": "INT",
            "desc": "INTERFERON F2A 250 ML BOTTLE 100 UNITS PER DOSE",
            "price": "150.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "8111",
            "alt": "LARG",
            "desc": "L ARGININE",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "571",
            "alt": "MMA",
            "desc": "MISCELLANEOUS MEDICATION ADMINISTERED",
            "price": "0.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "3091",
            "alt": "PENT",
            "desc": "PENTOSAN INJECTION",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "797",
            "alt": "B",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "985",
            "alt": "BP",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING AND PAIN",
            "price": "45.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "801",
            "alt": "BR",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING AND RESPIRATORY",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "802",
            "alt": "BT",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING AND TYING-UP",
            "price": "35.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "691",
            "alt": "BRT",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING, BREATHING AND TYING UP",
            "price": "50.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "916",
            "alt": "BPR",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING, PAIN AND RESPIRATORY",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "917",
            "alt": "BPT",
            "desc": "POST EXERCISE MEDICATION FOR BLEEDING, PAIN AND TYING-UP",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "798",
            "alt": "P",
            "desc": "POST EXERCISE MEDICATION FOR PAIN",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "806",
            "alt": "PR",
            "desc": "POST EXERCISE MEDICATION FOR PAIN AND RESPIRATORY",
            "price": "40.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "807",
            "alt": "PT",
            "desc": "POST EXERCISE MEDICATION FOR PAIN AND TYING-UP",
            "price": "40.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "918",
            "alt": "PRT",
            "desc": "POST EXERCISE MEDICATION FOR PAIN, RESPIRATORY AND TYINGUP-",
            "price": "65.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "805",
            "alt": "TU",
            "desc": "POST EXERCISE MEDICATION FOR TYING-UP",
            "price": "60.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "960",
            "alt": "BPRT",
            "desc": "POST EXERCISE MEDS. FOR BREATHING, PAIN, RESP. AND TYING-UP",
            "price": "75.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "539",
            "alt": "RESP",
            "desc": "RESPIRATORY TREATMENT",
            "price": "20.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "262",
            "alt": "ROBIN",
            "desc": "ROBINUL INJECTION IV",
            "price": "15.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "154",
            "alt": "ATP",
            "desc": "TREATMENT WITH ATP",
            "price": "25.00",
            "path": ["MEDICATION ADMINISTERED", "OTHER"],
        },
        {
            "code": "979",
            "alt": "R1000",
            "desc": "EXAM DISPENSE BOTTLE OF REGUMATE 1000 CC",
            "price": "350.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "146",
            "alt": "DBEST",
            "desc": "EXAM DISPENSE ONE BOTTLE OF ESTRONE",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "687",
            "alt": "DBACTH",
            "desc": "EXAM, DISPENSE BOTTLE OF ACTH",
            "price": "55.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "1009",
            "alt": "DBADC",
            "desc": "EXAM, DISPENSE BOTTLE OF ADRENAL CORTEX 50 CC",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "1254",
            "alt": "DBDEPO",
            "desc": "EXAM, DISPENSE BOTTLE OF DEPO-PROVERA 30 ML",
            "price": "225.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "981",
            "alt": "DBBCP",
            "desc": "EXAM, DISPENSE BOTTLE OF ECP",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "970",
            "alt": "DBES",
            "desc": "EXAM, DISPENSE BOTTLE OF EQUI-STEM",
            "price": "240.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "982",
            "alt": "DBHCG",
            "desc": "EXAM, DISPENSE BOTTLE OF HCG",
            "price": "70.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "684",
            "alt": "DBLEVO",
            "desc": "EXAM, DISPENSE BOTTLE OF LEVOTHYROXINE",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "980",
            "alt": "TL",
            "desc": "EXAM, DISPENSE THYROL -POWDER",
            "price": "55.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "6098",
            "alt": "PURG",
            "desc": "PURGOLIDE MESTILATE 1MG/ML 120 ML BOTTLE",
            "price": "150.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "8854",
            "alt": "TLL",
            "desc": "THROID POWDER LARGE BUCKET",
            "price": "250.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER HORMONES"],
        },
        {
            "code": "800",
            "alt": "DVAMP",
            "desc": "EXAM, DISPENSE BOTTLE OF AMPICILLIN",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - PENICILLINS"],
        },
        {
            "code": "8500",
            "alt": "DBPPG2",
            "desc": "EXAM, DISPENSE BOTTLE OF PROCAINE PENNICILLIN 250ML",
            "price": "45.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - PENICILLINS"],
        },
        {
            "code": "804",
            "alt": "DBPPG",
            "desc": "EXAM, DISPENSE BOTTLE OF PROCAINE PENNICILLIN G 100 CC'S",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - PENICILLINS"],
        },
        {
            "code": "857",
            "alt": "DBGEN",
            "desc": "EXAM, DISPENSE BOTTLE OF GENTOCIN 100 ML",
            "price": "70.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "858",
            "alt": "DBGBN2",
            "desc": "EXAM, DISPENSE BOTTLE OF GENTOCIN 250 ML",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "37",
            "alt": "DBBAYI",
            "desc": "EXAM, DISPENSE BOTTLE OF INJECTABLE BAYTRIL",
            "price": "300.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "826",
            "alt": "DBNAX",
            "desc": "EXAM, DISPENSE BOTTLE OF NAXCEL",
            "price": "105.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "817",
            "alt": "DBTET",
            "desc": "EXAM, DISPENSE BOTTLE OF TETRACYCLINE 250CC'S",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "819",
            "alt": "DBDOX",
            "desc": "EXAM, DISPENSE CONTAINER OF DOXYCYCLINE HYCLATE POWDER",
            "price": "250.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "1015",
            "alt": "SMZS",
            "desc": "EXAM, DISPENSE SMZ SYRUP",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "544",
            "alt": "DBEPM",
            "desc": "EXAM, DISPENSE TREATMENT WITH EPM MEDICATION",
            "price": "155.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "820",
            "alt": "DBTMS5",
            "desc": "EXAM, DISPENSE TRIMETHOPRIM SULFA PILLS #500",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "63",
            "alt": "TUCO",
            "desc": "EXAM, DISPENSE TUCOPRIM POWDER",
            "price": "45.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "3906",
            "alt": "DBBAYL",
            "desc": "LARGE BOTTLE OF BAYTRIL 100 MG PER ML. 250 CC BOTTLE",
            "price": "0.00",
            "path": ["MEDICATIONS DISPENSED", "ANTIBIOTICS - OTHER"],
        },
        {
            "code": "927",
            "alt": "VC",
            "desc": "EXAM, DISPENSE ONE CASE OF VETWRAP",
            "price": "72.00",
            "path": ["MEDICATIONS DISPENSED", "BANDAGES & MATERIALS"],
        },
        {
            "code": "923",
            "alt": "COT",
            "desc": "EXAM, DISPENSE ONE ROLL OF COTTON",
            "price": "10.00",
            "path": ["MEDICATIONS DISPENSED", "BANDAGES & MATERIALS"],
        },
        {
            "code": "926",
            "alt": "V",
            "desc": "EXAM, DISPENSE ONE ROLL OF VETWRAP",
            "price": "3.00",
            "path": ["MEDICATIONS DISPENSED", "BANDAGES & MATERIALS"],
        },
        {
            "code": "988",
            "alt": "FUL",
            "desc": "EXAM, DISPENSE FULVICIN LARGE-",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "DERMATITIS/TOPICAL ANTISEPTICS"],
        },
        {
            "code": "900",
            "alt": "NOLV",
            "desc": "EXAM, DISPENSE NOLVASAN OINTMENT",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "DERMATITIS/TOPICAL ANTISEPTICS"],
        },
        {
            "code": "899",
            "alt": "NOLVL",
            "desc": "EXAM, DISPENSE NOLVESAN LARGE",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "DERMATITIS/TOPICAL ANTISEPTICS"],
        },
        {
            "code": "1016",
            "alt": "SSD",
            "desc": "EXAM, DISPENSE SILVER SULFADIAZINE CREAM",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "DERMATITIS/TOPICAL ANTISEPTICS"],
        },
        {
            "code": "28",
            "alt": "DBNAQI",
            "desc": "EXAM, DISPENSE BOTTLE INJECTABLE NAQUASONE",
            "price": "35.00",
            "path": ["MEDICATIONS DISPENSED", "DIURETICS"],
        },
        {
            "code": "592",
            "alt": "DBLAS",
            "desc": "EXAM, DISPENSE BOTTLE OF LASIX",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "DIURETICS"],
        },
        {
            "code": "1257",
            "alt": "LR",
            "desc": "EXAM, DISPENSE 1 LITER LACTATED RINGERS",
            "price": "8.00",
            "path": ["MEDICATIONS DISPENSED", "FLUIDS"],
        },
        {
            "code": "1250",
            "alt": "DBCAR",
            "desc": "CARAFATE TABLETS",
            "price": "120.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "863",
            "alt": "FUR",
            "desc": "EXAM, DISPENSE 1 LB FURACIN OINTMENT",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "1252",
            "alt": "DBLACL",
            "desc": "EXAM, DISPENSE LARGE BOTTLE OF LACTANASE 100CC",
            "price": "130.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "358",
            "alt": "DGPB",
            "desc": "EXAM, DISPENSE ONE GALLON OF PEPTO BISMOL",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "1010",
            "alt": "LACP",
            "desc": "EXAM, DISPENSE ONE TUBE OF LACTANASE PASTE",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "655",
            "alt": "PROBP",
            "desc": "EXAM, DISPENSE PROBIAS PASTE",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "656",
            "alt": "PROB",
            "desc": "EXAM, DISPENSE PROBIAS POWDER",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "1002",
            "alt": "FULP",
            "desc": "EXAM, DISPENSE TUBE OF FULVICIN PASTE 12.5g",
            "price": "28.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "1003",
            "alt": "LEVP",
            "desc": "EXAM, DISPENSE TUBE OF LEVAMISOLE PASTE",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "144",
            "alt": "OMBP",
            "desc": "EXAM, DISPENSE TUBE OF OMEPRAZOLE",
            "price": "18.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "43",
            "alt": "GG",
            "desc": "TREATMENT WITH GASTROGUARD ONE DOSE",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "G.I. MEDICATIONS"],
        },
        {
            "code": "894",
            "alt": "DBNOV",
            "desc": "EXAM, DISPENSE 1 BOTTLE DIPYRONE 100 ML",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "893",
            "alt": "DBANB",
            "desc": "EXAM, DISPENSE BOTTLE OF BANAMINE 100 CC",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "6210",
            "alt": "DBKET",
            "desc": "EXAM, DISPENSE BOTTLE OF KETOFEN",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "229",
            "alt": "DBLAC",
            "desc": "EXAM, DISPENSE BOTTLE OF LACTANASE",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "891",
            "alt": "DBUTB",
            "desc": "EXAM, DISPENSE BOTTLE OF PHENYLBUTAZONE 100 CC",
            "price": "28.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "837",
            "alt": "DBBUT",
            "desc": "EXAM, DISPENSE BOTTLE OF PHENYLBUTAZONE TABLETS 1g",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "47",
            "alt": "DBRVI",
            "desc": "EXAM, DISPENSE BOTTLE OF RVI",
            "price": "125.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "8904",
            "alt": "DBANBL",
            "desc": "EXAM, DISPENSE ONE BOTTLE FLUNIXIN 250CC",
            "price": "140.00",
            "path": ["MEDICATIONS DISPENSED", "INJECTABLE NSAID'S"],
        },
        {
            "code": "4798",
            "alt": "POLY",
            "desc": "BOTTLE OF POLYGLYCAN",
            "price": "120.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "901",
            "alt": "DBDBX",
            "desc": "EXAM, DISPENSE BOTTLE OF DEXAMETHASONE 100ML",
            "price": "44.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "903",
            "alt": "DBFLU",
            "desc": "EXAM, DISPENSE BOTTLE OF FLUCORT",
            "price": "70.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "1019",
            "alt": "DBHAIV",
            "desc": "EXAM, DISPENSE BOTTLE OF HYALURONIC ACID IV",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "46",
            "alt": "DBP",
            "desc": "EXAM, DISPENSE BOTTLE OF P-BLOC",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "1014",
            "alt": "DBVOR",
            "desc": "EXAM, DISPENSE BOTTLE OF VOREN",
            "price": "80.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "147",
            "alt": "DBGLU",
            "desc": "TREATMENT WITH ONE BOTTLE GLUCOSAMINE",
            "price": "60.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER INJECTABLE ANTI-INFLAM."],
        },
        {
            "code": "1012",
            "alt": "CHOND",
            "desc": "EXAM, DISPENSE CHONDROCARB JOINT SUPPLEMENT",
            "price": "80.00",
            "path": ["MEDICATIONS DISPENSED", "INTRA-ARTICULAR PRODUCTS"],
        },
        {
            "code": "368",
            "alt": "T",
            "desc": "EXAM, DISPENSE ONE VIAL OF TRAUMBEL",
            "price": "8.00",
            "path": ["MEDICATIONS DISPENSED", "INTRA-ARTICULAR PRODUCTS"],
        },
        {
            "code": "367",
            "alt": "Z",
            "desc": "EXAM, DISPENSE ONE VIAL OF ZEEL",
            "price": "8.00",
            "path": ["MEDICATIONS DISPENSED", "INTRA-ARTICULAR PRODUCTS"],
        },
        {
            "code": "879",
            "alt": "DMSOP",
            "desc": "EXAM, DISPENSE DMSO 1 PINT",
            "price": "35.00",
            "path": ["MEDICATIONS DISPENSED", "LEG PREPARATIONS"],
        },
        {
            "code": "882",
            "alt": "DMSOG",
            "desc": "EXAM, DISPENSE DMSO GEL",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "LEG PREPARATIONS"],
        },
        {
            "code": "881",
            "alt": "FURSW",
            "desc": "EXAM, DISPENSE ONE PT FURACIN SWEAT",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "LEG PREPARATIONS"],
        },
        {
            "code": "36",
            "alt": "RIT",
            "desc": "EXAM, TREATMENT WITH RITE'S PAINT",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "LEG PREPARATIONS"],
        },
        {
            "code": "953",
            "alt": "N19B",
            "desc": 'BOX OF 19 X 1 1/2" NEEDLES',
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "933",
            "alt": "N16B",
            "desc": "EXAM, DISPENSE 16G NEEDLES 100 CT.",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "937",
            "alt": "N20B",
            "desc": "EXAM, DISPENSE 20g NEEDLES 100 CT.",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "935",
            "alt": "N18B",
            "desc": "EXAM, DISPENSE BOX 18 G NEEDLES",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "944",
            "alt": "S12B",
            "desc": "EXAM, DISPENSE BOX OF 12 CC SYRINGES",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "946",
            "alt": "S20B",
            "desc": "EXAM, DISPENSE BOX OF 20 CC SYRINGES",
            "price": "35.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "940",
            "alt": "S3B",
            "desc": "EXAM, DISPENSE BOX OF 3 CC SYRINGES",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "947",
            "alt": "S35B",
            "desc": "EXAM, DISPENSE BOX OF 35 CC SYRINGES",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "948",
            "alt": "S6B",
            "desc": "EXAM, DISPENSE BOX OF 6 CC SYRINGES",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "950",
            "alt": "S60B",
            "desc": "EXAM, DISPENSE BOX OF 60 CC SYRINGES",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "951",
            "alt": "DS",
            "desc": "EXAM, DISPENSE DOSING SYRINGE",
            "price": "4.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "949",
            "alt": "S60",
            "desc": "EXAM, DISPENSE ONE 60 CC SYRINGE",
            "price": "2.00",
            "path": ["MEDICATIONS DISPENSED", "NEEDLES & SYRINGES"],
        },
        {
            "code": "7023",
            "alt": None,
            "desc": "100 SCOOP APPLE FLAVORED PHENYLBUTAZONE POWDER",
            "price": "45.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "4960",
            "alt": "BQUI",
            "desc": "BQUIOX PASTE",
            "price": "0.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "82",
            "alt": "DBARQ",
            "desc": "EXAM, DISPENSE BOTTLE OF ARQUEL",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "897",
            "alt": "DBASA",
            "desc": "EXAM, DISPENSE ONE BOTTLE OF ASPIRIN 100 ML",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "24",
            "alt": "DBANP",
            "desc": "EXAM, DISPENSE TREATMENT WITH BANAMINE PASTE",
            "price": "45.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "836",
            "alt": "DPB12",
            "desc": "EXAM, DISPENSE TUBE OF PHENYLBUTAZONE PASTE 12g",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "6051",
            "alt": "BUTP",
            "desc": "ORAL PHENYLBUTAZONE POWDER 100 SCOOP CONTAINER",
            "price": "45.00",
            "path": ["MEDICATIONS DISPENSED", "ORAL NSAID'S"],
        },
        {
            "code": "905",
            "alt": "DBPRED",
            "desc": "EXAM, DISPENSE 1000CT BOTTLE PREDNISOLONE 20MG TABS.",
            "price": "120.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER ORAL ANTI-INFLAM."],
        },
        {
            "code": "851",
            "alt": "IS",
            "desc": "EXAM, DISPENSE ISOXSUPRINE TABLETS",
            "price": "42.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER ORAL ANTI-INFLAM."],
        },
        {
            "code": "852",
            "alt": "NAQ",
            "desc": "EXAM, DISPENSE NAQUASONE BOLUS",
            "price": "5.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER ORAL ANTI-INFLAM."],
        },
        {
            "code": "21",
            "alt": "NAQP",
            "desc": "EXAM, DISPENSE NAQUASONE PASTE",
            "price": "28.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER ORAL ANTI-INFLAM."],
        },
        {
            "code": "6033",
            "alt": "UCII",
            "desc": "FLEXADIN UCII POWDER ORAL",
            "price": "167.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER ORAL ANTI-INFLAM."],
        },
        {
            "code": "527",
            "alt": "O",
            "desc": "EXAM AND DISPENSE OPTHALMIC MEDICATION",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "OPHTHALMIC DRUGS"],
        },
        {
            "code": "29",
            "alt": "DBCAM",
            "desc": "EXAM DISPENSE BOTTLE OF CAMPHOR",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "554",
            "alt": "ALB",
            "desc": "EXAM, DISPENSE ALBUTEROL SYRUP",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "533",
            "alt": "BH",
            "desc": "EXAM, DISPENSE ANTIHISTAMINE GRANULES",
            "price": "35.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "997",
            "alt": "DBACTL",
            "desc": "EXAM, DISPENSE BOTTLE OF ACETYLCYSTEINE 100 CC",
            "price": "60.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "130",
            "alt": "DI",
            "desc": "EXAM, DISPENSE BOTTLE OF DIAMINE IODIDE POWDER",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "1255",
            "alt": "DBINT",
            "desc": "EXAM, DISPENSE BOTTLE OF INTAL 20 MG/2 ML",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "127",
            "alt": "DBKR",
            "desc": "EXAM, DISPENSE BOTTLE OF KENTUCKY RED",
            "price": "60.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "5503",
            "alt": None,
            "desc": "EXAM, DISPENSE BOTTLE OF L ARGININE",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "1500",
            "alt": "DBMET",
            "desc": "EXAM, DISPENSE BOTTLE OF METICORT",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "890",
            "alt": "VENT",
            "desc": "EXAM, DISPENSE BOTTLE OF VENTIPULMIN SYRUP 100 ML",
            "price": "140.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "1011",
            "alt": "VENTL",
            "desc": "EXAM, DISPENSE BOTTLE OF VENTIPULMIN SYRUP 330 ML",
            "price": "300.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "1008",
            "alt": "CKP",
            "desc": "EXAM, DISPENSE C.K. POWDER",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "131",
            "alt": "CE",
            "desc": "EXAM, DISPENSE COUGH BASE SYRUP",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "64",
            "alt": "TUCOL",
            "desc": "EXAM, DISPENSE LARGE CONTAINER OF TUCOPRIM",
            "price": "180.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "6877",
            "alt": "NEB",
            "desc": "NEBULISER SOLUTION 500ML",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "RESPIRATORY DRUGS"],
        },
        {
            "code": "865",
            "alt": "ICH",
            "desc": "EXAM, DISPENSE 1LB. ICTHAMMOL",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "TOPICAL MEDICATIONS"],
        },
        {
            "code": "26",
            "alt": "FURSP",
            "desc": "EXAM, DISPENSE FURACIN SPRAY",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "TOPICAL MEDICATIONS"],
        },
        {
            "code": "866",
            "alt": "P8",
            "desc": "EXAM, DISPENSE PANALOG 8 oz.",
            "price": "90.00",
            "path": ["MEDICATIONS DISPENSED", "TOPICAL MEDICATIONS"],
        },
        {
            "code": "867",
            "alt": "P30",
            "desc": "EXAM, DISPENSE PANALOG TUBE 30 ML",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "TOPICAL MEDICATIONS"],
        },
        {
            "code": "9631",
            "alt": "SUR",
            "desc": "SURPASS TOPICAL ANTI INFLAMMATORY CREAM",
            "price": "70.00",
            "path": ["MEDICATIONS DISPENSED", "TOPICAL MEDICATIONS"],
        },
        {
            "code": "542",
            "alt": "DBACK",
            "desc": "EXAM, DISPENSE BOTTLE OF ACEPROMAZINE MALEATE",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "1013",
            "alt": "DBDET",
            "desc": "EXAM, DISPENSE BOTTLE OF DETOMIDINE HCL 30ML",
            "price": "400.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "909",
            "alt": "DROBB",
            "desc": "EXAM, DISPENSE BOTTLE OF METHOCARBONAL 100 CC",
            "price": "44.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "547",
            "alt": "DTR",
            "desc": "EXAM, DISPENSE BOTTLE OF METHOCARBONAL TABLETS 500 CT.",
            "price": "110.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "394",
            "alt": "DBRES",
            "desc": "EXAM, DISPENSE BOTTLE OF RESERPINE",
            "price": "50.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "550",
            "alt": "DBX",
            "desc": "EXAM, DISPENSE BOTTLE OF XYLAZINE",
            "price": "80.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "27",
            "alt": "DILP",
            "desc": "EXAM, DISPENSE TREATMENT WITH DILANTIN PASTE",
            "price": "28.00",
            "path": ["MEDICATIONS DISPENSED", "TRANQUILIZERS & MUSCLE RELAX."],
        },
        {
            "code": "1589",
            "alt": "ERY",
            "desc": "ERYTHO EQ BLOOD BUILDER ORAL POWDER",
            "price": "85.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "587",
            "alt": "DBHEMO",
            "desc": "EXAM DISPENSE BOTTLE OF HEMO/150 100ML",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "567",
            "alt": "DBB12",
            "desc": "EXAM, DISPENSE BOTTLE OF B-12 3000 MCG 100 CC",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "563",
            "alt": "DBBC",
            "desc": "EXAM, DISPENSE BOTTLE OF B-COMPLEX VITAMINS",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "561",
            "alt": "DBCIC",
            "desc": "EXAM, DISPENSE BOTTLE OF CACO-COPPER",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "559",
            "alt": "DBLIV",
            "desc": "EXAM, DISPENSE BOTTLE OF DELVOREX",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "556",
            "alt": "DBHIP",
            "desc": "EXAM, DISPENSE BOTTLE OF HIP IRON",
            "price": "60.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "150",
            "alt": "DBLIPO",
            "desc": "EXAM, DISPENSE BOTTLE OF LIPOTROPES",
            "price": "30.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "565",
            "alt": "DBC",
            "desc": "EXAM, DISPENSE BOTTLE OF VITAMIN C 100 ML",
            "price": "15.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "1253",
            "alt": "DBCL",
            "desc": "EXAM, DISPENSE BOTTLE OF VITAMIN C 250 ML",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "45",
            "alt": "DBIAS",
            "desc": "EXAM, DISPENSE BOTTLE OF WESTERN FORMULA",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "449",
            "alt": "ELEC",
            "desc": "EXAM, DISPENSE BUCKET OF ELECTROLYTES 25#",
            "price": "75.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "346",
            "alt": "HIPP",
            "desc": "EXAM, DISPENSE HIPPARION POWDER",
            "price": "100.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "570",
            "alt": "MMD",
            "desc": "EXAM, DISPENSE MISCELLANEOUS MEDICATION",
            "price": "0.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "448",
            "alt": "FOLIC",
            "desc": "EXAM, DISPENSE TREATMENT OF FOLIC ACID",
            "price": "40.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "66",
            "alt": "DBB15",
            "desc": "EXAM, DISPENSE TREATMENT WITH ONE BOTTLE OF B-15",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "6677",
            "alt": "DBFOL",
            "desc": "FOLIC ACID INJECTABLE BOTTLE 100 CC",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "VITAMINS"],
        },
        {
            "code": "399",
            "alt": "RL",
            "desc": "EXAM, DISPENSE RED LUNG PLUS POWDER",
            "price": "90.00",
            "path": ["MEDICATIONS DISPENSED", "NON-VITAMIN FEED SUPPLEMENTS"],
        },
        {
            "code": "9990",
            "alt": "NAV",
            "desc": "EXAM AND DISPENSE 28 DAY SUPPLY OF NAVIGATOR PASTE-EPM TXT",
            "price": "1200.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "9994",
            "alt": "CYP",
            "desc": "EXAM, DISPENSE 100 ML CYPROHEPTADINE 100MG/MG",
            "price": "150.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "376",
            "alt": "DBADN",
            "desc": "EXAM, DISPENSE BOTTLE OF ADENOSINE",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "1258",
            "alt": "DBCYPR",
            "desc": "EXAM, DISPENSE BOTTLE OF CYPROHEPTADINE 120 ML",
            "price": "125.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "141",
            "alt": "DBWNV",
            "desc": "EXAM, DISPENSE BOTTLE OF WEST NILE VACCINE",
            "price": "150.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "65",
            "alt": "CK",
            "desc": "EXAM, DISPENSE C.K. POWDER",
            "price": "25.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "500",
            "alt": "ETHER",
            "desc": "EXAM, DISPENSE ETHER",
            "price": "20.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "374",
            "alt": "NL",
            "desc": "EXAM, DISPENSE NEIGH-LOX",
            "price": "200.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "250",
            "alt": "MARQ",
            "desc": "EXAM, DISPENSE TUBE OF MARQUIS",
            "price": "280.00",
            "path": ["MEDICATIONS DISPENSED", "OTHER"],
        },
        {
            "code": "5908",
            "alt": "CASL",
            "desc": "CASLICKS PROCEEDURE",
            "price": "115.00",
            "path": ["REPRODUCTIVE PROCEDURES", "GENERAL BROODMARE WORK"],
        },
        {
            "code": "1275",
            "alt": "BREED",
            "desc": "INSEMINATE MARE",
            "price": "50.00",
            "path": ["REPRODUCTIVE PROCEDURES", "GENERAL BROODMARE WORK"],
        },
        {
            "code": "450",
            "alt": "REC",
            "desc": "RECTAL PALPATION",
            "price": "40.00",
            "path": ["REPRODUCTIVE PROCEDURES", "GENERAL BROODMARE WORK"],
        },
        {
            "code": "98",
            "alt": "US",
            "desc": "ULTRASOUND FOR PREGNANCY",
            "price": "60.00",
            "path": ["REPRODUCTIVE PROCEDURES", "GENERAL BROODMARE WORK"],
        },
        {
            "code": "501",
            "alt": "CAST",
            "desc": "CASTRATION",
            "price": "500.00",
            "path": ["SURGICAL PROCEDURES"],
        },
        {
            "code": "1256",
            "alt": "CRYO",
            "desc": "CRYOSURGICAL PROCEDURE",
            "price": "150.00",
            "path": ["SURGICAL PROCEDURES"],
        },
        {
            "code": "503",
            "alt": "CUT1",
            "desc": "SUTURE LACERATION",
            "price": "70.00",
            "path": ["SURGICAL PROCEDURES"],
        },
        {
            "code": "5030",
            "alt": "SR",
            "desc": "SUTURE REMOVAL",
            "price": "20.00",
            "path": ["SURGICAL PROCEDURES"],
        },
        {
            "code": "95",
            "alt": "BAND",
            "desc": "BANDAGE LEG",
            "price": "60.00",
            "path": ["VET. PROCEDURES & SERVICES", "BANDAGING"],
        },
        {
            "code": "1001",
            "alt": "GEL",
            "desc": "EXAM, DISPENSE GEL CAST",
            "price": "15.00",
            "path": ["VET. PROCEDURES & SERVICES", "BANDAGING"],
        },
        {
            "code": "99",
            "alt": "ACU",
            "desc": "ACUPUNCTURE",
            "price": "100.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "1000",
            "alt": "CS",
            "desc": "CLEAN SHEATH",
            "price": "60.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "999",
            "alt": "DP",
            "desc": "DRENCH PROCEDURE",
            "price": "50.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "23",
            "alt": "SW",
            "desc": "EXTRACORPOREAL SHOCK WAVE THERAPY",
            "price": "100.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "38",
            "alt": "SWR",
            "desc": "EXTRACORPOREAL SHOCK WAVE THERAPY",
            "price": "150.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "92",
            "alt": "FGP",
            "desc": "FLUSH GUTTERAL POUCHES WITH ANTIBIOTICS AND FLUIDS",
            "price": "30.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "93",
            "alt": "FNLD",
            "desc": "FLUSH NASOLACRIMAL DUCT",
            "price": "15.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "106",
            "alt": "BURSA",
            "desc": "INJECT NAVICULAR BURSAS",
            "price": "100.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "310",
            "alt": "IP",
            "desc": "INJECT PALATE",
            "price": "40.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "1007",
            "alt": "INLFSP",
            "desc": "INJECTION OF LEFT FRONT SPLINT",
            "price": "50.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "1006",
            "alt": "INLHSP",
            "desc": "INJECTION OF LEFT HIND SPLINT",
            "price": "50.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "1005",
            "alt": "INRFSP",
            "desc": "INJECTION OF RIGHT FRONT SPLINT",
            "price": "50.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "1004",
            "alt": "INRHSP",
            "desc": "INJECTION OF RIGHT HIND SPLINT",
            "price": "50.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "707",
            "alt": "PRD",
            "desc": "POST TRAINING/RACE DRENCH WITH VITAMINS AND ELECTROLYTES",
            "price": "25.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "739",
            "alt": "PS",
            "desc": "PROFESSIONAL SERVICE",
            "price": "0.00",
            "path": ["VET. PROCEDURES & SERVICES", "OTHER"],
        },
        {
            "code": "5000",
            "alt": "BD",
            "desc": "BOARD",
            "price": "500.00",
            "path": ["OTHER"],
        },
        {
            "code": "5002",
            "alt": "DBD",
            "desc": "DAILY BOARD",
            "price": "18.00",
            "path": ["OTHER"],
        },
        {
            "code": "5003",
            "alt": "PRBD",
            "desc": "DAILY LAY-UP BOARD",
            "price": "20.00",
            "path": ["OTHER"],
        },
        {
            "code": "3126",
            "alt": "EN",
            "desc": "FLEET ENEMA",
            "price": "10.00",
            "path": ["OTHER"],
        },
        {
            "code": "9452",
            "alt": "HOSP",
            "desc": "HOSPITALIZATION",
            "price": "30.00",
            "path": ["OTHER"],
        },
        {
            "code": "5001",
            "alt": "LBD",
            "desc": "LAY-UP BOARD",
            "price": "550.00",
            "path": ["OTHER"],
        },
        {
            "code": "5005",
            "alt": "MFB",
            "desc": "MARE AND FOAL BOARD",
            "price": "600.00",
            "path": ["OTHER"],
        },
        {
            "code": "808",
            "alt": "RT",
            "desc": "POST EXERCISE MEDICATION FOR RESPIRATORY AND TYING-UP",
            "price": "40.00",
            "path": ["OTHER"],
        },
        {
            "code": "19",
            "alt": "TRYP",
            "desc": "TRYPZYME SPRAY",
            "price": "35.00",
            "path": ["OTHER"],
        },
    ]

    existing_codes = {cc_tuple[0] for cc_tuple in session.query(ChargeCode.code).all()}
    new_charge_codes_instances = []
    changes_made = False

    for data in charge_codes_data:
        if data["code"] not in existing_codes:
            category_id = (
                _get_category_id_by_path(session, data["path"])
                if data.get("path")
                else None
            )
            if category_id is None and data.get("path"):
                logger.warning(
                    f"Could not find category for charge code '{data['code']}' using path {data['path']}. Assigning to root or skipping."
                )

            charge_code_model_data = {
                "code": data["code"],
                "alternate_code": data.get("alt"),
                "description": data["desc"],
                "standard_charge": Decimal(data["price"]),
                "category_id": category_id,
                "is_active": True,
                "taxable": False,
                "created_by": "system_init",
                "modified_by": "system_init",
            }

            new_charge_codes_instances.append(ChargeCode(**charge_code_model_data))
            logger.info(
                f"Prepared charge code: {data['code']} with category_id: {category_id}"
            )
            changes_made = True
        else:
            logger.info(f"Charge code '{data['code']}' already exists, skipping.")

    if new_charge_codes_instances:
        session.add_all(new_charge_codes_instances)
        logger.info(
            f"Successfully prepared {len(new_charge_codes_instances)} new charge codes."
        )
    else:
        logger.info("No new charge codes to add.")

    return changes_made


def add_initial_data_main():
    logger.info("Running script to add initial data to the database...")

    # Initialize DatabaseManager locally for this standalone script
    _db_manager = DatabaseManager(AppConfig, config_manager)

    try:
        _db_manager.initialize_database()  # Corrected call
        logger.info("Database initialized.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        return

    session = _db_manager.get_session()  # Corrected call
    try:
        logger.info("Starting to add initial reference data...")
        changes_made_this_block = False
        if add_roles(session):
            changes_made_this_block = True
        if add_admin_user(session):
            changes_made_this_block = True
        if changes_made_this_block:
            session.commit()
            logger.info("Committed roles and admin user.")
            changes_made_this_block = False

        if add_charge_code_categories(session):
            session.commit()
            logger.info("Committed charge code categories.")

        if add_state_provinces(session):
            session.commit()
            logger.info("Committed states/provinces.")

        if add_initial_locations(session):
            changes_made_this_block = True
        if add_sample_owners(session):
            changes_made_this_block = True
        if add_all_charge_codes(session):
            changes_made_this_block = True
        if changes_made_this_block:
            session.commit()
            logger.info("Committed locations, owners, and all charge codes.")

        logger.info("Initial data setup process completed successfully.")

    except SQLAlchemyError as e_sql:
        logger.error(f"SQLAlchemyError during data population: {e_sql}", exc_info=True)
        session.rollback()
    except Exception as e_gen:
        logger.error(
            f"An unexpected error occurred during data population: {e_gen}",
            exc_info=True,
        )
        session.rollback()
    finally:
        if session and session.is_active:  # Check session.is_active before closing
            _db_manager.close()  # Corrected call, close on the local manager
        logger.info("Database session closed.")


if __name__ == "__main__":
    add_initial_data_main()
    print("Script execution finished. Check logs for details.")
