# controllers/location_controller.py
"""
EDSI Veterinary Management System - Location Controller
Version: 1.2.2
Purpose: Handles business logic for locations.
         Methods now accept an optional session parameter for transactional control.
Last Updated: July 15, 2025
Author: Gemini

Changelog:
- v1.2.2 (2025-07-15):
    - **BUG FIX**: Removed `_session.refresh(new_location)` from `create_location` method.
      The `refresh` call was happening before the object was committed in the external session,
      causing `InvalidRequestError: Instance is not persistent within this Session`.
      The calling script is now responsible for committing and refreshing.
- v1.2.1 (2025-07-15):
    - **Refactor**: Modified all database-interacting methods (`get_all_locations`,
      `get_location_by_id`, `validate_location_data`, `create_location`,
      `update_location`, `toggle_location_active_status`, `delete_location`)
      to accept an optional `session: Session` parameter.
    - If a session is provided, it is used; otherwise, a new session is obtained
      from `db_manager()`. This allows for external transaction management
      (e.g., from import scripts) and resolves `RuntimeError: DatabaseManager instance not set`.
    - `db_manager().close()` is now called only if the session was opened internally by the method.
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
import models  # Import models for direct use


class LocationController:
    """Controller for location management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_locations(
        self, status_filter: str = "all", session: Optional[Session] = None
    ) -> List[models.Location]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            query = _session.query(models.Location).options(
                joinedload(models.Location.state)
            )
            if status_filter == "active":
                query = query.filter(models.Location.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(models.Location.is_active == False)
            locations = query.order_by(models.Location.location_name).all()
            return locations
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all locations: {e}", exc_info=True)
            return []
        finally:
            if _close_session:
                _session.close()

    def get_location_by_id(
        self, location_id: int, session: Optional[Session] = None
    ) -> Optional[models.Location]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            return (
                _session.query(models.Location)
                .options(joinedload(models.Location.state))
                .filter(models.Location.location_id == location_id)
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching location by ID {location_id}: {e}", exc_info=True
            )
            return None
        finally:
            if _close_session:
                _session.close()

    def validate_location_data(
        self,
        location_data: dict,
        is_new: bool = True,
        location_id_to_check_for_unique: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        name = location_data.get("location_name", "").strip()

        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            if not name:
                errors.append("Location Name is required.")
            elif len(name) > 100:
                errors.append("Location Name cannot exceed 100 characters.")
            else:
                query = _session.query(models.Location.location_id).filter(
                    models.Location.location_name.collate("NOCASE") == name
                )
                if not is_new and location_id_to_check_for_unique is not None:
                    query = query.filter(
                        models.Location.location_id != location_id_to_check_for_unique
                    )
                if query.first():
                    errors.append(f"Location Name '{name}' already exists.")
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error validating location name uniqueness: {e}", exc_info=True
            )
            errors.append("Database error validating location name.")
        finally:
            if _close_session:
                _session.close()
        return not errors, errors

    def create_location(
        self,
        location_data: dict,
        current_user_id: str,
        session: Optional[Session] = None,
    ) -> Tuple[bool, str, Optional[models.Location]]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            is_valid, errors = self.validate_location_data(
                location_data, is_new=True, session=_session
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors), None

            def process_string(value: Any) -> Optional[str]:
                return value.strip() if isinstance(value, str) else None

            new_location = models.Location(  # Use models. prefix
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
            _session.add(new_location)
            # REMOVED: _session.refresh(new_location) - Refresh happens after commit in import script

            # Only commit if this method opened the session
            if _close_session:
                _session.commit()
                _session.refresh(new_location)  # Refresh here if committed internally

            self.logger.info(
                f"Location '{new_location.location_name}' created by {current_user_id}."
            )
            return True, "Location created successfully.", new_location
        except sqlalchemy_exc.IntegrityError as e:
            _session.rollback()
            self.logger.error(f"Error creating location: {e.orig}", exc_info=True)
            return False, f"Database integrity error: {e.orig}", None
        except Exception as e:
            _session.rollback()
            self.logger.error(f"Error creating location: {e}", exc_info=True)
            return False, f"Failed to create location: {e}", None
        finally:
            if _close_session:
                _session.close()

    def update_location(
        self,
        location_id: int,
        location_data: dict,
        current_user_id: str,
        session: Optional[Session] = None,
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            is_valid, errors = self.validate_location_data(
                location_data,
                is_new=False,
                location_id_to_check_for_unique=location_id,
                session=_session,
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            location = (
                _session.query(models.Location)
                .filter(models.Location.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found."

            for key, value in location_data.items():
                if hasattr(location, key):
                    processed_value = value.strip() if isinstance(value, str) else value
                    setattr(location, key, processed_value)

            location.modified_by = current_user_id
            if _close_session:
                _session.commit()
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location_id}) updated by {current_user_id}."
            )
            return True, "Location updated successfully."
        except Exception as e:
            _session.rollback()
            self.logger.error(
                f"Error updating location ID {location_id}: {e}", exc_info=True
            )
            return False, f"Failed to update location: {e}"
        finally:
            if _close_session:
                _session.close()

    def toggle_location_active_status(
        self,
        location_id: int,
        current_user_id: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            location = (
                _session.query(models.Location)
                .filter(models.Location.location_id == location_id)
                .first()
            )
            if not location:
                return False, f"Location with ID {location_id} not found."

            location.is_active = not location.is_active
            location.modified_by = current_user_id

            if _close_session:
                _session.commit()

            new_status = "activated" if location.is_active else "deactivated"
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location_id}) status changed to {new_status} by {current_user_id}."
            )
            return (
                True,
                f"Location '{location.location_name}' has been successfully {new_status}.",
            )

        except sqlalchemy_exc.SQLAlchemyError as e:
            _session.rollback()
            self.logger.error(
                f"Database error toggling status for location ID {location_id}: {e}",
                exc_info=True,
            )
            return False, "A database error occurred while toggling location status."
        finally:
            if _close_session:
                _session.close()

    def delete_location(
        self, location_id: int, current_user_id: str, session: Optional[Session] = None
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            linked_horses_count = (
                _session.query(models.HorseLocation)
                .filter(models.HorseLocation.location_id == location_id)
                .count()
            )

            if linked_horses_count > 0:
                message = f"Cannot delete location. It is currently or was previously assigned to {linked_horses_count} horse(s)."
                self.logger.warning(message)
                return False, message

            location_to_delete = (
                _session.query(models.Location)
                .filter(models.Location.location_id == location_id)
                .first()
            )

            if not location_to_delete:
                return False, "Location not found."

            location_name = location_to_delete.location_name
            _session.delete(location_to_delete)
            if _close_session:
                _session.commit()
            self.logger.info(
                f"Location '{location_name}' (ID: {location_id}) deleted by {current_user_id}."
            )
            return True, f"Location '{location_name}' was deleted."
        except sqlalchemy_exc.SQLAlchemyError as e:
            _session.rollback()
            self.logger.error(
                f"Database error deleting location ID {location_id}: {e}", exc_info=True
            )
            return False, f"A database error occurred: {e}"
        finally:
            if _close_session:
                _session.close()
