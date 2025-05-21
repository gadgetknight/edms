# controllers/location_controller.py
"""
EDSI Veterinary Management System - Location Controller
Version: 1.1.0 (Based on GitHub v1.0.0)
Purpose: Handles business logic for managing practice locations.
         Enhanced to handle all detailed address and contact fields from Location model.
         Added eager loading for state relationship to prevent DetachedInstanceError.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-05-20):
    - (Based on GitHub v1.0.0)
    - Enhanced `validate_location_data` to include checks for new address/contact fields
      (e.g., length checks for address lines, city, zip, phone, email format).
    - Modified `create_location` to accept and store all new address and contact fields
      from the Location model (address_line1, address_line2, city, state_code,
      zip_code, country_code, phone, email, contact_person). Sanitizes empty strings
      to None for nullable fields.
    - Modified `update_location` to allow updating of all new address and contact fields,
      with similar sanitization.
    - Added `_sanitize_value` helper method for consistent input cleaning.
    - Updated `get_location_by_id` and `get_all_locations` to use `joinedload` for
      the `state` relationship to prevent DetachedInstanceError.
    - Added `delete_location` method with a placeholder for dependency checking (critical).
      (Note: The previous v1.0.0 from user did not have delete_location, this adds it back
       from what would be expected in a full CRUD controller, aligning with prior discussions
       if this controller was previously more complete).
- v1.0.0 (2025-05-19):
    - Initial implementation with CRUD operations for Locations (name, description, active).
    - Includes validation for location_name (required, unique).
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload  # Added joinedload
from sqlalchemy import exc as sqlalchemy_exc
import re  # For email validation

from config.database_config import db_manager
from models import (
    Location as LocationModel,
    StateProvince as StateProvinceModel,  # For type hinting and validation if needed
)
from models.base_model import BaseModel


class LocationController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _sanitize_value(
        self, value: Optional[str], max_length: Optional[int] = None
    ) -> Optional[str]:
        """Helper to strip whitespace and optionally truncate. Returns None if empty after strip."""
        if value is None:
            return None
        stripped_value = str(value).strip()
        if not stripped_value:
            return None
        if max_length is not None and len(stripped_value) > max_length:
            # Optionally log truncation or handle as an error in validation instead
            self.logger.warning(
                f"Value truncated from '{stripped_value}' to max length {max_length}"
            )
            return stripped_value[:max_length]
        return stripped_value

    def validate_location_data(
        self,
        location_data: Dict[str, Any],
        is_new: bool = True,
        location_id_to_check_for_unique: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """Validates location data before saving, including all address/contact fields."""
        errors = []
        location_name = self._sanitize_value(location_data.get("location_name"), 100)

        if not location_name:
            errors.append("Location Name is required.")
        # Removed length check for location_name here as _sanitize_value handles it,
        # but explicit validation error is better if truncation is not desired.
        # For now, assuming truncation is acceptable if it happens via _sanitize_value.
        # If not, add: elif len(location_data.get("location_name", "").strip()) > 100:
        # errors.append("Location Name cannot exceed 100 characters.")

        else:  # Check uniqueness only if location_name is present
            session = db_manager.get_session()
            try:
                query = session.query(LocationModel).filter(
                    LocationModel.location_name == location_name
                )
                if not is_new and location_id_to_check_for_unique is not None:
                    query = query.filter(
                        LocationModel.location_id != location_id_to_check_for_unique
                    )
                if query.first():
                    errors.append(
                        f"A location with the name '{location_name}' already exists."
                    )
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(
                    f"Database error during location name uniqueness check: {e}",
                    exc_info=True,
                )
                errors.append(
                    "A database error occurred while validating the location name."
                )
            finally:
                session.close()

        # Validate other fields (lengths are based on typical DB constraints, adjust if needed)
        # Model definition for Location uses String(255) for address_line1, address_line2, description
        # String(100) for city, contact_person, email
        # String(30) for phone
        # String(20) for zip_code
        # String(10) for state_code, country_code

        fields_to_validate_length = {
            "address_line1": 255,
            "address_line2": 255,
            "city": 100,
            "zip_code": 20,
            "country_code": 10,
            "phone": 30,
            "email": 100,
            "contact_person": 100,
            "description": 255,
        }
        for field, max_len in fields_to_validate_length.items():
            value = location_data.get(field)
            if value is not None and len(str(value).strip()) > max_len:
                errors.append(
                    f"{field.replace('_', ' ').title()} cannot exceed {max_len} characters."
                )

        email_val = self._sanitize_value(location_data.get("email"), 100)
        if email_val and not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_val
        ):
            errors.append("Invalid email format.")

        state_code_val = self._sanitize_value(location_data.get("state_code"), 10)
        if state_code_val:  # If state_code is provided, check if it exists
            session = db_manager.get_session()
            try:
                if (
                    not session.query(StateProvinceModel)
                    .filter(StateProvinceModel.state_code == state_code_val)
                    .first()
                ):
                    errors.append(f"State Code '{state_code_val}' is not valid.")
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(f"DB error validating state_code: {e}", exc_info=True)
                errors.append("Error validating state code.")
            finally:
                session.close()

        return not errors, errors

    def create_location(
        self, location_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[LocationModel]]:
        """Creates a new location with all fields."""
        is_valid, errors = self.validate_location_data(location_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_location = LocationModel(
                location_name=self._sanitize_value(
                    location_data["location_name"], 100
                ),  # Already validated not empty
                address_line1=self._sanitize_value(
                    location_data.get("address_line1"), 255
                ),
                address_line2=self._sanitize_value(
                    location_data.get("address_line2"), 255
                ),
                city=self._sanitize_value(location_data.get("city"), 100),
                state_code=self._sanitize_value(location_data.get("state_code"), 10),
                zip_code=self._sanitize_value(location_data.get("zip_code"), 20),
                country_code=self._sanitize_value(
                    location_data.get("country_code"), 10
                ),
                phone=self._sanitize_value(location_data.get("phone"), 30),
                email=self._sanitize_value(location_data.get("email"), 100),
                contact_person=self._sanitize_value(
                    location_data.get("contact_person"), 100
                ),
                description=self._sanitize_value(location_data.get("description"), 255),
                is_active=location_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_location)
            session.commit()
            session.refresh(new_location)
            if new_location.state_code:  # Eager load state if it exists after creation
                session.query(LocationModel).options(
                    joinedload(LocationModel.state)
                ).filter_by(location_id=new_location.location_id).one()

            self.logger.info(
                f"Location '{new_location.location_name}' (ID: {new_location.location_id}) created by {current_user_id}."
            )
            return True, "Location created successfully.", new_location
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating location: {ie.orig}", exc_info=True
            )
            return (
                False,
                f"Database integrity error: Could not save location. It might already exist or a foreign key is invalid. {ie.orig}",
                None,
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"SQLAlchemyError creating location: {e}", exc_info=True)
            return False, f"Database error creating location: {e}", None
        finally:
            session.close()

    def update_location(
        self, location_id: int, location_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[
        bool, str, Optional[LocationModel]
    ]:  # Added Optional[LocationModel] to return type
        """Updates an existing location with all fields."""
        is_valid, errors = self.validate_location_data(
            location_data, is_new=False, location_id_to_check_for_unique=location_id
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .filter(LocationModel.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found.", None

            location.location_name = self._sanitize_value(
                location_data["location_name"], 100
            )  # Validated not empty
            location.address_line1 = self._sanitize_value(
                location_data.get("address_line1"), 255
            )
            location.address_line2 = self._sanitize_value(
                location_data.get("address_line2"), 255
            )
            location.city = self._sanitize_value(location_data.get("city"), 100)
            location.state_code = self._sanitize_value(
                location_data.get("state_code"), 10
            )
            location.zip_code = self._sanitize_value(location_data.get("zip_code"), 20)
            location.country_code = self._sanitize_value(
                location_data.get("country_code"), 10
            )
            location.phone = self._sanitize_value(location_data.get("phone"), 30)
            location.email = self._sanitize_value(location_data.get("email"), 100)
            location.contact_person = self._sanitize_value(
                location_data.get("contact_person"), 100
            )
            location.description = self._sanitize_value(
                location_data.get("description"), 255
            )

            if "is_active" in location_data:
                location.is_active = location_data["is_active"]
            location.modified_by = current_user_id

            session.commit()
            session.refresh(location)  # Refresh to get updated state
            if location.state_code:  # Eager load state if it exists after update
                session.query(LocationModel).options(
                    joinedload(LocationModel.state)
                ).filter_by(location_id=location.location_id).one()

            self.logger.info(
                f"Location '{location.location_name}' (ID: {location.location_id}) updated by {current_user_id}."
            )
            return True, "Location updated successfully.", location
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating location: {ie.orig}", exc_info=True
            )
            return (
                False,
                f"Database integrity error: Could not update location. Name might conflict or FK invalid. {ie.orig}",
                None,
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"SQLAlchemyError updating location: {e}", exc_info=True)
            return False, f"Database error updating location: {e}", None
        finally:
            session.close()

    def get_location_by_id(self, location_id: int) -> Optional[LocationModel]:
        """Fetches a single location by its ID, eagerly loading state."""
        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .options(joinedload(LocationModel.state))  # Eager load state
                .filter(LocationModel.location_id == location_id)
                .first()
            )
            return location
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching location by ID {location_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_all_locations(self, status_filter: str = "all") -> List[LocationModel]:
        """
        Fetches all locations, optionally filtered by active status, eagerly loading state.
        status_filter: "all", "active", "inactive"
        """
        session = db_manager.get_session()
        try:
            query = session.query(LocationModel).options(
                joinedload(LocationModel.state)
            )  # Eager load state
            if status_filter == "active":
                query = query.filter(LocationModel.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(LocationModel.is_active == False)

            locations = query.order_by(LocationModel.location_name).all()
            return locations
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching all locations with filter '{status_filter}': {e}",
                exc_info=True,
            )
            return []
        finally:
            session.close()

    def toggle_location_status(
        self, location_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        """Toggles the active status of a location."""
        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .filter(LocationModel.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found."

            location.is_active = not location.is_active
            location.modified_by = current_user_id
            action_desc = "activated" if location.is_active else "deactivated"

            session.commit()
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location.location_id}) status changed to {action_desc} by {current_user_id}."
            )
            return True, f"Location '{location.location_name}' has been {action_desc}."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error toggling location status for ID {location_id}: {e}",
                exc_info=True,
            )
            return False, "Database error occurred while changing location status."
        finally:
            session.close()

    def delete_location(
        self, location_id: int, current_user_id: str  # Added current_user_id
    ) -> Tuple[bool, str]:
        """
        Deletes a location. Includes a basic check for horse assignment.
        """
        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .filter(LocationModel.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found."

            # Basic dependency check: Are any horses assigned to this location?
            # This requires Horse model.
            from models import Horse as HorseModel  # Local import for dependency check

            if (
                session.query(HorseModel)
                .filter(HorseModel.current_location_id == location_id)
                .first()
            ):
                return (
                    False,
                    "Cannot delete location: It is currently assigned to one or more horses. Please deactivate it instead.",
                )

            self.logger.warning(
                f"Attempting hard delete of location ID {location_id} ('{location.location_name}') by user {current_user_id}."
            )
            location_name_for_msg = location.location_name  # Store before delete
            session.delete(location)
            session.commit()
            self.logger.info(
                f"Location ID {location_id} ('{location_name_for_msg}') permanently deleted by {current_user_id}."
            )
            return True, f"Location '{location_name_for_msg}' permanently deleted."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError deleting location: {ie.orig}", exc_info=True
            )
            # This might also catch FK violations if a horse was somehow still assigned
            # despite the check, or other DB constraints.
            return (
                False,
                f"Cannot delete location. It might be in use or referenced by other records. ({ie.orig})",
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error deleting location ID {location_id}: {e}", exc_info=True
            )
            return False, "Database error occurred while deleting location."
        finally:
            session.close()
