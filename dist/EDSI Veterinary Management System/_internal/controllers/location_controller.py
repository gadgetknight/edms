# controllers/location_controller.py
"""
EDSI Veterinary Management System - Location Controller
Version: 1.2.0
Purpose: Handles business logic for locations.
         - Added delete_location method with referential integrity check.
         - Modified get_all_locations to accept a string-based status_filter.
Last Updated: June 5, 2025
Author: Gemini

Changelog:
- v1.2.0 (2025-06-05):
    - Added `delete_location` method, which checks for linked horses in
      HorseLocation before allowing deletion.
    - Modified `get_all_locations` to accept a string `status_filter` ('active',
      'inactive', or 'all') instead of a boolean for consistency.
- v1.1.7 (2025-06-05):
    - Reverted `update_location` to return a tuple of two values (bool, str).
"""
import logging
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc as sqlalchemy_exc

from config.database_config import db_manager
from models import Location, StateProvince, HorseLocation


class LocationController:
    """Controller for location management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_locations(self, status_filter: str = "all") -> List[Location]:
        session = db_manager().get_session()  # Corrected line
        try:
            query = session.query(Location).options(joinedload(Location.state))
            if status_filter == "active":
                query = query.filter(Location.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(Location.is_active == False)
            locations = query.order_by(Location.location_name).all()
            return locations
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all locations: {e}", exc_info=True)
            return []
        finally:
            db_manager().close()  # Corrected line

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        session = db_manager().get_session()  # Corrected line
        try:
            return (
                session.query(Location)
                .options(joinedload(Location.state))
                .filter(Location.location_id == location_id)
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching location by ID {location_id}: {e}", exc_info=True
            )
            return None
        finally:
            db_manager().close()  # Corrected line

    def validate_location_data(
        self,
        location_data: dict,
        is_new: bool = True,
        location_id_to_check_for_unique: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        name = location_data.get("location_name", "").strip()

        if not name:
            errors.append("Location Name is required.")
        elif len(name) > 100:
            errors.append("Location Name cannot exceed 100 characters.")
        else:
            session = db_manager().get_session()  # Corrected line
            try:
                query = session.query(Location.location_id).filter(
                    Location.location_name.collate("NOCASE") == name
                )
                if not is_new and location_id_to_check_for_unique is not None:
                    query = query.filter(
                        Location.location_id != location_id_to_check_for_unique
                    )
                if query.first():
                    errors.append(f"Location Name '{name}' already exists.")
            finally:
                db_manager().close()  # Corrected line
        return not errors, errors

    def create_location(
        self, location_data: dict, current_user_id: str
    ) -> Tuple[bool, str, Optional[Location]]:
        is_valid, errors = self.validate_location_data(location_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager().get_session()  # Corrected line
        try:

            def process_string(value: Any) -> Optional[str]:
                return value.strip() if isinstance(value, str) else None

            new_location = Location(
                location_name=location_data.get("location_name", "").strip(),
                address_line1=process_string(location_data.get("address_line1")),
                address_line2=process_string(location_data.get("address_line2")),
                city=process_string(location_data.get("city")),
                state_code=process_string(location_data.get("state_code")),
                zip_code=process_string(location_data.get("zip_code")),
                phone=process_string(location_data.get("phone")),
                contact_person=process_string(location_data.get("contact_person")),
                email=process_string(location_data.get("email")),
                is_active=location_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_location)
            session.commit()
            session.refresh(new_location)
            self.logger.info(
                f"Location '{new_location.location_name}' created by {current_user_id}."
            )
            return True, "Location created successfully.", new_location
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            self.logger.error(f"Error creating location: {e.orig}", exc_info=True)
            return False, f"Database integrity error: {e.orig}", None
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating location: {e}", exc_info=True)
            return False, f"Failed to create location: {e}", None
        finally:
            db_manager().close()  # Corrected line

    def update_location(
        self, location_id: int, location_data: dict, current_user_id: str
    ) -> Tuple[bool, str]:
        is_valid, errors = self.validate_location_data(
            location_data, is_new=False, location_id_to_check_for_unique=location_id
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors)

        session = db_manager().get_session()  # Corrected line
        try:
            location = (
                session.query(Location)
                .filter(Location.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found."

            for key, value in location_data.items():
                if hasattr(location, key):
                    processed_value = value.strip() if isinstance(value, str) else value
                    setattr(location, key, processed_value)

            location.modified_by = current_user_id
            session.commit()
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location_id}) updated by {current_user_id}."
            )
            return True, "Location updated successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating location ID {location_id}: {e}", exc_info=True
            )
            return False, f"Failed to update location: {e}"
        finally:
            db_manager().close()  # Corrected line

    def toggle_location_active_status(
        self, location_id: int, current_user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            location = (
                session.query(Location)
                .filter(Location.location_id == location_id)
                .first()
            )
            if not location:
                return False, f"Location with ID {location_id} not found."

            location.is_active = not location.is_active
            location.modified_by = current_user_id

            session.commit()

            new_status = "activated" if location.is_active else "deactivated"
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location_id}) status changed to {new_status} by {current_user_id}."
            )
            return (
                True,
                f"Location '{location.location_name}' has been successfully {new_status}.",
            )

        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error toggling status for location ID {location_id}: {e}",
                exc_info=True,
            )
            return False, "A database error occurred while toggling location status."
        finally:
            db_manager().close()  # Corrected line

    def delete_location(
        self, location_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        session = db_manager().get_session()  # Corrected line
        try:
            linked_horses_count = (
                session.query(HorseLocation)
                .filter(HorseLocation.location_id == location_id)
                .count()
            )

            if linked_horses_count > 0:
                message = f"Cannot delete location. It is currently or was previously assigned to {linked_horses_count} horse(s)."
                self.logger.warning(message)
                return False, message

            location_to_delete = (
                session.query(Location)
                .filter(Location.location_id == location_id)
                .first()
            )

            if not location_to_delete:
                return False, "Location not found."

            location_name = location_to_delete.location_name
            session.delete(location_to_delete)
            session.commit()
            self.logger.info(
                f"Location '{location_name}' (ID: {location_id}) deleted by {current_user_id}."
            )
            return True, f"Location '{location_name}' was deleted."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error deleting location ID {location_id}: {e}", exc_info=True
            )
            return False, f"A database error occurred: {e}"
        finally:
            db_manager().close()  # Corrected line
