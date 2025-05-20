# controllers/location_controller.py
"""
EDSI Veterinary Management System - Location Controller
Version: 1.0.0
Purpose: Handles business logic for managing practice locations.
Last Updated: May 19, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-05-19):
    - Initial implementation with CRUD operations for Locations.
    - Includes validation for location_name (required, unique).
    - Methods: create_location, update_location, get_location_by_id,
      get_all_locations, toggle_location_status, validate_location_data.
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import exc as sqlalchemy_exc

from config.database_config import db_manager
from models import (
    Location as LocationModel,
)  # Alias to avoid conflict if Location is used as var name
from models.base_model import (
    BaseModel,
)  # For audit fields if needed, though Location inherits them


class LocationController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_location_data(
        self,
        location_data: Dict[str, Any],
        is_new: bool = True,
        location_id_to_check_for_unique: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """Validates location data before saving."""
        errors = []
        location_name = location_data.get("location_name", "").strip()

        if not location_name:
            errors.append("Location Name is required.")
        elif len(location_name) > 100:  # Assuming max length from model String(100)
            errors.append("Location Name cannot exceed 100 characters.")
        else:
            # Check for uniqueness
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

        description = location_data.get("description", "")
        if (
            description and len(description) > 255
        ):  # Assuming max length from model String(255)
            errors.append("Description cannot exceed 255 characters.")

        return not errors, errors

    def create_location(
        self, location_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[LocationModel]]:
        """Creates a new location."""
        is_valid, errors = self.validate_location_data(location_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_location = LocationModel(
                location_name=location_data["location_name"].strip(),
                description=location_data.get("description", "").strip()
                or None,  # Store None if empty
                is_active=location_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_location)
            session.commit()
            session.refresh(new_location)
            self.logger.info(
                f"Location '{new_location.location_name}' (ID: {new_location.location_id}) created by {current_user_id}."
            )
            return True, "Location created successfully.", new_location
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating location: {ie.orig}", exc_info=True
            )
            # This should ideally be caught by validate_location_data uniqueness check
            return (
                False,
                f"Database integrity error: Could not save location. It might already exist. {ie.orig}",
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
    ) -> Tuple[bool, str]:
        """Updates an existing location."""
        is_valid, errors = self.validate_location_data(
            location_data, is_new=False, location_id_to_check_for_unique=location_id
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors)

        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
                .filter(LocationModel.location_id == location_id)
                .first()
            )
            if not location:
                return False, "Location not found."

            location.location_name = location_data["location_name"].strip()
            location.description = location_data.get("description", "").strip() or None
            if (
                "is_active" in location_data
            ):  # Only update if provided, otherwise toggle handles it
                location.is_active = location_data["is_active"]
            location.modified_by = current_user_id
            # location.modified_date is handled by BaseModel's onupdate

            session.commit()
            self.logger.info(
                f"Location '{location.location_name}' (ID: {location.location_id}) updated by {current_user_id}."
            )
            return True, "Location updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating location: {ie.orig}", exc_info=True
            )
            return (
                False,
                f"Database integrity error: Could not update location. Name might conflict. {ie.orig}",
                None,
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"SQLAlchemyError updating location: {e}", exc_info=True)
            return False, f"Database error updating location: {e}", None
        finally:
            session.close()

    def get_location_by_id(self, location_id: int) -> Optional[LocationModel]:
        """Fetches a single location by its ID."""
        session = db_manager.get_session()
        try:
            location = (
                session.query(LocationModel)
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
        Fetches all locations, optionally filtered by active status.
        status_filter: "all", "active", "inactive"
        """
        session = db_manager.get_session()
        try:
            query = session.query(LocationModel)
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
        self, location_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        """
        Deletes a location. Consider implications (e.g., horses assigned to this location).
        For now, this is a hard delete. A soft delete (setting is_active=False) is often safer.
        The toggle_location_status method handles soft delete. This method is for permanent removal.
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

            # Check for dependencies (e.g., if horses are assigned to this location)
            # This requires access to the Horse model and potentially HorseController logic
            # For simplicity, this check is omitted here but is CRITICAL in a real system.
            # Example check (would need Horse model import):
            # from models import Horse
            # if session.query(Horse).filter(Horse.current_location_id == location_id).first():
            #     return False, "Cannot delete location: It is currently assigned to one or more horses."

            self.logger.warning(
                f"Attempting hard delete of location ID {location_id} ('{location.location_name}') by user {current_user_id}."
            )
            session.delete(location)
            session.commit()
            self.logger.info(
                f"Location ID {location_id} ('{location.location_name}') permanently deleted by {current_user_id}."
            )
            return True, f"Location '{location.location_name}' permanently deleted."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError deleting location: {ie.orig}", exc_info=True
            )
            return False, f"Cannot delete location. It might be in use. ({ie.orig})"
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error deleting location ID {location_id}: {e}", exc_info=True
            )
            return False, "Database error occurred while deleting location."
        finally:
            session.close()
