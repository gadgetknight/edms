# controllers/location_controller.py
"""
EDSI Veterinary Management System - Location Controller
Version: 1.1.1
Purpose: Handles business logic for managing practice locations.
         - Removed handling of 'description' field as it's not on Location model.
Last Updated: June 02, 2025
Author: Gemini

Changelog:
- v1.1.1 (2025-06-02):
    - Removed 'description' field handling from `validate_location_data`,
      `create_location`, and `update_location` methods to align with
      the Location model which does not have this attribute.
- v1.1.0 (2025-05-20) (Based on GitHub v1.0.0):
    - Enhanced to handle all detailed address and contact fields from Location model.
    - Added eager loading for state relationship to prevent DetachedInstanceError.
    - Added `delete_location` method.
- v1.0.0 (2025-05-19) (User's original baseline):
    - Initial implementation with CRUD for Locations (name, description, active).
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc as sqlalchemy_exc
import re

from config.database_config import db_manager
from models import (
    Location as LocationModel,
    StateProvince as StateProvinceModel,
    Horse as HorseModel,  # Moved import here for delete_location check
)

# BaseModel import is not directly used here, but models inherit from it.


class LocationController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _sanitize_value(
        self, value: Optional[str], max_length: Optional[int] = None
    ) -> Optional[str]:
        if value is None:
            return None
        stripped_value = str(value).strip()
        if not stripped_value:
            return None
        if max_length is not None and len(stripped_value) > max_length:
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
        errors = []
        location_name = self._sanitize_value(location_data.get("location_name"), 100)

        if not location_name:
            errors.append("Location Name is required.")
        else:
            session = db_manager.get_session()
            try:
                query = session.query(LocationModel).filter(
                    LocationModel.location_name.collate("NOCASE")
                    == location_name  # Added collate for case-insensitivity
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

        fields_to_validate_length = {
            "address_line1": 100,  # Max length from Location model
            "address_line2": 100,  # Max length from Location model
            "city": 50,  # Max length from Location model
            "zip_code": 20,  # Max length from Location model
            "country_code": 10,  # Max length from Location model
            "phone": 20,  # Max length from Location model
            "email": 100,  # Max length from Location model (once added)
            "contact_person": 100,  # Max length from Location model
            # REMOVED: "description": 255,
        }
        for field, max_len in fields_to_validate_length.items():
            value = location_data.get(field)
            # Check if value is not None before calling strip() and len()
            if (
                value is not None
                and isinstance(value, str)
                and len(value.strip()) > max_len
            ):
                errors.append(
                    f"{field.replace('_', ' ').title()} cannot exceed {max_len} characters."
                )

        email_val = self._sanitize_value(location_data.get("email"), 100)
        if email_val and not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_val
        ):
            errors.append("Invalid email format.")

        state_code_val = self._sanitize_value(location_data.get("state_code"), 10)
        if state_code_val:
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
        is_valid, errors = self.validate_location_data(location_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_location = LocationModel(
                location_name=self._sanitize_value(location_data["location_name"], 100),
                address_line1=self._sanitize_value(
                    location_data.get("address_line1"), 100
                ),
                address_line2=self._sanitize_value(
                    location_data.get("address_line2"), 100
                ),
                city=self._sanitize_value(location_data.get("city"), 50),
                state_code=self._sanitize_value(location_data.get("state_code"), 10),
                zip_code=self._sanitize_value(location_data.get("zip_code"), 20),
                country_code=self._sanitize_value(
                    location_data.get("country_code"), 10
                ),
                phone=self._sanitize_value(location_data.get("phone"), 20),
                email=self._sanitize_value(
                    location_data.get("email"), 100
                ),  # Uses email if provided by dialog
                contact_person=self._sanitize_value(
                    location_data.get("contact_person"), 100
                ),
                # REMOVED: description from instantiation
                is_active=location_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_location)
            session.commit()
            session.refresh(new_location)
            if new_location.state_code:
                session.query(LocationModel).options(
                    joinedload(LocationModel.state)
                ).filter_by(
                    location_id=new_location.location_id
                ).one_or_none()  # one_or_none more robust

            self.logger.info(
                f"Location '{new_location.location_name}' (ID: {new_location.location_id}) created by {current_user_id}."
            )
            return True, "Location created successfully.", new_location
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating location: {ie.orig}", exc_info=True
            )
            # Check for unique constraint on location_name
            if "UNIQUE constraint failed: locations.location_name" in str(ie.orig):
                return (
                    False,
                    f"A location with the name '{location_data['location_name']}' already exists.",
                    None,
                )
            return False, f"Database integrity error: {ie.orig}", None
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"SQLAlchemyError creating location: {e}", exc_info=True)
            return False, f"Database error creating location: {e}", None
        finally:
            session.close()

    def update_location(
        self, location_id: int, location_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[LocationModel]]:
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

            location.location_name = self._sanitize_value(location_data["location_name"], 100)  # type: ignore
            location.address_line1 = self._sanitize_value(
                location_data.get("address_line1"), 100
            )
            location.address_line2 = self._sanitize_value(
                location_data.get("address_line2"), 100
            )
            location.city = self._sanitize_value(location_data.get("city"), 50)
            location.state_code = self._sanitize_value(
                location_data.get("state_code"), 10
            )
            location.zip_code = self._sanitize_value(location_data.get("zip_code"), 20)
            location.country_code = self._sanitize_value(
                location_data.get("country_code"), 10
            )
            location.phone = self._sanitize_value(location_data.get("phone"), 20)
            location.email = self._sanitize_value(location_data.get("email"), 100)
            location.contact_person = self._sanitize_value(
                location_data.get("contact_person"), 100
            )
            # REMOVED: location.description update

            if "is_active" in location_data:
                location.is_active = location_data["is_active"]
            location.modified_by = current_user_id

            session.commit()
            session.refresh(location)
            if location.state_code:
                session.query(LocationModel).options(
                    joinedload(LocationModel.state)
                ).filter_by(location_id=location.location_id).one_or_none()

            self.logger.info(
                f"Location '{location.location_name}' (ID: {location.location_id}) updated by {current_user_id}."
            )
            return True, "Location updated successfully.", location
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating location: {ie.orig}", exc_info=True
            )
            if "UNIQUE constraint failed: locations.location_name" in str(ie.orig):
                return (
                    False,
                    f"A location with the name '{location_data['location_name']}' already exists.",
                    None,
                )
            return False, f"Database integrity error: {ie.orig}", None
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"SQLAlchemyError updating location: {e}", exc_info=True)
            return False, f"Database error updating location: {e}", None
        finally:
            session.close()

    def get_location_by_id(self, location_id: int) -> Optional[LocationModel]:
        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .options(joinedload(LocationModel.state))
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
        session = db_manager.get_session()
        try:
            query = session.query(LocationModel).options(
                joinedload(LocationModel.state)
            )
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
        self, location_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
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
            # HorseModel was imported at the top of the file now.
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
            location_name_for_msg = location.location_name
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
