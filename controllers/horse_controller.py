# controllers/horse_controller.py

"""
EDSI Veterinary Management System - Horse Controller
Version: 1.2.3
Purpose: Business logic for horse management operations including CRUD, validation,
         data processing, and horse-owner associations.
         Allows 0% ownership percentage.
Last Updated: May 17, 2025
Author: Claude Assistant

Changelog:
- v1.2.3 (2025-05-17):
    - Modified percentage validation in `add_owner_to_horse` and
      `update_horse_owner_percentage` to allow 0% ownership.
- v1.2.2 (2025-05-15): Removed non-existent audit fields from HorseOwner instantiation.
- v1.2.1 (2025-05-14): Corrected querying by owner_name in get_horse_owners.
- v1.2.0 (2025-05-13): Added methods for horse-owner associations.
- v1.1.1 (2025-05-13): Implemented eager loading for Horse.location.
- v1.1.0 (2025-05-13): Enhanced search_horses for flexible status filtering.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from config.database_config import db_manager
from models import Horse, Owner, HorseOwner, Location


class HorseController:
    """Controller for horse management operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_horse(
        self, horse_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Horse]]:
        session = db_manager.get_session()
        try:
            if not horse_data.get("horse_name", "").strip():
                return False, "Horse name is required", None

            horse = Horse(
                horse_name=horse_data["horse_name"].strip(),
                account_number=horse_data.get("account_number", "").strip(),
                breed=horse_data.get("breed", "").strip(),
                color=horse_data.get("color", "").strip(),
                sex=horse_data.get("sex"),
                date_of_birth=self._parse_date(horse_data.get("date_of_birth")),
                registration_number=horse_data.get("registration_number", "").strip(),
                microchip_id=horse_data.get("microchip_id", "").strip(),
                tattoo=horse_data.get("tattoo", "").strip(),
                brand=horse_data.get("brand", "").strip(),
                band_tag_number=horse_data.get("band_tag_number", "").strip(),
                current_location_id=horse_data.get("current_location_id"),
                created_by=current_user,
                modified_by=current_user,
                is_active=True,
            )
            session.add(horse)
            session.commit()
            session.refresh(horse)
            self.logger.info(
                f"Created new horse: {horse.horse_name} (ID: {horse.horse_id})"
            )
            return True, "Horse created successfully", horse
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
            if not horse_data.get("horse_name", "").strip():
                return False, "Horse name is required"

            horse.horse_name = horse_data["horse_name"].strip()
            horse.account_number = horse_data.get("account_number", "").strip()
            horse.breed = horse_data.get("breed", "").strip()
            horse.color = horse_data.get("color", "").strip()
            horse.sex = horse_data.get("sex")
            horse.date_of_birth = self._parse_date(horse_data.get("date_of_birth"))
            horse.registration_number = horse_data.get(
                "registration_number", ""
            ).strip()
            horse.microchip_id = horse_data.get("microchip_id", "").strip()
            horse.tattoo = horse_data.get("tattoo", "").strip()
            horse.brand = horse_data.get("brand", "").strip()
            horse.band_tag_number = horse_data.get("band_tag_number", "").strip()
            horse.current_location_id = horse_data.get("current_location_id")
            horse.modified_by = current_user
            session.commit()
            self.logger.info(
                f"Updated horse: {horse.horse_name} (ID: {horse.horse_id})"
            )
            return True, "Horse updated successfully"
        except Exception as e:
            session.rollback()
            error_msg = f"Error updating horse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
        finally:
            session.close()

    def get_horse_by_id(self, horse_id: int) -> Optional[Horse]:
        session = db_manager.get_session()
        try:
            horse = (
                session.query(Horse)
                .options(
                    joinedload(Horse.location),
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
            query = session.query(Horse).options(joinedload(Horse.location))

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
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Horse.horse_name.ilike(search_pattern),
                        Horse.account_number.ilike(search_pattern),
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

    def validate_horse_data(self, horse_data: dict) -> Tuple[bool, List[str]]:
        errors = []
        if not horse_data.get("horse_name", "").strip():
            errors.append("Horse name is required")
        if len(horse_data.get("horse_name", "")) > 100:
            errors.append("Horse name cannot exceed 100 characters")
        if horse_data.get("date_of_birth"):
            try:
                birth_date = self._parse_date(horse_data["date_of_birth"])
                if birth_date and birth_date > date.today():
                    errors.append("Date of birth cannot be in the future")
            except Exception:
                errors.append("Invalid date of birth format or value")
        return len(errors) == 0, errors

    def _parse_date(self, date_value) -> Optional[date]:
        if not date_value:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, str):
            formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
        self.logger.warning(
            f"Could not parse date: {date_value} of type {type(date_value)}"
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
            "delete_horse called, redirecting to deactivate_horse. Ensure UI reflects deactivation."
        )
        return self.deactivate_horse(horse_id, current_user)

    def get_horse_owners(self, horse_id: int) -> List[Dict[str, any]]:
        session = db_manager.get_session()
        try:
            horse_owners_data = (
                session.query(
                    Owner.owner_id,
                    Owner.first_name,
                    Owner.last_name,
                    Owner.farm_name,
                    Owner.account_number,
                    HorseOwner.ownership_percentage,
                )
                .join(HorseOwner, Owner.owner_id == HorseOwner.owner_id)
                .filter(HorseOwner.horse_id == horse_id)
                .order_by(Owner.farm_name, Owner.last_name, Owner.first_name)
                .all()
            )
            result = []
            for (
                owner_id,
                first_name,
                last_name,
                farm_name,
                acc_num,
                percentage,
            ) in horse_owners_data:
                name_parts = []
                if first_name:
                    name_parts.append(first_name)
                if last_name:
                    name_parts.append(last_name)
                individual_name = " ".join(name_parts)
                owner_name_for_display = ""
                if farm_name:
                    owner_name_for_display = farm_name
                    if individual_name:
                        owner_name_for_display += f" ({individual_name})"
                elif individual_name:
                    owner_name_for_display = individual_name
                else:
                    owner_name_for_display = "Unnamed Owner"
                display_name_with_account = (
                    f"{owner_name_for_display} [{acc_num}]"
                    if acc_num
                    else owner_name_for_display
                )
                result.append(
                    {
                        "owner_id": owner_id,
                        "owner_name": owner_name_for_display,
                        "account_number": acc_num,
                        "display_name": display_name_with_account,
                        "percentage": percentage,
                    }
                )
            return result
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

            # Allow 0% ownership
            if not (0 <= percentage <= 100):  # MODIFIED: was (0 < percentage <= 100)
                return (
                    False,
                    "Ownership percentage must be between 0 and 100 (inclusive).",  # MODIFIED: Message
                )

            current_total_percentage = (
                session.query(func.sum(HorseOwner.ownership_percentage))
                .filter(HorseOwner.horse_id == horse_id)
                .scalar()
                or 0
            )
            if current_total_percentage + percentage > 100.001:
                precise_total = sum(
                    ho.ownership_percentage
                    for ho in session.query(HorseOwner.ownership_percentage)
                    .filter(HorseOwner.horse_id == horse_id)
                    .all()
                )
                if precise_total + percentage > 100.001:
                    return (
                        False,
                        f"Adding {percentage:.2f}% would exceed 100% total ownership for this horse (current total: {precise_total:.2f}%).",
                    )

            new_horse_owner = HorseOwner(
                horse_id=horse_id,
                owner_id=owner_id,
                ownership_percentage=percentage,
                start_date=date.today(),
            )
            session.add(new_horse_owner)
            session.commit()
            self.logger.info(
                f"Added owner ID {owner_id} to horse ID {horse_id} with {percentage:.2f}% ownership by {current_user}."
            )
            return True, "Owner added to horse successfully."
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

            # Allow 0% ownership
            if not (
                0 <= new_percentage <= 100
            ):  # MODIFIED: was (0 < new_percentage <= 100)
                return (
                    False,
                    "Ownership percentage must be between 0 and 100 (inclusive).",  # MODIFIED: Message
                )

            other_owners_percentage = (
                session.query(func.sum(HorseOwner.ownership_percentage))
                .filter(
                    HorseOwner.horse_id == horse_id, HorseOwner.owner_id != owner_id
                )
                .scalar()
                or 0
            )
            if other_owners_percentage + new_percentage > 100.001:
                precise_other_total = sum(
                    ho.ownership_percentage
                    for ho in session.query(HorseOwner.ownership_percentage)
                    .filter(
                        HorseOwner.horse_id == horse_id, HorseOwner.owner_id != owner_id
                    )
                    .all()
                )
                if precise_other_total + new_percentage > 100.001:
                    return (
                        False,
                        f"Updating to {new_percentage:.2f}% would exceed 100% total ownership (other owners: {precise_other_total:.2f}%).",
                    )

            assoc.ownership_percentage = new_percentage
            session.commit()
            self.logger.info(
                f"Updated ownership for horse ID {horse_id}, owner ID {owner_id} to {new_percentage:.2f}% by {current_user}."
            )
            return True, "Ownership percentage updated successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating ownership percentage: {e}", exc_info=True
            )
            return False, f"Failed to update percentage: {e}"
        finally:
            session.close()

    def remove_owner_from_horse(
        self, horse_id: int, owner_id: int, current_user: str
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
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error removing owner from horse: {e}", exc_info=True)
            return False, f"Failed to remove owner: {e}"
        finally:
            session.close()
