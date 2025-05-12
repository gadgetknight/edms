"""
EDSI Veterinary Management System - Horse Controller
Version: 1.0.0
Purpose: Business logic for horse management operations including CRUD, validation, and data processing.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.0 (2025-05-12): Initial implementation
  - Created HorseController class with CRUD operations
  - Implemented horse validation logic
  - Added search and filtering capabilities
  - Included proper error handling and logging
  - Added methods for horse-owner relationship management
"""

# controllers/horse_controller.py

import logging
from datetime import datetime, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from config.database_config import db_manager
from models import Horse, Owner, HorseOwner, Location, Species


class HorseController:
    """Controller for horse management operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_horse(
        self, horse_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Horse]]:
        """
        Create a new horse record

        Args:
            horse_data: Dictionary containing horse information
            current_user: Current logged-in user ID

        Returns:
            Tuple of (success, message, horse_object)
        """
        session = db_manager.get_session()
        try:
            # Validate required fields
            if not horse_data.get("horse_name", "").strip():
                return False, "Horse name is required", None

            # Create horse object
            horse = Horse(
                horse_name=horse_data["horse_name"].strip(),
                account_number=horse_data.get("account_number", "").strip(),
                species_code=horse_data.get("species_code"),
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
            )

            session.add(horse)
            session.commit()

            self.logger.info(
                f"Created new horse: {horse.horse_name} (ID: {horse.horse_id})"
            )
            return True, "Horse created successfully", horse

        except Exception as e:
            session.rollback()
            error_msg = f"Error creating horse: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None
        finally:
            session.close()

    def update_horse(
        self, horse_id: int, horse_data: dict, current_user: str
    ) -> Tuple[bool, str]:
        """
        Update an existing horse record

        Args:
            horse_id: ID of horse to update
            horse_data: Dictionary containing updated horse information
            current_user: Current logged-in user ID

        Returns:
            Tuple of (success, message)
        """
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found"

            # Validate required fields
            if not horse_data.get("horse_name", "").strip():
                return False, "Horse name is required"

            # Update fields
            horse.horse_name = horse_data["horse_name"].strip()
            horse.account_number = horse_data.get("account_number", "").strip()
            horse.species_code = horse_data.get("species_code")
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
            self.logger.error(error_msg)
            return False, error_msg
        finally:
            session.close()

    def get_horse_by_id(self, horse_id: int) -> Optional[Horse]:
        """Get horse by ID"""
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if horse:
                # Eager load related data
                _ = horse.species  # Load species relationship
                _ = horse.location  # Load location relationship
            return horse
        except Exception as e:
            self.logger.error(f"Error getting horse by ID {horse_id}: {str(e)}")
            return None
        finally:
            session.close()

    def search_horses(
        self, search_term: str = "", active_only: bool = True
    ) -> List[Horse]:
        """
        Search horses by name or account number

        Args:
            search_term: Search term to match against horse name or account number
            active_only: If True, only return active horses

        Returns:
            List of matching horses
        """
        session = db_manager.get_session()
        try:
            query = session.query(Horse)

            if active_only:
                query = query.filter(Horse.is_active == True)

            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Horse.horse_name.like(search_pattern),
                        Horse.account_number.like(search_pattern),
                    )
                )

            horses = query.order_by(Horse.horse_name).all()

            # Eager load related data for all horses
            for horse in horses:
                _ = horse.species
                _ = horse.location

            return horses
        except Exception as e:
            self.logger.error(f"Error searching horses: {str(e)}")
            return []
        finally:
            session.close()

    def get_species_list(self) -> List[Species]:
        """Get list of all active species"""
        session = db_manager.get_session()
        try:
            return (
                session.query(Species)
                .filter(Species.is_active == True)
                .order_by(Species.species_name)
                .all()
            )
        except Exception as e:
            self.logger.error(f"Error getting species list: {str(e)}")
            return []
        finally:
            session.close()

    def get_locations_list(self) -> List[Location]:
        """Get list of all active locations"""
        session = db_manager.get_session()
        try:
            return (
                session.query(Location)
                .filter(Location.is_active == True)
                .order_by(Location.location_name)
                .all()
            )
        except Exception as e:
            self.logger.error(f"Error getting locations list: {str(e)}")
            return []
        finally:
            session.close()

    def validate_horse_data(self, horse_data: dict) -> Tuple[bool, List[str]]:
        """
        Validate horse data

        Args:
            horse_data: Dictionary containing horse information

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required field validation
        if not horse_data.get("horse_name", "").strip():
            errors.append("Horse name is required")

        # Length validation
        if len(horse_data.get("horse_name", "")) > 100:
            errors.append("Horse name cannot exceed 100 characters")

        if len(horse_data.get("account_number", "")) > 20:
            errors.append("Account number cannot exceed 20 characters")

        if len(horse_data.get("breed", "")) > 50:
            errors.append("Breed cannot exceed 50 characters")

        # Date validation
        if horse_data.get("date_of_birth"):
            try:
                birth_date = self._parse_date(horse_data["date_of_birth"])
                if birth_date and birth_date > date.today():
                    errors.append("Date of birth cannot be in the future")
            except:
                errors.append("Invalid date of birth format")

        return len(errors) == 0, errors

    def _parse_date(self, date_value) -> Optional[date]:
        """Parse date from various formats"""
        if not date_value:
            return None

        if isinstance(date_value, date):
            return date_value

        if isinstance(date_value, str):
            # Try different date formats
            formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue

        return None

    def delete_horse(self, horse_id: int) -> Tuple[bool, str]:
        """
        Soft delete a horse (mark as inactive)

        Args:
            horse_id: ID of horse to delete

        Returns:
            Tuple of (success, message)
        """
        session = db_manager.get_session()
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return False, f"Horse with ID {horse_id} not found"

            horse.is_active = False
            horse.modified_date = datetime.utcnow()
            session.commit()

            self.logger.info(
                f"Deactivated horse: {horse.horse_name} (ID: {horse.horse_id})"
            )
            return True, "Horse deactivated successfully"

        except Exception as e:
            session.rollback()
            error_msg = f"Error deactivating horse: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        finally:
            session.close()
