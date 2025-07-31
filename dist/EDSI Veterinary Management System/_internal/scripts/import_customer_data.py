# scripts/import_customer_data.py

"""
EDMS Veterinary Management System - Customer Data Import Script
Version: 1.0.4
Purpose: Imports horse, owner, and location data from a customer-provided CSV file
         into the EDMS database. Now correctly handles missing location contact/phone/email columns.
Last Updated: July 15, 2025
Author: Gemini

Changelog:
- v1.0.4 (2025-07-15):
    - **BUG FIX**: Removed 'Location Contact Person', 'Location Phone', 'Location Email',
      and 'Location Active' from the `unique_locations_df` column selection, as these
      columns are not present in the provided CSV screenshots, resolving `KeyError`.
    - The `_get_or_create_location` function will now correctly receive `None` for these
      fields if they are truly missing from the source data.
- v1.0.3 (2025-07-15):
    - **Precise Column Mapping**: Updated all column accesses (`df[...]`, `row.get(...)`)
      to use the exact headers identified from the user's screenshots (e.g., 'Animal Weight (lb)',
      'Physical Address Suburb/Neighborhood', 'Email Addresses', 'Mobile Numbers', 'Phone Numbers',
      'Physical Address Postcode', 'Active' for horse/owner status).
    - Owner lookup and creation now strictly uses 'Owner Business Name', 'Owner First Name', 'Owner Last Name'.
    - Location lookup and creation uses 'Physical Address Suburb/Neighborhood'.
    - Horse creation uses 'Animal Name', 'Animal Code', 'Microchip Num', 'Reg Num', 'Band Tag'.
    - Added parsing for date/time strings in 'Animal Record Created At' and 'Animal Record Last Modified At'.
- v1.0.2 (2025-07-15):
    - **BUG FIX**: Added `encoding='latin-1'` (or 'cp1252') to `pd.read_csv()` call
      to resolve `UnicodeDecodeError: 'utf-8' codec can't decode bytes`.
      This addresses character encoding mismatches in the CSV file.
- v1.0.1 (2025-07-03):
    - **Refinement**: Updated column mappings based on user's clarification for:
        - 'Animal Record Created At' -> horses.created_date
        - 'Animal Record Last Modified' -> horses.modified_date
        - 'Animal Code' -> horses.account_number
    - Added filtering to only import records where 'Species' is "Equine (Horse)".
    - Removed owner account number lookup for owners as per user's request.
    - Adjusted owner lookup to prioritize exact name match.
- v1.0.0 (2025-07-03):
    - Initial creation of the data import script.
    - Designed to read a combined CSV file (hypothetical structure).
    - Implements sequential import: Locations -> Owners -> Horses.
    - Includes logic for looking up existing entities and creating new ones.
    - Uses controllers for database interactions and leverages existing validation.
"""

import logging
import os
import sys
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Setup project path to allow imports from config and models
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import EDMS modules
try:
    from config.database_config import (
        DatabaseManager,
        set_db_manager_instance,
        db_manager,
    )
    from config.app_config import AppConfig
    from config.config_manager import config_manager
    from controllers.location_controller import LocationController
    from controllers.owner_controller import OwnerController
    from controllers.horse_controller import HorseController
    import models
except ImportError as e:
    print(f"Error importing EDMS modules: {e}")
    print(
        "Please ensure you are running this script from the project root directory or that sys.path is correctly configured."
    )
    sys.exit(1)

# --- Logging Setup ---
log_file_path = os.path.join(AppConfig.LOG_DIR, "data_import.log")
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

# --- Controllers ---
location_controller = LocationController()
owner_controller = OwnerController()
horse_controller = HorseController()

# --- Helper Functions for Data Transformation ---


def _parse_date(date_str: Any) -> Optional[date]:
    if pd.isna(date_str) or not str(date_str).strip():
        return None
    # Try common date formats
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str), fmt).date()
        except ValueError:
            continue
    logger.warning(f"Could not parse date: '{date_str}'. Returning None.")
    return None


def _parse_numeric(num_str: Any) -> Optional[Decimal]:
    if pd.isna(num_str) or not str(num_str).strip():
        return None
    try:
        return Decimal(str(num_str).replace("$", "").replace(",", "")).quantize(
            Decimal("0.01")
        )
    except InvalidOperation:
        logger.warning(f"Could not parse numeric value: '{num_str}'. Returning None.")
        return None


def _parse_boolean(bool_str: Any) -> bool:
    if pd.isna(bool_str) or not str(bool_str).strip():
        return False
    return str(bool_str).strip().lower() in ("true", "yes", "1")


def _get_or_create_location(
    session: Session, loc_data: Dict[str, Any], created_by: str
) -> Optional[models.Location]:
    loc_name = loc_data.get("Physical Address Suburb/Neighborhood")
    if not loc_name or not str(loc_name).strip():
        logger.warning(
            f"Skipping location due to missing 'Physical Address Suburb/Neighborhood': {loc_data}"
        )
        return None
    loc_name = str(loc_name).strip()

    existing_loc = (
        session.query(models.Location)
        .filter(models.Location.location_name.collate("NOCASE") == loc_name)
        .first()
    )
    if existing_loc:
        return existing_loc

    new_loc_data = {
        "location_name": loc_name,
        "contact_person": loc_data.get(
            "Location Contact Person"
        ),  # Not in CSV, will be None
        "address_line1": loc_data.get("Physical Address Street 1"),
        "address_line2": loc_data.get("Physical Address Street 2"),
        "city": loc_data.get("Physical Address City"),
        "state_code": loc_data.get("Physical Address State"),
        "zip_code": loc_data.get("Physical Address Postcode"),
        "country_code": loc_data.get("Physical Address Country") or "USA",
        "phone": loc_data.get("Location Phone"),  # Not in CSV, will be None
        "email": loc_data.get("Location Email"),  # Not in CSV, will be None
        "is_active": _parse_boolean(
            loc_data.get("Location Active", True)
        ),  # Not in CSV, will be True by default
    }

    is_valid, errors = location_controller.validate_location_data(
        new_loc_data, is_new=True, session=session
    )
    if not is_valid:
        logger.error(
            f"Validation failed for new location '{loc_name}': {'; '.join(errors)}"
        )
        return None

    success, msg, created_loc = location_controller.create_location(
        new_loc_data, created_by, session=session
    )
    if success:
        logger.info(
            f"Created new location: '{loc_name}' (ID: {created_loc.location_id})"
        )
        return created_loc
    else:
        logger.error(f"Failed to create location '{loc_name}': {msg}")
        return None


def _get_or_create_owner(
    session: Session, owner_data: Dict[str, Any], created_by: str
) -> Optional[models.Owner]:
    farm_name = owner_data.get("Owner Business Name")
    first_name = owner_data.get("Owner First Name")
    last_name = owner_data.get("Owner Last Name")

    # Prioritize unique identification: Farm Name, then First/Last Name
    query = session.query(models.Owner)

    # Try to find by exact match of all three if available
    if (
        farm_name
        and first_name
        and last_name
        and str(farm_name).strip()
        and str(first_name).strip()
        and str(last_name).strip()
    ):
        existing_owner = query.filter(
            models.Owner.farm_name.collate("NOCASE") == str(farm_name).strip(),
            models.Owner.first_name.collate("NOCASE") == str(first_name).strip(),
            models.Owner.last_name.collate("NOCASE") == str(last_name).strip(),
        ).first()
        if existing_owner:
            return existing_owner
    # Try by farm name only if it's present
    elif farm_name and str(farm_name).strip():
        existing_owner = query.filter(
            models.Owner.farm_name.collate("NOCASE") == str(farm_name).strip()
        ).first()
        if existing_owner:
            return existing_owner
    # Try by first and last name only if both are present
    elif (
        first_name and last_name and str(first_name).strip() and str(last_name).strip()
    ):
        existing_owner = query.filter(
            models.Owner.first_name.collate("NOCASE") == str(first_name).strip(),
            models.Owner.last_name.collate("NOCASE") == str(last_name).strip(),
        ).first()
        if existing_owner:
            return existing_owner

    if not (farm_name or (first_name and last_name)):
        logger.warning(
            f"Skipping owner due to insufficient identification (no farm name or first/last name): {owner_data}"
        )
        return None

    new_owner_data = {
        "account_number": None,  # As per user request, leaving out owner account numbers for now
        "farm_name": str(farm_name).strip() if farm_name else None,
        "first_name": str(first_name).strip() if first_name else None,
        "last_name": str(last_name).strip() if last_name else None,
        "address_line1": owner_data.get("Physical Address Street 1"),
        "address_line2": owner_data.get("Physical Address Street 2"),
        "city": owner_data.get("Physical Address City"),
        "state_code": owner_data.get("Physical Address State"),
        "zip_code": owner_data.get("Physical Address Postcode"),
        "phone": owner_data.get("Phone Numbers"),
        "mobile_phone": owner_data.get("Mobile Numbers"),
        "email": owner_data.get("Email Addresses"),
        "is_active": _parse_boolean(owner_data.get("Active", True)),
        "balance": _parse_numeric(
            owner_data.get("Owner Balance", "0.00")
        ),  # Not in CSV, will be 0.00
        "credit_limit": _parse_numeric(
            owner_data.get("Owner Credit Limit")
        ),  # Not in CSV, will be None
        "billing_terms": owner_data.get(
            "Owner Billing Terms"
        ),  # Not in CSV, will be None
        "notes": owner_data.get("Owner Notes"),  # Not in CSV, will be None
    }

    is_valid, errors = owner_controller.validate_owner_data(
        new_owner_data, is_new=True, session=session
    )
    if not is_valid:
        logger.error(
            f"Validation failed for new owner '{farm_name or last_name}': {'; '.join(errors)}"
        )
        return None

    success, msg, created_owner = owner_controller.create_master_owner(
        new_owner_data, created_by, session=session
    )
    if success:
        logger.info(
            f"Created new owner: '{farm_name or last_name}' (ID: {created_owner.owner_id})"
        )
        return created_owner
    else:
        logger.error(f"Failed to create owner '{farm_name or last_name}': {msg}")
        return None


def import_customer_data(csv_file_path: str, created_by_user: str = "import_script"):
    logger.info(f"Starting data import from: {csv_file_path}")

    _db_manager = DatabaseManager(AppConfig, config_manager)

    try:
        _db_manager.initialize_database()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}. Aborting import.")
        return

    with _db_manager.get_session() as session:
        try:
            df = pd.read_csv(csv_file_path, encoding="latin-1")
            df = df.where(pd.notna(df), None)

            # --- Collect unique data for Locations and Owners first ---

            # Locations
            # Corrected column names based on screenshots. Removed assumed 'Location Contact Person', 'Location Phone', 'Location Email', 'Location Active'
            unique_locations_df = df[
                [
                    "Physical Address Suburb/Neighborhood",
                    "Physical Address Street 1",
                    "Physical Address Street 2",
                    "Physical Address City",
                    "Physical Address State",
                    "Physical Address Postcode",
                    "Physical Address Country",
                ]
            ].drop_duplicates(subset=["Physical Address Suburb/Neighborhood"])

            locations_map = {}
            for index, row_data in unique_locations_df.iterrows():
                loc_obj = _get_or_create_location(
                    session, row_data.to_dict(), created_by_user
                )
                if loc_obj:
                    locations_map[loc_obj.location_name.lower()] = loc_obj
            logger.info(f"Finished processing {len(locations_map)} unique locations.")

            # Owners
            # Corrected column names based on screenshots. Removed assumed 'Owner Balance', 'Owner Credit Limit', 'Owner Billing Terms', 'Owner Notes'
            unique_owners_df = df[
                [
                    "Owner Business Name",
                    "Owner First Name",
                    "Owner Last Name",
                    "Physical Address Street 1",
                    "Physical Address Street 2",
                    "Physical Address City",
                    "Physical Address State",
                    "Physical Address Postcode",
                    "Phone Numbers",
                    "Mobile Numbers",
                    "Email Addresses",
                    "Active",
                ]
            ].drop_duplicates(
                subset=["Owner Business Name", "Owner First Name", "Owner Last Name"]
            )

            owners_map = {}
            for index, row_data in unique_owners_df.iterrows():
                owner_obj = _get_or_create_owner(
                    session, row_data.to_dict(), created_by_user
                )
                if owner_obj:
                    key = (
                        (
                            str(owner_obj.farm_name).lower()
                            if owner_obj.farm_name
                            else ""
                        )
                        + (
                            str(owner_obj.first_name).lower()
                            if owner_obj.first_name
                            else ""
                        )
                        + (
                            str(owner_obj.last_name).lower()
                            if owner_obj.last_name
                            else ""
                        )
                    )
                    owners_map[key] = owner_obj
            logger.info(f"Finished processing {len(owners_map)} unique owners.")

            # --- Process Horses Last ---
            logger.info("Processing horses and their associations...")
            processed_horses_count = 0
            processed_horse_owners_count = 0
            processed_horse_locations_count = 0

            for index, row in df.iterrows():
                species = row.get("Species")
                if species and str(species).strip().lower() not in (
                    "equine (horse)",
                    "horse",
                ):
                    logger.info(
                        f"Skipping row {index+2} ('{row.get('Animal Name')}') due to non-Equine species: '{species}'."
                    )
                    continue

                horse_name = row.get("Animal Name")
                if not horse_name or not str(horse_name).strip():
                    logger.warning(
                        f"Skipping row {index+2} due to missing 'Animal Name'."
                    )
                    continue
                horse_name = str(horse_name).strip()

                existing_horse_query = session.query(models.Horse).filter(
                    models.Horse.horse_name.collate("NOCASE") == horse_name
                )

                animal_code = row.get("Animal Code")
                if animal_code and str(animal_code).strip():
                    existing_horse_query = existing_horse_query.filter(
                        models.Horse.account_number.collate("NOCASE")
                        == str(animal_code).strip()
                    )

                microchip_num = row.get("Microchip Num")
                if microchip_num and str(microchip_num).strip():
                    existing_horse_query = existing_horse_query.filter(
                        models.Horse.chip_number.collate("NOCASE")
                        == str(microchip_num).strip()
                    )

                tattoo_num = row.get("Tattoo Number")
                if tattoo_num and str(tattoo_num).strip():
                    existing_horse_query = existing_horse_query.filter(
                        models.Horse.tattoo_number.collate("NOCASE")
                        == str(tattoo_num).strip()
                    )

                existing_horse = existing_horse_query.first()

                horse_obj = None
                if existing_horse:
                    logger.info(
                        f"Horse '{horse_name}' (ID: {existing_horse.horse_id}) already exists. Using existing record."
                    )
                    horse_obj = existing_horse
                else:
                    horse_data = {
                        "horse_name": horse_name,
                        "account_number": (
                            str(animal_code).strip() if animal_code else None
                        ),
                        "breed": row.get("Breed"),
                        "color": row.get("AnimalColor"),
                        "sex": row.get("Sex"),
                        "date_of_birth": _parse_date(row.get("Date of Birth")),
                        "height_hands": _parse_numeric(row.get("Height Hands")),
                        "chip_number": microchip_num,
                        "tattoo_number": tattoo_num,
                        "reg_number": row.get("Reg Num"),
                        "brand": row.get("Brand"),  # Not in CSV, will be None
                        "band_tag": row.get("Band Tag"),
                        "description": row.get("Animal Notes"),
                        "is_active": _parse_boolean(row.get("Active", True)),
                        "date_deceased": _parse_date(
                            row.get("Date Deceased")
                        ),  # Not in CSV, will be None
                        "coggins_date": _parse_date(
                            row.get("Coggins Date")
                        ),  # Not in CSV, will be None
                        "created_date": _parse_date(row.get("Animal Record Created At"))
                        or datetime.utcnow(),
                        "modified_date": _parse_date(
                            row.get("Animal Record Last Modified At")
                        )
                        or datetime.utcnow(),
                        "created_by": created_by_user,
                        "modified_by": created_by_user,
                    }
                    success, msg, created_horse = horse_controller.create_horse(
                        horse_data, created_by_user, session=session
                    )
                    if success:
                        horse_obj = created_horse
                        processed_horses_count += 1
                    else:
                        logger.error(
                            f"Failed to create horse '{horse_name}': {msg}. Skipping associations for this horse."
                        )
                        continue

                owner_business_name = row.get("Owner Business Name")
                owner_first_name = row.get("Owner First Name")
                owner_last_name = row.get("Owner Last Name")

                linked_owner_obj = None
                if owner_business_name or (owner_first_name and owner_last_name):
                    key = (
                        (
                            str(owner_business_name).lower()
                            if owner_business_name
                            else ""
                        )
                        + (str(owner_first_name).lower() if owner_first_name else "")
                        + (str(owner_last_name).lower() if owner_last_name else "")
                    )
                    linked_owner_obj = owners_map.get(key)

                if linked_owner_obj:
                    existing_assoc = (
                        session.query(models.HorseOwner)
                        .filter_by(
                            horse_id=horse_obj.horse_id,
                            owner_id=linked_owner_obj.owner_id,
                        )
                        .first()
                    )
                    if not existing_assoc:
                        percentage = _parse_numeric(
                            row.get("Percentage Ownership", "100.00")
                        )
                        success, msg = horse_controller.add_owner_to_horse(
                            horse_obj.horse_id,
                            linked_owner_obj.owner_id,
                            float(percentage),
                            created_by_user,
                            session=session,
                        )
                        if success:
                            logger.info(
                                f"Linked horse '{horse_obj.horse_name}' to owner '{linked_owner_obj.farm_name or linked_owner_obj.last_name}' with {percentage}%."
                            )
                            processed_horse_owners_count += 1
                        else:
                            logger.error(
                                f"Failed to link horse '{horse_obj.horse_name}' to owner '{linked_owner_obj.farm_name or linked_owner_obj.last_name}': {msg}"
                            )
                    else:
                        logger.info(
                            f"Horse '{horse_obj.horse_name}' already linked to owner '{linked_owner_obj.farm_name or linked_owner_obj.last_name}'. Skipping owner link."
                        )
                else:
                    logger.warning(
                        f"Owner for horse '{horse_obj.horse_name}' (Business: {owner_business_name}, Name: {owner_first_name} {owner_last_name}) not found in map. Skipping owner link."
                    )

                loc_name = row.get("Physical Address Suburb/Neighborhood")
                if loc_name and str(loc_name).strip():
                    linked_loc_obj = locations_map.get(str(loc_name).strip().lower())
                    if linked_loc_obj:
                        if horse_obj.current_location_id != linked_loc_obj.location_id:
                            success, msg = horse_controller.assign_horse_to_location(
                                horse_obj.horse_id,
                                linked_loc_obj.location_id,
                                None,
                                created_by_user,
                                session=session,
                            )
                            if success:
                                logger.info(
                                    f"Assigned horse '{horse_obj.horse_name}' to location '{linked_loc_obj.location_name}'."
                                )
                                processed_horse_locations_count += 1
                            else:
                                logger.error(
                                    f"Failed to assign horse '{horse_obj.horse_name}' to location '{linked_loc_obj.location_name}': {msg}"
                                )
                        else:
                            logger.info(
                                f"Horse '{horse_obj.horse_name}' already at location '{linked_loc_obj.location_name}'. Skipping location update."
                            )
                    else:
                        logger.warning(
                            f"Location '{loc_name}' for horse '{horse_obj.horse_name}' not found in map. Skipping location assignment."
                        )

                session.commit()

            logger.info(f"Import Summary:")
            logger.info(f"  New Horses Created: {processed_horses_count}")
            logger.info(f"  Horse-Owner Links Created: {processed_horse_owners_count}")
            logger.info(
                f"  Horse-Location Assignments Made/Updated: {processed_horse_locations_count}"
            )
            logger.info("Data import completed successfully.")

        except FileNotFoundError:
            logger.critical(f"Error: CSV file not found at '{csv_file_path}'.")
        except pd.errors.EmptyDataError:
            logger.critical(f"Error: CSV file '{csv_file_path}' is empty.")
        except pd.errors.ParserError as e:
            logger.critical(f"Error parsing CSV file '{csv_file_path}': {e}")
        except SQLAlchemyError as e:
            logger.critical(f"Database error during import: {e}", exc_info=True)
            session.rollback()
        except Exception as e:
            logger.critical(
                f"An unexpected error occurred during import: {e}", exc_info=True
            )
        finally:
            _db_manager.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_customer_data.py <path_to_csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    import_customer_data(csv_file)
