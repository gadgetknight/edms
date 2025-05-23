# controllers/horse_controller.py
"""
EDSI Veterinary Management System - Horse Controller
Version: 1.2.7
Purpose: Handles business logic related to horses.
         - Changed 'updated_by' to 'modified_by' to match BaseModel.
         - Removed temporary pop for coggins_date.
Last Updated: May 22, 2025
Author: Gemini

Changelog:
- v1.2.7 (2025-05-22):
    - Updated `create_horse` and `update_horse` to use `modified_by` instead of `updated_by`
      to align with the user's current `BaseModel` definition.
    - Removed temporary `data.pop('coggins_date', None)` as `coggins_date` is now a valid model field.
- v1.2.6 (2025-05-21 - User Uploaded version):
    - Initial version with methods for CRUD, search, linking owners, locations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import joinedload, selectinload, aliased
from sqlalchemy.exc import SQLAlchemyError

from config.database_config import Session
from models import Horse, Owner, HorseOwner, Species, Location, HorseLocation

# Make sure all necessary models are imported if used directly for queries.


class HorseController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_species(self) -> List[Species]:
        """Retrieves all species from the database."""
        session = Session()
        try:
            species_list = session.query(Species).order_by(Species.name).all()
            self.logger.info(f"Retrieved {len(species_list)} species records.")
            return species_list
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving species: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_all_locations(self) -> List[Location]:
        """Retrieves all locations from the database."""
        session = Session()
        try:
            locations = session.query(Location).order_by(Location.location_name).all()
            self.logger.info(f"Retrieved {len(locations)} location records.")
            return locations
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving locations: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def validate_horse_data(
        self,
        data: dict,
        is_new: bool = True,
        horse_id_to_check_for_unique: Optional[int] = None,
    ) -> tuple[bool, list]:
        errors = []
        required_fields = ["horse_name"]  # Add other required fields here as necessary

        for field in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                errors.append(f"{field.replace('_', ' ').capitalize()} is required.")

        # Example: Validate date of birth is not in the future
        if data.get("date_of_birth"):
            try:
                dob = data["date_of_birth"]
                if isinstance(dob, str):
                    dob = date.fromisoformat(dob)
                if dob > date.today():
                    errors.append("Date of Birth cannot be in the future.")
            except ValueError:
                errors.append("Invalid Date of Birth format. Please use YYYY-MM-DD.")

        # Example: Validate Coggins date is not in the future
        if data.get("coggins_date"):
            try:
                coggins_dt = data["coggins_date"]
                if isinstance(coggins_dt, str):
                    coggins_dt = date.fromisoformat(coggins_dt)
                if (
                    coggins_dt > date.today()
                ):  # Basic check, could be more complex (e.g., not older than X years)
                    errors.append("Coggins Date cannot be in the future.")
            except ValueError:
                errors.append("Invalid Coggins Date format. Please use YYYY-MM-DD.")

        # Check uniqueness for chip number if provided
        chip_number = data.get("chip_number")
        if chip_number and str(chip_number).strip():
            session = Session()
            query = session.query(Horse).filter(Horse.chip_number == chip_number)
            if not is_new and horse_id_to_check_for_unique:
                query = query.filter(Horse.horse_id != horse_id_to_check_for_unique)
            if query.first():
                errors.append(f"Chip number '{chip_number}' already exists.")
            session.close()

        # Check uniqueness for tattoo number if provided
        tattoo_number = data.get("tattoo_number")
        if tattoo_number and str(tattoo_number).strip():
            session = Session()
            query = session.query(Horse).filter(Horse.tattoo_number == tattoo_number)
            if not is_new and horse_id_to_check_for_unique:
                query = query.filter(Horse.horse_id != horse_id_to_check_for_unique)
            if query.first():
                errors.append(f"Tattoo number '{tattoo_number}' already exists.")
            session.close()

        return not errors, errors

    def create_horse(
        self, data: dict, created_by_user: str
    ) -> tuple[bool, str, Optional[Horse]]:
        session = Session()
        try:
            # Set audit fields using names from BaseModel
            data["created_by"] = created_by_user
            data["modified_by"] = created_by_user  # CHANGED from updated_by
            # created_date and modified_date are handled by BaseModel defaults/onupdate

            self.logger.debug(
                f"HorseController.create_horse - Data RECEIVED/FINAL: {data}"
            )
            self.logger.debug(
                f"HorseController.create_horse - Data KEYS: {list(data.keys())}"
            )

            # coggins_date should now be a valid field if added to Horse model and present in data
            new_horse = Horse(**data)
            session.add(new_horse)
            session.commit()
            session.refresh(new_horse)
            self.logger.info(
                f"Horse '{new_horse.horse_name}' (ID: {new_horse.horse_id}) created successfully by {created_by_user}."
            )
            return (
                True,
                f"Horse '{new_horse.horse_name}' created successfully.",
                new_horse,
            )
        except TypeError as te:
            self.logger.error(
                f"TypeError during Horse creation: {te} - Data was: {data}",
                exc_info=True,
            )
            session.rollback()
            return (
                False,
                f"Failed to create horse due to invalid data field: {te}",
                None,
            )
        except SQLAlchemyError as e:  # More general SQLAlchemy error
            self.logger.error(
                f"SQLAlchemyError creating horse: {e} - Data was: {data}", exc_info=True
            )
            session.rollback()
            return (
                False,
                f"A database error occurred while creating the horse: {e}",
                None,
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error creating horse: {e} - Data was: {data}",
                exc_info=True,
            )
            session.rollback()
            return (
                False,
                f"An unexpected error occurred while creating the horse: {e}",
                None,
            )
        finally:
            session.close()

    def update_horse(
        self, horse_id: int, data: dict, modified_by_user: str
    ) -> tuple[bool, str]:
        session = Session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, "Horse not found."

            # Set audit fields using names from BaseModel
            data["modified_by"] = modified_by_user  # CHANGED from updated_by
            # modified_date handled by BaseModel's onupdate

            self.logger.debug(f"HorseController.update_horse - Data for update: {data}")

            for key, value in data.items():
                if hasattr(horse, key):  # Make sure the attribute exists on the model
                    setattr(horse, key, value)
                else:
                    self.logger.warning(
                        f"HorseController.update_horse - Attempted to set unknown attribute '{key}' on Horse model."
                    )

            session.commit()
            self.logger.info(
                f"Horse ID {horse_id} updated successfully by {modified_by_user}."
            )
            return True, "Horse details updated successfully."
        except SQLAlchemyError as e:
            self.logger.error(
                f"SQLAlchemyError updating horse ID {horse_id}: {e}", exc_info=True
            )
            session.rollback()
            return False, f"A database error occurred while updating the horse: {e}"
        except Exception as e:
            self.logger.error(
                f"Unexpected error updating horse ID {horse_id}: {e}", exc_info=True
            )
            session.rollback()
            return False, f"An unexpected error occurred while updating the horse: {e}"
        finally:
            session.close()

    # ... (rest of HorseController methods like get_horse_by_id, search_horses, etc. remain mostly unchanged
    # unless they directly interact with 'updated_by' which should now be 'modified_by' if fetched/displayed)

    def get_horse_by_id(self, horse_id: int) -> Optional[Horse]:
        session = Session()
        try:
            horse = (
                session.query(Horse)
                .options(
                    selectinload(Horse.owner_associations).selectinload(
                        HorseOwner.owner
                    ),
                    selectinload(Horse.location_history).selectinload(
                        HorseLocation.location
                    ),
                    joinedload(Horse.species),  # Eager load species
                    joinedload(Horse.location),  # Eager load current location object
                )
                .filter(Horse.horse_id == horse_id)
                .first()
            )
            if horse:
                self.logger.info(f"Retrieved horse ID {horse_id}: {horse.horse_name}")
            else:
                self.logger.warning(f"Horse ID {horse_id} not found.")
            return horse
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving horse ID {horse_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def search_horses(
        self, search_term: str = "", status: str = "active"
    ) -> List[Horse]:
        session = Session()
        try:
            query = session.query(Horse).options(
                selectinload(Horse.owner_associations).selectinload(HorseOwner.owner),
                joinedload(Horse.species),
                joinedload(
                    Horse.location
                ),  # Eager load current location for list display
            )

            if search_term:
                search_term_like = f"%{search_term}%"
                # Search in name, account number, chip number, tattoo
                # Also search by owner name - requires a join
                OwnerAlias = aliased(Owner)
                query = query.outerjoin(Horse.owner_associations).outerjoin(
                    OwnerAlias,
                    Horse.owner_associations.c.owner_id == OwnerAlias.owner_id,
                )

                query = query.filter(
                    or_(
                        Horse.horse_name.ilike(search_term_like),
                        Horse.account_number.ilike(search_term_like),
                        Horse.chip_number.ilike(search_term_like),
                        Horse.tattoo_number.ilike(search_term_like),
                        OwnerAlias.owner_name.ilike(
                            search_term_like
                        ),  # Search by owner name
                    )
                ).distinct(
                    Horse.horse_id
                )  # Distinct because of join with owners

            if status == "active":
                query = query.filter(Horse.is_active == True)
            elif status == "inactive":
                query = query.filter(Horse.is_active == False)
            # If status is "all", no active/inactive filter is applied.

            horses = query.order_by(Horse.horse_name).all()
            self.logger.info(
                f"Search for horses (term: '{search_term}', status: {status}) found {len(horses)} results."
            )
            return horses
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching horses: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def deactivate_horse(
        self, horse_id: int, modified_by_user: str
    ) -> tuple[bool, str]:
        return self._toggle_horse_status(horse_id, False, modified_by_user)

    def activate_horse(self, horse_id: int, modified_by_user: str) -> tuple[bool, str]:
        return self._toggle_horse_status(horse_id, True, modified_by_user)

    def _toggle_horse_status(
        self, horse_id: int, is_active: bool, modified_by_user: str
    ) -> tuple[bool, str]:
        session = Session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, "Horse not found."

            horse.is_active = is_active
            horse.modified_by = modified_by_user  # Use modified_by
            # horse.date_updated = datetime.utcnow() # BaseModel handles modified_date

            if (
                not is_active and not horse.date_deceased
            ):  # If deactivating and no deceased date, prompt or set default?
                # For now, just deactivating. UI might handle setting deceased date.
                pass

            session.commit()
            status_text = "activated" if is_active else "deactivated"
            self.logger.info(
                f"Horse ID {horse_id} {status_text} by {modified_by_user}."
            )
            return True, f"Horse {status_text} successfully."
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error toggling horse status for ID {horse_id}: {e}", exc_info=True
            )
            session.rollback()
            return False, f"Database error: Could not change horse status."
        finally:
            session.close()

    # --- Owner Association Methods ---
    def get_horse_owners(self, horse_id: int) -> List[Dict[str, Any]]:
        session = Session()
        try:
            associations = (
                session.query(HorseOwner)
                .filter(HorseOwner.horse_id == horse_id)
                .options(joinedload(HorseOwner.owner))
                .all()
            )
            owner_details = []
            for assoc in associations:
                if assoc.owner:
                    owner_details.append(
                        {
                            "owner_id": assoc.owner.owner_id,
                            "owner_name": assoc.owner.owner_name,
                            "percentage_ownership": assoc.percentage_ownership,
                            "phone_number": assoc.owner.phone_number_primary,  # Assuming owner model has this
                        }
                    )
            return owner_details
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owners for horse ID {horse_id}: {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def add_owner_to_horse(
        self,
        horse_id: int,
        owner_id: int,
        percentage: Optional[float],
        modified_by_user: str,
    ) -> tuple[bool, str]:
        session = Session()
        try:
            # Check if association already exists
            existing_assoc = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if existing_assoc:
                return False, "Owner is already associated with this horse."

            new_association = HorseOwner(
                horse_id=horse_id, owner_id=owner_id, percentage_ownership=percentage
            )
            # If HorseOwner inherits BaseModel, set created_by/modified_by here.
            # For now, assuming HorseOwner is a simple link table (does not inherit BaseModel).
            # new_association.created_by = modified_by_user
            # new_association.modified_by = modified_by_user

            session.add(new_association)

            # Update modified_by on the Horse record itself
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                horse.modified_by = modified_by_user

            session.commit()
            self.logger.info(
                f"Owner ID {owner_id} added to horse ID {horse_id} by {modified_by_user}."
            )
            return True, "Owner successfully added to horse."
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding owner to horse: {e}", exc_info=True)
            session.rollback()
            return False, "Database error: Could not add owner."
        finally:
            session.close()

    def update_horse_owner_percentage(
        self, horse_id: int, owner_id: int, percentage: float, modified_by_user: str
    ) -> tuple[bool, str]:
        session = Session()
        try:
            association = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not association:
                return False, "Owner association not found."

            association.percentage_ownership = percentage
            # if hasattr(association, 'modified_by'): association.modified_by = modified_by_user

            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                horse.modified_by = modified_by_user

            session.commit()
            self.logger.info(
                f"Ownership percentage updated for horse ID {horse_id}, owner ID {owner_id} by {modified_by_user}."
            )
            return True, "Ownership percentage updated."
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error updating ownership percentage: {e}", exc_info=True
            )
            session.rollback()
            return False, "Database error: Could not update ownership."
        finally:
            session.close()

    def remove_owner_from_horse(
        self, horse_id: int, owner_id: int, modified_by_user: str
    ) -> tuple[bool, str]:
        session = Session()
        try:
            association = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not association:
                return False, "Owner association not found."

            session.delete(association)

            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                horse.modified_by = modified_by_user

            session.commit()
            self.logger.info(
                f"Owner ID {owner_id} removed from horse ID {horse_id} by {modified_by_user}."
            )
            return True, "Owner removed from horse successfully."
        except SQLAlchemyError as e:
            self.logger.error(f"Error removing owner from horse: {e}", exc_info=True)
            session.rollback()
            return False, "Database error: Could not remove owner."
        finally:
            session.close()

    # --- Location Assignment Methods ---
    def assign_horse_to_location(
        self,
        horse_id: int,
        location_id: int,
        notes: Optional[str],
        modified_by_user: str,
    ) -> tuple[bool, str]:
        session = Session()
        try:
            # End date for any previous current location record for this horse
            today = date.today()
            previous_assignments = (
                session.query(HorseLocation)
                .filter(
                    HorseLocation.horse_id == horse_id,
                    HorseLocation.date_departed == None,
                )
                .all()
            )
            for prev_assign in previous_assignments:
                if (
                    prev_assign.location_id != location_id
                ):  # Only end if it's a different location
                    prev_assign.date_departed = today
                    # prev_assign.modified_by = modified_by_user # If HorseLocation uses BaseModel

            # Check if this exact assignment (horse to this location, still current) already exists
            # to prevent duplicate active assignments to the SAME location.
            # This logic might need refinement if re-assigning to the same location "refreshes" the arrival date.
            # For now, if already at this location and current, we might just update notes or do nothing.
            # The current logic might create a new record even if horse is re-assigned to same location.
            # This depends on desired behavior (e.g., new arrival date vs. continuous stay).

            new_assignment = HorseLocation(
                horse_id=horse_id,
                location_id=location_id,
                date_arrived=today,
                notes=notes,
                created_by=modified_by_user,  # From BaseModel
                modified_by=modified_by_user,  # From BaseModel
            )
            session.add(new_assignment)

            # Update the Horse's current_location_id
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                horse.current_location_id = location_id
                horse.modified_by = modified_by_user  # From BaseModel

            session.commit()
            self.logger.info(
                f"Horse ID {horse_id} assigned to location ID {location_id} by {modified_by_user}."
            )
            return True, "Horse location assigned successfully."
        except SQLAlchemyError as e:
            self.logger.error(f"Error assigning horse to location: {e}", exc_info=True)
            session.rollback()
            return False, "Database error: Could not assign location."
        finally:
            session.close()

    def remove_horse_from_location(
        self,
        horse_id: int,
        location_id: Optional[int] = None,
        modified_by_user: str = "system",
    ) -> tuple[bool, str]:
        """
        Sets date_departed for the current assignment of the horse.
        If location_id is provided, only removes from that specific current assignment.
        If location_id is None, removes from any current assignment.
        """
        session = Session()
        try:
            query = session.query(HorseLocation).filter(
                HorseLocation.horse_id == horse_id, HorseLocation.date_departed == None
            )

            if (
                location_id is not None
            ):  # Only end assignment for specific location if provided
                query = query.filter(HorseLocation.location_id == location_id)

            current_assignment = query.first()

            if not current_assignment:
                return (
                    False,
                    "No current location assignment found for this horse (or not at the specified location).",
                )

            current_assignment.date_departed = date.today()
            # current_assignment.modified_by = modified_by_user # If HorseLocation uses BaseModel

            # Clear current_location_id on Horse if this was its current location
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse and horse.current_location_id == current_assignment.location_id:
                horse.current_location_id = None
                horse.modified_by = modified_by_user  # From BaseModel

            session.commit()
            self.logger.info(
                f"Horse ID {horse_id} removed from location (assignment ID: {current_assignment.id}) by {modified_by_user}."
            )
            return True, "Horse removed from location (assignment ended)."
        except SQLAlchemyError as e:
            self.logger.error(f"Error removing horse from location: {e}", exc_info=True)
            session.rollback()
            return False, "Database error: Could not remove horse from location."
        finally:
            session.close()
