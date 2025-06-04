# scripts/add_initial_data.py
"""
EDSI Veterinary Management System - Add Initial Data Script
Version: 1.2.13
Purpose: Populates the database with essential initial data.
         - Corrected commit order to ensure states/provinces are saved
           before locations and owners that reference them.
         - Updated ChargeCodeCategory structure to a 2-level hierarchy
           based on user-provided list, dropping "VETERINARY" as top level.
         - Updated sample charge codes to use new 2-level category paths.
Last Updated: June 3, 2025
Author: Gemini

Changelog:
- v1.2.13 (2025-06-03):
    - Replaced `categories_structure` in `add_charge_code_categories` with the
      new 2-level hierarchy based on user's scanned document.
    - Updated `target_category_path` in `add_sample_charge_codes` to align
      with the new 2-level category structure (e.g., ["ANTHELMINTICS", "ADMINISTERED"]).
- v1.2.12 (2025-06-02):
    - Modified `add_initial_data_main` to commit the session immediately
      after `add_state_provinces` if changes were made. This resolves
      warnings about state codes not being found when creating
      initial locations and owners.
- v1.2.11 (2025-06-02):
    - Imported new ChargeCodeCategory model.
    - Added new function `add_charge_code_categories` to create hierarchical
      charge code categories.
    - Modified `add_sample_charge_codes` to use `category_id`.
    - Updated `add_initial_data_main` to call `add_charge_code_categories`.
- v1.2.10 (2025-05-23) (User's baseline):
    - Original version details.
"""
import logging
import os
import sys
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Any

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config.database_config import db_manager
    from models import (
        User,
        Role,
        UserRole,
        StateProvince,
        ChargeCodeCategory,
        ChargeCode,
        Veterinarian,  # Keep for completeness, though not added in this script
        Location,
        Owner,
    )
except ImportError as e:
    print(f"Error importing modules in add_initial_data.py: {e}")
    sys.exit(1)

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
    # MODIFIED: New 2-level structure based on user's image
    categories_structure = [
        {
            "name": "ANTHELMINTICS",
            "level": 1,
            "children": [
                {"name": "ADMINISTERED", "level": 2, "children": []},
                {"name": "DISPENSED", "level": 2, "children": []},
            ],
        },
        {"name": "CALL FEES", "level": 1, "children": []},
        {
            "name": "DIAGNOSTIC PROCEDURES",
            "level": 1,
            "children": [
                {"name": "NERVE BLOCKS", "level": 2, "children": []},
                {"name": "JOINT BLOCKS", "level": 2, "children": []},
                {"name": "RADIOLOGY - FRONT LEG", "level": 2, "children": []},
                {"name": "RADIOLOGY - HIND LEG", "level": 2, "children": []},
                {"name": "RADIOLOGY - OTHER", "level": 2, "children": []},
                {"name": "ULTRASOUND EXAM OF EXTREMITIES", "level": 2, "children": []},
                {
                    "name": "OTHER",
                    "level": 2,
                    "children": [],
                },  # OTHER under Diagnostic Procedures
            ],
        },
        {
            "name": "EXAMINATIONS",
            "level": 1,
            "children": [
                {"name": "SICK HORSE EXAMS", "level": 2, "children": []},
                {"name": "OTHER EXAMS", "level": 2, "children": []},
            ],
        },
        {
            "name": "IMMUNIZATIONS",
            "level": 1,
            "children": [
                {"name": "HORSE", "level": 2, "children": []},
            ],
        },
        {
            "name": "LABORATORY PROCEDURES",
            "level": 1,
            "children": [
                {"name": "BLOOD WORK", "level": 2, "children": []},
                {
                    "name": "OTHER",
                    "level": 2,
                    "children": [],
                },  # OTHER under Laboratory Procedures
            ],
        },
        {
            "name": "MEDICATION ADMINISTERED",
            "level": 1,
            "children": [
                {"name": "ANABOLIC STEROIDS", "level": 2, "children": []},
                {"name": "ANTIBIOTICS", "level": 2, "children": []},
                {"name": "DIURETICS", "level": 2, "children": []},
                {"name": "FLUIDS ADMINISTERED", "level": 2, "children": []},
                {"name": "GASTROINTESTINAL TREATMENTS", "level": 2, "children": []},
                {"name": "INTRA-ARTICULAR INJECTIONS", "level": 2, "children": []},
                {"name": "OTHER HORMONES", "level": 2, "children": []},
                {"name": "NON-ARTICULAR INJECTIONS", "level": 2, "children": []},
                {"name": "NSAID'S ANALGESICS", "level": 2, "children": []},
                {"name": "TRANQUILIZERS & ANESTHETICS", "level": 2, "children": []},
                {"name": "VITAMINS", "level": 2, "children": []},
                {"name": "OTHER", "level": 2, "children": []},  # OTHER under Med Admin
            ],
        },
        {
            "name": "MEDICATIONS DISPENSED",
            "level": 1,
            "children": [
                {"name": "OTHER HORMONES", "level": 2, "children": []},
                {"name": "ANTIBIOTICS - PENICILLINS", "level": 2, "children": []},
                {"name": "ANTIBIOTICS - OTHER", "level": 2, "children": []},
                {"name": "BANDAGES & MATERIALS", "level": 2, "children": []},
                {"name": "DERMATITIS/TOPICAL ANTISEPTICS", "level": 2, "children": []},
                {"name": "DIURETICS", "level": 2, "children": []},
                {"name": "FLUIDS", "level": 2, "children": []},
                {"name": "G.I. MEDICATIONS", "level": 2, "children": []},
            ],
        },
    ]
    changes_made = False

    def _process_categories(
        categories_list: List[Dict[str, Any]], current_parent_id: Optional[int] = None
    ):
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
                session.flush()  # Flush to get the new_cat.category_id for children
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
    parent_id = None
    current_category_id = None
    level = 1
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


def add_sample_charge_codes(session) -> bool:
    logger.info("Preparing sample charge codes with hierarchical categories...")
    # MODIFIED: Sample charge codes updated for new 2-level category structure
    charge_codes_data = [
        {
            "code": "9991",
            "alternate_code": "IVO",
            "description": "Ivermectin and Praziquantel",
            "target_category_path": [
                "ANTHELMINTICS",
                "ADMINISTERED",
            ],  # Was ["VETERINARY", "ANTHELMINTICS", "ADMINISTERED"]
            "standard_charge": Decimal("25.00"),
            "is_active": True,
            "taxable": False,
        },
        {
            "code": "EXAM001",
            "alternate_code": "EX01",
            "description": "Routine Examination",
            "target_category_path": [
                "EXAMINATIONS"
            ],  # Was ["VETERINARY", "EXAMINATIONS"]
            "standard_charge": Decimal("75.00"),
            "is_active": True,
            "taxable": True,
        },
    ]
    for cc_data in charge_codes_data:
        cc_data.update({"created_by": "system_init", "modified_by": "system_init"})
    existing_codes = {cc_tuple[0] for cc_tuple in session.query(ChargeCode.code).all()}
    new_charge_codes_instances = []
    changes_made = False
    for data in charge_codes_data:
        if data["code"] not in existing_codes:
            category_id = (
                _get_category_id_by_path(session, data["target_category_path"])
                if "target_category_path" in data
                else None
            )
            if category_id is None and "target_category_path" in data:
                logger.warning(
                    f"Could not find category for charge code '{data['code']}' using path {data['target_category_path']}. Skipping category linkage."
                )
            charge_code_model_data = {
                k: v for k, v in data.items() if k != "target_category_path"
            }
            if category_id is not None:
                charge_code_model_data["category_id"] = category_id
            required_fields = {"code", "description", "standard_charge"}
            if not required_fields.issubset(charge_code_model_data.keys()):
                logger.error(
                    f"Missing required fields for charge code {data['code']}. Skipping."
                )
                continue
            try:
                new_charge_codes_instances.append(ChargeCode(**charge_code_model_data))
                logger.info(
                    f"Prepared charge code: {data['code']} with category_id: {category_id}"
                )
                changes_made = True
            except TypeError as te:
                logger.error(
                    f"TypeError creating ChargeCode for {data['code']}: {te}. Data: {charge_code_model_data}",
                    exc_info=True,
                )
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
        elif (
            owner_data.get("account_number") is None
        ):  # Allow adding owners without account numbers if desired
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
        print(f"CRITICAL: Database initialization failed: {e}. Cannot proceed.")
        return

    session = db_manager.get_session()
    try:
        logger.info("Starting to add initial reference data...")
        any_changes_committed_in_block = False

        if add_roles(session):
            any_changes_committed_in_block = True
        if add_admin_user(session):
            any_changes_committed_in_block = True
        if any_changes_committed_in_block:
            session.commit()
            any_changes_committed_in_block = False
            logger.info("Committed roles and admin user.")

        if add_charge_code_categories(session):
            any_changes_committed_in_block = True
        if any_changes_committed_in_block:
            session.commit()
            any_changes_committed_in_block = False
            logger.info("Committed charge code categories.")

        if add_state_provinces(session):
            any_changes_committed_in_block = True
        if any_changes_committed_in_block:  # Commit states before locations/owners
            session.commit()
            any_changes_committed_in_block = False
            logger.info("Committed states/provinces.")

        if add_initial_locations(session):
            any_changes_committed_in_block = True
        if add_sample_owners(session):
            any_changes_committed_in_block = True
        if add_sample_charge_codes(session):
            any_changes_committed_in_block = True

        if any_changes_committed_in_block:
            session.commit()
            logger.info("Committed locations, owners, and sample charge codes.")

        logger.info("Initial data setup process completed and committed successfully.")

    except SQLAlchemyError as e_sql:
        logger.error(f"SQLAlchemyError during data population: {e_sql}", exc_info=True)
        session.rollback()
        print(f"ERROR: A database error occurred during data population: {e_sql}")
    except AttributeError as e_attr:
        logger.error(f"AttributeError during data population: {e_attr}", exc_info=True)
        session.rollback()
        print(f"ERROR: An AttributeError occurred: {e_attr}")
    except Exception as e_gen:
        logger.error(
            f"An unexpected error occurred during data population: {e_gen}",
            exc_info=True,
        )
        session.rollback()
        print(f"ERROR: An unexpected error occurred during data population: {e_gen}")
    finally:
        if session and session.is_active:
            session.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    if not db_manager:
        print(
            "CRITICAL: Database manager (db_manager) not initialized prior to main call in script."
        )
    else:
        add_initial_data_main()
    print("Script execution finished. Check logs for details and potential warnings.")
