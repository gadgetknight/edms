# controllers/horse_controller.py

"""
EDSI Veterinary Management System - Horse Controller
Version: 1.2.5
Purpose: Business logic for horse management operations including CRUD, validation,
         data processing, and horse-owner associations.
         Added logging for current_location_id during save/update.
Last Updated: May 21, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.2.5 (2025-05-21):
    - Added logging in `create_horse` and `update_horse` to show the
      `current_location_id` being processed.
- v1.2.4 (2025-05-19):
    - Modified `create_horse` and `update_horse` to convert empty strings to None
      for unique, nullable string fields (microchip_id, registration_number,
      tattoo, brand, band_tag_number) directly before attribute assignment
      to prevent UNIQUE constraint errors with multiple blank entries.
    - Ensured specific IntegrityError check for UNIQUE constraint failures.
# ... (rest of previous changelog)
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import (
    or_,
    and_,
    func,
    exc as sqlalchemy_exc,
)

from config.database_config import db_manager
from models import (
    Horse,
    Owner,
    HorseOwner,
    Location,
    Species,
)


class HorseController:
    """Controller for horse management operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _sanitize_value(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped_value = value.strip()
        return None if not stripped_value else stripped_value

    def create_horse(
        self, horse_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Horse]]:
        session = db_manager.get_session()
        try:
            horse_name_val = self._sanitize_value(horse_data.get("horse_name"))
            if not horse_name_val:
                return False, "Horse name is required", None

            microchip_id_val = self._sanitize_value(horse_data.get("microchip_id"))
            registration_number_val = self._sanitize_value(
                horse_data.get("registration_number")
            )
            tattoo_val = self._sanitize_value(horse_data.get("tattoo"))
            brand_val = self._sanitize_value(horse_data.get("brand"))
            band_tag_number_val = self._sanitize_value(
                horse_data.get("band_tag_number")
            )
            account_number_val = self._sanitize_value(horse_data.get("account_number"))
            breed_val = self._sanitize_value(horse_data.get("breed"))
            color_val = self._sanitize_value(horse_data.get("color"))
            notes_val = horse_data.get("notes")

            current_location_id_val = horse_data.get("current_location_id")
            self.logger.info(
                f"HorseController.create_horse: Received current_location_id = {current_location_id_val}"
            )

            horse = Horse(
                horse_name=horse_name_val,
                account_number=account_number_val,
                breed=breed_val,
                color=color_val,
                sex=horse_data.get("sex"),
                date_of_birth=self._parse_date(horse_data.get("date_of_birth")),
                registration_number=registration_number_val,
                microchip_id=microchip_id_val,
                tattoo=tattoo_val,
                brand=brand_val,
                band_tag_number=band_tag_number_val,
                current_location_id=current_location_id_val,
                species_id=horse_data.get("species_id"),
                notes=notes_val,
                created_by=current_user,
                modified_by=current_user,
                is_active=horse_data.get("is_active", True),
            )
            session.add(horse)
            session.commit()
            session.refresh(horse)
            self.logger.info(
                f"Created new horse: {horse.horse_name} (ID: {horse.horse_id}) with location_id: {horse.current_location_id}"
            )
            return True, "Horse created successfully", horse
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating horse: {ie.orig}", exc_info=True
            )
            if hasattr(ie.orig, "pgcode") and ie.orig.pgcode == "23505":
                return (
                    False,
                    f"Database integrity error: A record with a similar unique value already exists. {ie.orig}",
                    None,
                )
            elif "UNIQUE constraint failed" in str(ie.orig):
                failed_field_info = str(ie.orig).split(":")[-1].strip()
                user_friendly_field_name = failed_field_info.split(".")[-1].replace(
                    "_", " "
                )
                return (
                    False,
                    f"Error: A horse with this {user_friendly_field_name} already exists.",
                    None,
                )
            return False, f"Database integrity error: {ie.orig}", None
        except Exception as e:
            session.rollback()
            error_msg = f"Error creating horse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg, None
        finally:
            session.close()

    def update_horse(
        self, horse_id: int, horse_data: dict, current_user: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found"

            horse_name_val = self._sanitize_value(horse_data.get("horse_name"))
            if not horse_name_val:
                return False, "Horse name is required"
            horse.horse_name = horse_name_val

            horse.account_number = self._sanitize_value(
                horse_data.get("account_number")
            )
            horse.breed = self._sanitize_value(horse_data.get("breed"))
            horse.color = self._sanitize_value(horse_data.get("color"))
            horse.sex = horse_data.get("sex")
            horse.date_of_birth = self._parse_date(horse_data.get("date_of_birth"))
            horse.registration_number = self._sanitize_value(
                horse_data.get("registration_number")
            )
            horse.microchip_id = self._sanitize_value(horse_data.get("microchip_id"))
            horse.tattoo = self._sanitize_value(horse_data.get("tattoo"))
            horse.brand = self._sanitize_value(horse_data.get("brand"))
            horse.band_tag_number = self._sanitize_value(
                horse_data.get("band_tag_number")
            )

            current_location_id_val = horse_data.get("current_location_id")
            self.logger.info(
                f"HorseController.update_horse ID {horse_id}: Received current_location_id = {current_location_id_val}"
            )
            horse.current_location_id = current_location_id_val

            horse.species_id = horse_data.get("species_id")
            horse.notes = horse_data.get("notes")
            horse.is_active = horse_data.get("is_active", horse.is_active)
            horse.modified_by = current_user

            session.commit()
            self.logger.info(
                f"Updated horse: {horse.horse_name} (ID: {horse.horse_id}) with new location_id: {horse.current_location_id}"
            )
            return True, "Horse updated successfully"
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating horse ID {horse_id}: {ie.orig}", exc_info=True
            )
            if hasattr(ie.orig, "pgcode") and ie.orig.pgcode == "23505":
                return (
                    False,
                    f"Database integrity error: A record with a similar unique value already exists. {ie.orig}",
                )
            elif "UNIQUE constraint failed" in str(ie.orig):
                failed_field_info = str(ie.orig).split(":")[-1].strip()
                user_friendly_field_name = failed_field_info.split(".")[-1].replace(
                    "_", " "
                )
                return (
                    False,
                    f"Error: Another horse with this {user_friendly_field_name} already exists.",
                )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            error_msg = f"Error updating horse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
        finally:
            session.close()

    # ... (rest of HorseController methods like get_horse_by_id, search_horses, etc. remain unchanged from v1.2.4) ...
    def get_horse_by_id(self, horse_id: int) -> Optional[Horse]:
        session = db_manager.get_session()
        try:
            horse = (
                session.query(Horse)
                .options(
                    joinedload(Horse.location),
                    joinedload(Horse.species),
                    joinedload(Horse.owners).joinedload(HorseOwner.owner),
                )
                .filter(Horse.horse_id == horse_id)
                .first()
            )
            return horse
        except Exception as e:
            self.logger.error(
                f"Error getting horse by ID {horse_id}: {str(e)}", exc_info=True
            )
            return None
        finally:
            session.close()

    def search_horses(
        self, search_term: str = "", status: str = "active"
    ) -> List[Horse]:
        session = db_manager.get_session()
        try:
            query = session.query(Horse).options(
                joinedload(Horse.location),
                joinedload(Horse.species),
            )

            if status == "active":
                query = query.filter(Horse.is_active == True)
            elif status == "inactive":
                query = query.filter(Horse.is_active == False)
            elif status != "all":
                self.logger.warning(
                    f"Invalid status '{status}' for search_horses. Defaulting to 'active'."
                )
                query = query.filter(Horse.is_active == True)

            if search_term:
                search_pattern = f"%{search_term.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Horse.horse_name).like(search_pattern),
                        func.lower(Horse.account_number).like(search_pattern),
                    )
                )
            horses = query.order_by(Horse.horse_name).all()
            return horses
        except Exception as e:
            self.logger.error(f"Error searching horses: {str(e)}", exc_info=True)
            return []
        finally:
            session.close()

    def get_locations_list(self) -> List[Location]:
        session = db_manager.get_session()
        try:
            return (
                session.query(Location)
                .filter(Location.is_active == True)
                .order_by(Location.location_name)
                .all()
            )
        except Exception as e:
            self.logger.error(f"Error getting locations list: {str(e)}", exc_info=True)
            return []
        finally:
            session.close()

    def validate_horse_data(
        self,
        horse_data: dict,
        is_new: bool = True,
        horse_id_to_check_for_unique: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        if not self._sanitize_value(horse_data.get("horse_name")):
            errors.append("Horse Name is required.")

        sanitized_name = self._sanitize_value(horse_data.get("horse_name"))
        if sanitized_name and len(sanitized_name) > 100:
            errors.append("Horse name cannot exceed 100 characters.")

        if horse_data.get("date_of_birth"):
            try:
                birth_date = self._parse_date(horse_data["date_of_birth"])
                if birth_date and birth_date > date.today():
                    errors.append("Date of birth cannot be in the future.")
            except Exception:
                errors.append("Invalid date of birth format or value.")

        unique_check_fields = {
            "microchip_id": "Microchip ID",
            "registration_number": "Registration Number",
            "tattoo": "Tattoo",
            "brand": "Brand",
            "band_tag_number": "Band/Tag Number",
        }
        session = db_manager.get_session()
        try:
            for field_key, display_name in unique_check_fields.items():
                value_from_form = horse_data.get(field_key)
                sanitized_value_for_check = self._sanitize_value(value_from_form)
                if sanitized_value_for_check:
                    query = session.query(Horse).filter(
                        getattr(Horse, field_key) == sanitized_value_for_check
                    )
                    if not is_new and horse_id_to_check_for_unique is not None:
                        query = query.filter(
                            Horse.horse_id != horse_id_to_check_for_unique
                        )
                    if query.first():
                        errors.append(
                            f"{display_name} '{sanitized_value_for_check}' already exists for another horse."
                        )
        except Exception as e:
            self.logger.error(
                f"Error during horse data validation (unique check): {e}", exc_info=True
            )
            errors.append("A database error occurred during validation.")
        finally:
            session.close()

        return len(errors) == 0, errors

    def _parse_date(self, date_value) -> Optional[date]:
        if not date_value:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            stripped_date_value = date_value.strip()
            if not stripped_date_value:
                return None
            formats_to_try = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]
            for fmt in formats_to_try:
                try:
                    return datetime.strptime(stripped_date_value, fmt).date()
                except ValueError:
                    continue
            self.logger.warning(
                f"Could not parse date string: '{stripped_date_value}' with known formats."
            )
            return None
        if hasattr(date_value, "toPython") and callable(date_value.toPython):
            try:
                py_date = date_value.toPython()
                if isinstance(py_date, date):
                    return py_date
            except Exception:
                pass

        self.logger.warning(
            f"Could not parse date input: {date_value} (type: {type(date_value)})"
        )
        return None

    def deactivate_horse(self, horse_id: int, current_user: str) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found."
            if not horse.is_active:
                return False, f"Horse '{horse.horse_name}' is already inactive."
            horse.is_active = False
            horse.modified_by = current_user
            session.commit()
            self.logger.info(
                f"Deactivated horse: {horse.horse_name} (ID: {horse.horse_id}) by user {current_user}."
            )
            return True, f"Horse '{horse.horse_name}' deactivated successfully."
        except Exception as e:
            session.rollback()
            error_msg = f"Error deactivating horse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
        finally:
            session.close()

    def activate_horse(self, horse_id: int, current_user: str) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found."
            if horse.is_active:
                return False, f"Horse '{horse.horse_name}' is already active."
            horse.is_active = True
            horse.modified_by = current_user
            session.commit()
            self.logger.info(
                f"Activated horse: {horse.horse_name} (ID: {horse.horse_id}) by user {current_user}."
            )
            return True, f"Horse '{horse.horse_name}' activated successfully."
        except Exception as e:
            session.rollback()
            error_msg = f"Error activating horse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
        finally:
            session.close()

    def delete_horse(self, horse_id: int, current_user: str) -> Tuple[bool, str]:
        self.logger.warning(
            f"delete_horse called for ID {horse_id} by {current_user}, redirecting to deactivate_horse."
        )
        return self.deactivate_horse(horse_id, current_user)

    def get_horse_owners(self, horse_id: int) -> List[Dict[str, any]]:
        session = db_manager.get_session()
        try:
            horse_owners_associations = (
                session.query(HorseOwner, Owner)
                .join(Owner, HorseOwner.owner_id == Owner.owner_id)
                .filter(HorseOwner.horse_id == horse_id)
                .order_by(Owner.farm_name, Owner.last_name, Owner.first_name)
                .all()
            )

            result_list = []
            for assoc, owner_obj in horse_owners_associations:
                name_parts = []
                if owner_obj.first_name:
                    name_parts.append(owner_obj.first_name)
                if owner_obj.last_name:
                    name_parts.append(owner_obj.last_name)
                individual_name_str = " ".join(name_parts)

                display_name_str = owner_obj.farm_name if owner_obj.farm_name else ""
                if owner_obj.farm_name and individual_name_str:
                    display_name_str += f" ({individual_name_str})"
                elif not owner_obj.farm_name and individual_name_str:
                    display_name_str = individual_name_str
                elif not display_name_str:  # Fallback if no names at all
                    display_name_str = f"Owner ID: {owner_obj.owner_id}"

                account_str = (
                    f" [Acct: {owner_obj.account_number}]"
                    if owner_obj.account_number
                    else ""
                )

                result_list.append(
                    {
                        "owner_id": owner_obj.owner_id,
                        "owner_name": display_name_str,
                        "account_number": owner_obj.account_number,
                        "display_name": display_name_str + account_str,
                        "percentage": assoc.ownership_percentage,
                        "is_primary": getattr(assoc, "is_primary_owner", False),
                    }
                )
            return result_list
        except Exception as e:
            self.logger.error(
                f"Error fetching owners for horse ID {horse_id}: {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def add_owner_to_horse(
        self, horse_id: int, owner_id: int, percentage: float, current_user: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found."
            owner = session.query(Owner).filter(Owner.owner_id == owner_id).first()
            if not owner:
                return False, f"Owner with ID {owner_id} not found."

            existing_assoc = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if existing_assoc:
                owner_display_parts = []
                if owner.first_name:
                    owner_display_parts.append(owner.first_name)
                if owner.last_name:
                    owner_display_parts.append(owner.last_name)
                owner_individual_display = " ".join(owner_display_parts)
                owner_display = owner.farm_name if owner.farm_name else ""
                if owner.farm_name and owner_individual_display:
                    owner_display += f" ({owner_individual_display})"
                elif not owner.farm_name and owner_individual_display:
                    owner_display = owner_individual_display
                elif not owner_display:
                    owner_display = f"ID {owner.owner_id}"
                return (
                    False,
                    f"Owner '{owner_display}' is already associated with horse '{horse.horse_name}'.",
                )

            if not (0 <= percentage <= 100):
                return (
                    False,
                    "Ownership percentage must be between 0 and 100 (inclusive).",
                )

            current_total_percentage = (
                session.query(func.sum(HorseOwner.ownership_percentage))
                .filter(HorseOwner.horse_id == horse_id)
                .scalar()
                or 0.0
            )
            if float(current_total_percentage) + float(percentage) > 100.001:
                precise_total = sum(
                    ho.ownership_percentage
                    for ho in session.query(HorseOwner.ownership_percentage)
                    .filter(HorseOwner.horse_id == horse_id)
                    .all()
                )
                if float(precise_total) + float(percentage) > 100.001:
                    return (
                        False,
                        f"Adding {percentage:.2f}% would exceed 100% total ownership (current total: {precise_total:.2f}%).",
                    )

            new_horse_owner = HorseOwner(
                horse_id=horse_id,
                owner_id=owner_id,
                ownership_percentage=percentage,
                start_date=date.today(),
                created_by=current_user,
                modified_by=current_user,
            )
            session.add(new_horse_owner)
            session.commit()
            self.logger.info(
                f"Added owner ID {owner_id} to horse ID {horse_id} with {percentage:.2f}% ownership by {current_user}."
            )
            return True, "Owner added to horse successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError adding owner to horse: {ie.orig}", exc_info=True
            )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding owner to horse: {e}", exc_info=True)
            return False, f"Failed to add owner: {e}"
        finally:
            session.close()

    def update_horse_owner_percentage(
        self, horse_id: int, owner_id: int, new_percentage: float, current_user: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            assoc = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not assoc:
                return False, "Ownership association not found."

            if not (0 <= new_percentage <= 100):
                return (
                    False,
                    "Ownership percentage must be between 0 and 100 (inclusive).",
                )

            other_owners_percentage = (
                session.query(func.sum(HorseOwner.ownership_percentage))
                .filter(
                    HorseOwner.horse_id == horse_id, HorseOwner.owner_id != owner_id
                )
                .scalar()
                or 0.0
            )
            if float(other_owners_percentage) + float(new_percentage) > 100.001:
                precise_other_total = sum(
                    ho.ownership_percentage
                    for ho in session.query(HorseOwner.ownership_percentage)
                    .filter(
                        HorseOwner.horse_id == horse_id, HorseOwner.owner_id != owner_id
                    )
                    .all()
                )
                if float(precise_other_total) + float(new_percentage) > 100.001:
                    return (
                        False,
                        f"Updating to {new_percentage:.2f}% would exceed 100% total ownership (other owners currently have {precise_other_total:.2f}%).",
                    )

            assoc.ownership_percentage = new_percentage
            if hasattr(assoc, "modified_by"):
                assoc.modified_by = current_user
            session.commit()
            self.logger.info(
                f"Updated ownership for horse ID {horse_id}, owner ID {owner_id} to {new_percentage:.2f}% by {current_user}."
            )
            return True, "Ownership percentage updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating ownership percentage: {ie.orig}",
                exc_info=True,
            )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating ownership percentage: {e}", exc_info=True
            )
            return False, f"Failed to update percentage: {e}"
        finally:
            session.close()

    def remove_owner_from_horse(
        self,
        horse_id: int,
        owner_id: int,
        current_user: str,
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            assoc = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not assoc:
                return False, "Ownership association not found to remove."

            session.delete(assoc)
            session.commit()
            self.logger.info(
                f"Removed owner ID {owner_id} from horse ID {horse_id} by {current_user}."
            )
            return True, "Owner removed from horse successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError removing owner from horse: {ie.orig}", exc_info=True
            )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error removing owner from horse: {e}", exc_info=True)
            return False, f"Failed to remove owner: {e}"
        finally:
            session.close()
