# controllers/horse_controller.py
"""
EDSI Veterinary Management System - Horse Controller
Version: 1.5.0
Purpose: Handles business logic related to horses.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v1.5.0 (2025-06-10):
    - Fixed a critical bug in `create_horse` that caused a crash when saving a
      new horse without a location. The creation of a HorseLocation history
      record is now conditional on a location_id being provided.
- v1.4.0 (2025-06-09):
    - Refactored to improve separation of concerns by removing the redundant
      `get_all_locations` method. This functionality correctly belongs to the
      LocationController.
- v1.3.0 (2025-06-09):
    - Bug Fix: In `get_horse_by_id`, added `selectinload(Horse.owner_associations)`
      to the query to prevent DetachedInstanceError during invoice generation.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from sqlalchemy import (
    select,
    update,
    delete,
    and_,
    or_,
    func as sql_func,
)
from sqlalchemy.orm import joinedload, selectinload, aliased
from sqlalchemy.exc import SQLAlchemyError

from config.database_config import db_manager
from models import Horse, Owner, HorseOwner, Location, HorseLocation


class HorseController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_horse_data(
        self,
        data: dict,
        is_new: bool = True,
        horse_id_to_check_for_unique: Optional[int] = None,
    ) -> tuple[bool, list]:
        errors = []
        required_fields = ["horse_name"]

        for field in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                errors.append(f"{field.replace('_', ' ').capitalize()} is required.")

        if data.get("date_of_birth"):
            try:
                dob = data["date_of_birth"]
                if not isinstance(dob, date):
                    errors.append("Date of Birth was not a valid date object.")
                elif dob > date.today():
                    errors.append("Date of Birth cannot be in the future.")
            except Exception:
                errors.append("Invalid Date of Birth provided.")

        if data.get("coggins_date"):
            try:
                coggins_dt = data["coggins_date"]
                if not isinstance(coggins_dt, date):
                    errors.append("Coggins Date was not a valid date object.")
                elif coggins_dt > date.today():
                    errors.append("Coggins Date cannot be in the future.")
            except Exception:
                errors.append("Invalid Coggins Date provided.")

        chip_number = data.get("chip_number")
        if chip_number and str(chip_number).strip():
            session = db_manager().get_session()  # Corrected line
            try:
                query = session.query(Horse).filter(Horse.chip_number == chip_number)
                if not is_new and horse_id_to_check_for_unique:
                    query = query.filter(Horse.horse_id != horse_id_to_check_for_unique)
                if query.first():
                    errors.append(f"Chip number '{chip_number}' already exists.")
            finally:
                db_manager().close()  # Corrected line

        tattoo_number = data.get("tattoo_number")
        if tattoo_number and str(tattoo_number).strip():
            session = db_manager().get_session()  # Corrected line
            try:
                query = session.query(Horse).filter(
                    Horse.tattoo_number == tattoo_number
                )
                if not is_new and horse_id_to_check_for_unique:
                    query = query.filter(Horse.horse_id != horse_id_to_check_for_unique)
                if query.first():
                    errors.append(f"Tattoo number '{tattoo_number}' already exists.")
            finally:
                db_manager().close()  # Corrected line
        return not errors, errors

    def create_horse(
        self, data: dict, created_by_user: str
    ) -> tuple[bool, str, Optional[Horse]]:
        session = db_manager().get_session()  # Corrected line
        try:
            data["created_by"] = created_by_user
            data["modified_by"] = created_by_user

            horse_columns = {col.name for col in Horse.__table__.columns}
            filtered_data = {k: v for k, v in data.items() if k in horse_columns}

            for key in data:
                if key not in horse_columns and key not in ["current_location_id"]:
                    self.logger.warning(
                        f"HorseController.create_horse - Attribute '{key}' present in data but not in Horse model columns. It will be ignored."
                    )

            new_horse = Horse(**filtered_data)
            session.add(new_horse)

            # MODIFIED: Only create a location assignment if a location is provided.
            location_id = data.get("current_location_id")
            if location_id is not None:
                new_horse.current_location_id = location_id

                new_assignment = HorseLocation(
                    horse=new_horse,
                    location_id=location_id,
                    date_arrived=date.today(),
                    is_current_location=True,
                    created_by=created_by_user,
                    modified_by=created_by_user,
                )
                session.add(new_assignment)

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
        except SQLAlchemyError as e:
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
            db_manager().close()  # Corrected line

    def update_horse(
        self, horse_id: int, data: dict, modified_by_user: str
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, "Horse not found."

            data["modified_by"] = modified_by_user
            horse_columns = {col.name for col in Horse.__table__.columns}

            for key, value in data.items():
                if key == "current_location_id":
                    if horse.current_location_id != value:
                        horse.current_location_id = value
                elif key in horse_columns:
                    setattr(horse, key, value)
                elif hasattr(horse, key):
                    self.logger.info(
                        f"Setting attribute '{key}' which is not a direct column but exists on Horse model."
                    )
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
            db_manager().close()  # Corrected line

    def get_horse_by_id(self, horse_id: int) -> Optional[Horse]:
        session = db_manager().get_session()  # Corrected line
        try:
            horse = (
                session.query(Horse)
                .options(
                    selectinload(Horse.owner_associations).joinedload(HorseOwner.owner),
                    selectinload(Horse.owners),
                    joinedload(Horse.location),
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
            db_manager().close()  # Corrected line

    def search_horses(
        self,
        search_term: str = "",
        status: str = "active",
        owner_name_search: Optional[str] = None,
    ) -> List[Horse]:
        session = db_manager().get_session()  # Corrected line
        try:
            query = session.query(Horse).options(
                selectinload(Horse.owners),
                joinedload(Horse.location),
            )

            if search_term:
                search_term_like = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Horse.horse_name.ilike(search_term_like),
                        Horse.account_number.ilike(search_term_like),
                        Horse.chip_number.ilike(search_term_like),
                        Horse.tattoo_number.ilike(search_term_like),
                    )
                )

            if owner_name_search:
                OwnerAlias = aliased(Owner)
                owner_search_like = f"%{owner_name_search}%"
                query = query.join(Horse.owners.of_type(OwnerAlias)).filter(
                    or_(
                        OwnerAlias.farm_name.ilike(owner_search_like),
                        OwnerAlias.first_name.ilike(owner_search_like),
                        OwnerAlias.last_name.ilike(owner_search_like),
                    )
                )
                query = query.distinct()

            if status == "active":
                query = query.filter(Horse.is_active == True)
            elif status == "inactive":
                query = query.filter(Horse.is_active == False)

            horses = query.order_by(Horse.horse_name).all()
            self.logger.info(
                f"Search for horses (term: '{search_term}', owner: '{owner_name_search}', status: {status}) found {len(horses)} results."
            )
            return horses
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching horses: {e}", exc_info=True)
            session.rollback()
            return []
        finally:
            db_manager().close()  # Corrected line

    def deactivate_horse(
        self, horse_id: int, modified_by_user: str
    ) -> tuple[bool, str]:
        return self._toggle_horse_status(horse_id, False, modified_by_user)

    def activate_horse(self, horse_id: int, modified_by_user: str) -> tuple[bool, str]:
        return self._toggle_horse_status(horse_id, True, modified_by_user)

    def _toggle_horse_status(
        self, horse_id: int, is_active: bool, modified_by_user: str
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, "Horse not found."
            horse.is_active = is_active
            horse.modified_by = modified_by_user

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
            return False, "Database error: Could not change horse status."
        finally:
            db_manager().close()  # Corrected line

    def get_horse_owners(self, horse_id: int) -> List[Dict[str, Any]]:
        session = db_manager().get_session()  # Corrected line
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
                    owner_name_parts = []
                    if assoc.owner.farm_name:
                        owner_name_parts.append(assoc.owner.farm_name)

                    person_name_parts = []
                    if assoc.owner.first_name:
                        person_name_parts.append(assoc.owner.first_name)
                    if assoc.owner.last_name:
                        person_name_parts.append(assoc.owner.last_name)
                    person_name_str = " ".join(person_name_parts).strip()

                    if person_name_str:
                        owner_name_parts.append(f"({person_name_str})")

                    display_name = " ".join(owner_name_parts).strip()
                    if not display_name:
                        display_name = f"Owner ID: {assoc.owner.owner_id}"

                    owner_details.append(
                        {
                            "owner_id": assoc.owner.owner_id,
                            "owner_name": display_name,
                            "percentage_ownership": assoc.percentage_ownership,
                            "phone_number": assoc.owner.phone,
                        }
                    )
            return owner_details
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owners for horse ID {horse_id}: {e}", exc_info=True
            )
            session.rollback()
            return []
        finally:
            db_manager().close()  # Corrected line

    def add_owner_to_horse(
        self,
        horse_id: int,
        owner_id: int,
        percentage: Optional[float],
        modified_by_user: str,
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
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
            session.add(new_association)

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
            db_manager().close()  # Corrected line

    def update_horse_owner_percentage(
        self, horse_id: int, owner_id: int, percentage: float, modified_by_user: str
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            association = (
                session.query(HorseOwner)
                .filter_by(horse_id=horse_id, owner_id=owner_id)
                .first()
            )
            if not association:
                return False, "Owner association not found."
            association.percentage_ownership = percentage

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
            db_manager().close()  # Corrected line

    def remove_owner_from_horse(
        self, horse_id: int, owner_id: int, modified_by_user: str
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
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
            db_manager().close()  # Corrected line

    def assign_horse_to_location(
        self,
        horse_id: int,
        location_id: int,
        notes: Optional[str],
        modified_by_user: str,
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            today = date.today()
            previous_assignments = (
                session.query(HorseLocation)
                .filter(
                    HorseLocation.horse_id == horse_id,
                    HorseLocation.is_current_location == True,
                )
                .all()
            )
            for prev_assign in previous_assignments:
                if prev_assign.location_id != location_id:
                    prev_assign.date_departed = today
                    prev_assign.is_current_location = False
                    prev_assign.modified_by = modified_by_user

            new_assignment = HorseLocation(
                horse_id=horse_id,
                location_id=location_id,
                date_arrived=today,
                notes=notes,
                is_current_location=True,
                created_by=modified_by_user,
                modified_by=modified_by_user,
            )
            session.add(new_assignment)

            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                horse.current_location_id = location_id
                horse.modified_by = modified_by_user
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
            db_manager().close()  # Corrected line

    def remove_horse_from_location(
        self,
        horse_id: int,
        location_id: Optional[int] = None,
        modified_by_user: str = "system",
    ) -> tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            query = session.query(HorseLocation).filter(
                HorseLocation.horse_id == horse_id,
                HorseLocation.is_current_location == True,
            )
            if location_id is not None:
                query = query.filter(HorseLocation.location_id == location_id)

            current_assignment = query.first()
            if not current_assignment:
                return (
                    False,
                    "No current location assignment found for this horse (or not at the specified location if one was provided).",
                )

            current_assignment.date_departed = date.today()
            current_assignment.is_current_location = False
            current_assignment.modified_by = modified_by_user

            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse and horse.current_location_id == current_assignment.location_id:
                horse.current_location_id = None
                horse.modified_by = modified_by_user
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
            db_manager().close()  # Corrected line
