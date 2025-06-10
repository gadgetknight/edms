# controllers/veterinarian_controller.py
"""
EDSI Veterinary Management System - Veterinarian Controller
Version: 1.1.0
Purpose: Handles business logic for veterinarian records.
Last Updated: June 9, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-09):
    - Replaced placeholder with a full implementation providing CRUD operations.
- v1.0.0 (2025-06-09):
    - Initial placeholder file created.
"""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import exc as sqlalchemy_exc

from config.database_config import db_manager
from models import Veterinarian


class VeterinarianController:
    """Controller for veterinarian management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_veterinarians(self, status_filter: str = "all") -> List[Veterinarian]:
        """Retrieves all veterinarians, optionally filtered by active status."""
        session = db_manager.get_session()
        try:
            query = session.query(Veterinarian)
            if status_filter == "active":
                query = query.filter(Veterinarian.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(Veterinarian.is_active == False)

            vets = query.order_by(Veterinarian.last_name, Veterinarian.first_name).all()
            return vets
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all veterinarians: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_veterinarian_by_id(self, vet_id: int) -> Optional[Veterinarian]:
        """Retrieves a single veterinarian by their primary key."""
        session = db_manager.get_session()
        try:
            return (
                session.query(Veterinarian)
                .filter(Veterinarian.vet_id == vet_id)
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching veterinarian by ID {vet_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def validate_veterinarian_data(
        self,
        vet_data: Dict[str, Any],
        is_new: bool,
        vet_id_to_ignore: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        """Validates veterinarian data for creation or update."""
        errors = []
        required_fields = ["first_name", "last_name", "license_number"]
        for field in required_fields:
            if not vet_data.get(field) or not str(vet_data[field]).strip():
                errors.append(f"{field.replace('_', ' ').title()} is required.")

        license_number = vet_data.get("license_number", "").strip()
        email = vet_data.get("email", "").strip()

        session = db_manager.get_session()
        try:
            # Check license number uniqueness
            if license_number:
                query = session.query(Veterinarian).filter(
                    Veterinarian.license_number == license_number
                )
                if not is_new and vet_id_to_ignore is not None:
                    query = query.filter(Veterinarian.vet_id != vet_id_to_ignore)
                if query.first():
                    errors.append(
                        f"License Number '{license_number}' is already in use."
                    )

            # Check email format and uniqueness
            if email:
                if not re.match(
                    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email
                ):
                    errors.append("Invalid email format.")
                else:
                    query = session.query(Veterinarian).filter(
                        Veterinarian.email == email
                    )
                    if not is_new and vet_id_to_ignore is not None:
                        query = query.filter(Veterinarian.vet_id != vet_id_to_ignore)
                    if query.first():
                        errors.append(f"Email '{email}' is already in use.")
        finally:
            session.close()

        return not errors, errors

    def create_veterinarian(
        self, vet_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[Veterinarian]]:
        """Creates a new veterinarian record."""
        is_valid, errors = self.validate_veterinarian_data(vet_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_vet = Veterinarian(
                first_name=vet_data["first_name"],
                last_name=vet_data["last_name"],
                license_number=vet_data["license_number"],
                specialty=vet_data.get("specialty"),
                phone=vet_data.get("phone"),
                email=vet_data.get("email"),
                is_active=vet_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_vet)
            session.commit()
            session.refresh(new_vet)
            self.logger.info(
                f"Veterinarian '{new_vet.first_name} {new_vet.last_name}' created by {current_user_id}."
            )
            return True, "Veterinarian created successfully.", new_vet
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            self.logger.error(f"Error creating veterinarian: {e.orig}", exc_info=True)
            return False, f"Database integrity error: {e.orig}", None
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating veterinarian: {e}", exc_info=True)
            return False, f"Failed to create veterinarian: {e}", None
        finally:
            session.close()

    def update_veterinarian(
        self, vet_id: int, vet_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str]:
        """Updates an existing veterinarian record."""
        is_valid, errors = self.validate_veterinarian_data(
            vet_data, is_new=False, vet_id_to_ignore=vet_id
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors)

        session = db_manager.get_session()
        try:
            vet = (
                session.query(Veterinarian)
                .filter(Veterinarian.vet_id == vet_id)
                .first()
            )
            if not vet:
                return False, "Veterinarian not found."

            for key, value in vet_data.items():
                if hasattr(vet, key):
                    setattr(vet, key, value)

            vet.modified_by = current_user_id
            session.commit()
            self.logger.info(f"Veterinarian ID {vet_id} updated by {current_user_id}.")
            return True, "Veterinarian updated successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating veterinarian ID {vet_id}: {e}", exc_info=True
            )
            return False, f"Failed to update veterinarian: {e}"
        finally:
            session.close()

    def toggle_veterinarian_status(
        self, vet_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        """Toggles the active status of a veterinarian."""
        session = db_manager.get_session()
        try:
            vet = (
                session.query(Veterinarian)
                .filter(Veterinarian.vet_id == vet_id)
                .first()
            )
            if not vet:
                return False, "Veterinarian not found."

            vet.is_active = not vet.is_active
            vet.modified_by = current_user_id
            new_status = "activated" if vet.is_active else "deactivated"
            session.commit()
            self.logger.info(
                f"Veterinarian '{vet.first_name} {vet.last_name}' status changed to {new_status} by {current_user_id}."
            )
            return True, f"Veterinarian has been {new_status}."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error toggling status for vet ID {vet_id}: {e}", exc_info=True
            )
            return False, f"Failed to toggle status: {e}"
        finally:
            session.close()
