# controllers/horse_controller.py

"""
EDSI Veterinary Management System - Horse Controller
Version: 1.2.1
Purpose: Business logic for horse management operations including CRUD, validation,
         data processing, and horse-owner associations.
         Corrected owner_name querying in get_horse_owners.
Last Updated: May 14, 2025
Author: Claude Assistant

Changelog:
- v1.2.1 (2025-05-14): Corrected querying by owner_name in get_horse_owners.
  - Changed `Owner.owner_name` to query individual name fields
    (`first_name`, `last_name`, `farm_name`) for sorting and display construction.
- v1.2.0 (2025-05-13): Added methods for horse-owner associations.
- v1.1.1 (2025-05-13): Implemented eager loading for Horse.location.
- v1.1.0 (2025-05-13): Enhanced search_horses for flexible status filtering.
- v1.0.1 (2025-05-12): Removed species support for horses-only system
- v1.0.0 (2025-05-12): Initial implementation
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
        """
        Create a new horse record.
        Args:
            horse_data: Dictionary containing horse information.
            current_user: Current logged-in user ID.
        Returns:
            Tuple of (success, message, horse_object).
        """
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
        """
        Update an existing horse record.
        Args:
            horse_id: ID of horse to update.
            horse_data: Dictionary containing updated horse information.
            current_user: Current logged-in user ID.
        Returns:
            Tuple of (success, message).
        """
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
            horse.modified_date = datetime.utcnow()
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
        """Get horse by ID, including its location and owners."""
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
        """
        Search horses by name or account number, with status filtering.
        Location data is eager-loaded.
        Args:
            search_term (str): Term to match against horse name or account number.
            status (str): Horse status to filter by ('active', 'inactive', 'all').
                          Defaults to 'active'.
        Returns:
            List of matching horses.
        """
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
        """Get list of all active locations."""
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
        """Validate horse data."""
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
        """Parse date from various formats or QDate object."""
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
        """Deactivate a horse (mark as inactive)."""
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found."
            if not horse.is_active:
                return False, f"Horse '{horse.horse_name}' is already inactive."
            horse.is_active = False
            horse.modified_by = current_user
            horse.modified_date = datetime.utcnow()
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
        """Activate a horse (mark as active)."""
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found."
            if horse.is_active:
                return False, f"Horse '{horse.horse_name}' is already active."
            horse.is_active = True
            horse.modified_by = current_user
            horse.modified_date = datetime.utcnow()
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
        """This method now calls deactivate_horse for clarity."""
        self.logger.warning(
            "delete_horse called, redirecting to deactivate_horse. Ensure UI reflects deactivation."
        )
        return self.deactivate_horse(horse_id, current_user)

    # --- Horse-Owner Association Methods ---

    def get_horse_owners(self, horse_id: int) -> List[Dict[str, any]]:
        """
        Get a list of owners associated with a specific horse, including ownership percentage.
        Returns a list of dictionaries for easier display.
        """
        session = db_manager.get_session()
        try:
            # --- MODIFIED: Query individual name fields and sort by them ---
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
                .order_by(
                    Owner.farm_name, Owner.last_name, Owner.first_name
                )  # Corrected order
                .all()
            )
            # --- END MODIFICATION ---

            result = []
            for (
                owner_id,
                first_name,
                last_name,
                farm_name,
                acc_num,
                percentage,
            ) in horse_owners_data:
                # Construct display name from parts
                name_parts = []
                if first_name:
                    name_parts.append(first_name)
                if last_name:
                    name_parts.append(last_name)
                individual_name = " ".join(name_parts)

                owner_name_for_display = ""  # This will be the full constructed name
                if farm_name:
                    owner_name_for_display = farm_name
                    if individual_name:
                        owner_name_for_display += f" ({individual_name})"
                elif individual_name:
                    owner_name_for_display = individual_name
                else:
                    owner_name_for_display = "Unnamed Owner"  # Fallback

                display_name_with_account = (
                    f"{owner_name_for_display} [{acc_num}]"
                    if acc_num
                    else owner_name_for_display
                )

                result.append(
                    {
                        "owner_id": owner_id,
                        "owner_name": owner_name_for_display,  # Store the constructed full name
                        "account_number": acc_num,
                        "display_name": display_name_with_account,  # For UI list
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
        """Adds an existing owner to a horse with a specified ownership percentage."""
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
                # Use hybrid property owner.owner_name for display if available
                owner_display = (
                    owner.owner_name
                    if hasattr(owner, "owner_name")
                    else f"ID {owner.owner_id}"
                )
                return (
                    False,
                    f"Owner '{owner_display}' is already associated with horse '{horse.horse_name}'.",
                )

            if not (0 < percentage <= 100):
                return (
                    False,
                    "Ownership percentage must be greater than 0 and less than or equal to 100.",
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
                        f"Adding {percentage}% would exceed 100% total ownership for this horse (current total: {precise_total:.2f}%).",
                    )

            new_horse_owner = HorseOwner(
                horse_id=horse_id,
                owner_id=owner_id,
                ownership_percentage=percentage,
                created_by=current_user,
                modified_by=current_user,
                created_date=datetime.utcnow(),
                modified_date=datetime.utcnow(),
            )
            session.add(new_horse_owner)
            session.commit()
            self.logger.info(
                f"Added owner ID {owner_id} to horse ID {horse_id} with {percentage}% ownership by {current_user}."
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
        """Updates the ownership percentage for a specific horse-owner association."""
        session = db_manager.get_session()
        try:
            assoc = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not assoc:
                return False, "Ownership association not found."

            if not (0 < new_percentage <= 100):
                return (
                    False,
                    "Ownership percentage must be greater than 0 and less than or equal to 100.",
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
                        f"Updating to {new_percentage}% would exceed 100% total ownership (other owners: {precise_other_total:.2f}%).",
                    )

            assoc.ownership_percentage = new_percentage
            assoc.modified_by = current_user
            assoc.modified_date = datetime.utcnow()
            session.commit()
            self.logger.info(
                f"Updated ownership for horse ID {horse_id}, owner ID {owner_id} to {new_percentage}% by {current_user}."
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
        """Removes an owner's association from a horse."""
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
