# controllers/charge_code_controller.py

"""
EDSI Veterinary Management System - Charge Code Controller
Version: 1.0.0
Purpose: Business logic for charge code operations including CRUD and validation.
Last Updated: May 17, 2025
Author: Claude Assistant
"""

import logging
from typing import List, Optional, Tuple, Dict
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from config.database_config import db_manager
from models import ChargeCode


class ChargeCodeController:
    """Controller for charge code operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_charge_code_data(
        self, charge_data: dict, is_new: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validates charge code data.
        Args:
            charge_data: Dictionary containing charge code information.
                         Expected keys: 'code', 'description', 'standard_charge',
                                        'alternate_code' (optional), 'category' (optional).
            is_new: Boolean indicating if this is for a new charge code (True) or an update (False).
        Returns:
            Tuple (is_valid, list_of_errors).
        """
        errors = []
        code = charge_data.get("code", "").strip()
        description = charge_data.get("description", "").strip()
        standard_charge_str = str(
            charge_data.get("standard_charge", "")
        ).strip()  # Ensure it's a string for Decimal conversion

        if not code:
            errors.append("Charge Code (Code) is required.")
        elif len(code) > 50:
            errors.append("Charge Code (Code) cannot exceed 50 characters.")

        if (
            is_new and code
        ):  # Check for duplicate code only if it's a new entry and code is provided
            if self.get_charge_code_by_code(code):
                errors.append(f"Charge Code '{code}' already exists.")

        if not description:
            errors.append("Description is required.")
        elif len(description) > 255:
            errors.append("Description cannot exceed 255 characters.")

        if not standard_charge_str:
            errors.append("Standard Charge is required.")
        else:
            try:
                charge_value = Decimal(standard_charge_str)
                if charge_value < Decimal("0.00"):
                    errors.append("Standard Charge cannot be negative.")
                # Numeric(10,2) means up to 99,999,999.99.
                # We can add a check for total digits if necessary, but SQLAlchemy handles precision.
            except InvalidOperation:
                errors.append("Standard Charge must be a valid number (e.g., 25.00).")

        alternate_code = charge_data.get("alternate_code", "").strip()
        if alternate_code and len(alternate_code) > 50:
            errors.append("Alternate Code cannot exceed 50 characters.")

        category = charge_data.get("category", "").strip()
        if category and len(category) > 100:
            errors.append("Category cannot exceed 100 characters.")

        return not errors, errors

    def create_charge_code(
        self, charge_data: dict
    ) -> Tuple[bool, str, Optional[ChargeCode]]:
        """
        Creates a new charge code.
        Args:
            charge_data: Dictionary of charge code data.
        Returns:
            Tuple (success_bool, message_str, charge_code_object_or_None).
        """
        is_valid, errors = self.validate_charge_code_data(charge_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_charge_code = ChargeCode(
                code=charge_data["code"].strip(),
                description=charge_data["description"].strip(),
                standard_charge=Decimal(str(charge_data["standard_charge"]).strip()),
                alternate_code=charge_data.get("alternate_code", "").strip() or None,
                category=charge_data.get("category", "").strip() or None,
                is_active=charge_data.get("is_active", True),  # Default to active
            )
            session.add(new_charge_code)
            session.commit()
            session.refresh(new_charge_code)
            self.logger.info(
                f"Charge Code '{new_charge_code.code}' created successfully (ID: {new_charge_code.charge_code_id})."
            )
            return True, "Charge code created successfully.", new_charge_code
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating charge code: {e}", exc_info=True)
            return False, f"Failed to create charge code: {str(e)}", None
        finally:
            session.close()

    def get_charge_code_by_id(self, charge_code_id: int) -> Optional[ChargeCode]:
        session = db_manager.get_session()
        try:
            return (
                session.query(ChargeCode)
                .filter(ChargeCode.charge_code_id == charge_code_id)
                .first()
            )
        except Exception as e:
            self.logger.error(
                f"Error fetching charge code by ID {charge_code_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_charge_code_by_code(self, code: str) -> Optional[ChargeCode]:
        """Fetches a charge code by its primary code (case-sensitive)."""
        session = db_manager.get_session()
        try:
            return session.query(ChargeCode).filter(ChargeCode.code == code).first()
        except Exception as e:
            self.logger.error(
                f"Error fetching charge code by code '{code}': {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_all_charge_codes(
        self, search_term: str = "", status_filter: str = "all"
    ) -> List[ChargeCode]:
        """
        Retrieves all charge codes, optionally filtered by search term and active status.
        Args:
            search_term: Term to search in code, alternate_code, description, or category.
            status_filter: "all", "active", or "inactive".
        Returns:
            List of ChargeCode objects.
        """
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCode)

            if status_filter == "active":
                query = query.filter(ChargeCode.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(ChargeCode.is_active == False)

            if search_term:
                like_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        ChargeCode.code.ilike(like_pattern),
                        ChargeCode.alternate_code.ilike(like_pattern),
                        ChargeCode.description.ilike(like_pattern),
                        ChargeCode.category.ilike(like_pattern),
                    )
                )

            return query.order_by(ChargeCode.category, ChargeCode.code).all()
        except Exception as e:
            self.logger.error(f"Error fetching all charge codes: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def update_charge_code(
        self, charge_code_id: int, charge_data: dict
    ) -> Tuple[bool, str]:
        """
        Updates an existing charge code.
        Args:
            charge_code_id: The ID of the charge code to update.
            charge_data: Dictionary containing updated data.
        Returns:
            Tuple (success_bool, message_str).
        """
        session = db_manager.get_session()
        try:
            charge_code_to_update = (
                session.query(ChargeCode)
                .filter(ChargeCode.charge_code_id == charge_code_id)
                .first()
            )
            if not charge_code_to_update:
                return False, "Charge code not found."

            # Validate, but exclude current code from unique check if it hasn't changed
            original_code = charge_code_to_update.code
            current_code_in_data = charge_data.get("code", "").strip()

            # If code is being changed, it must be unique among other records
            if current_code_in_data and current_code_in_data != original_code:
                existing_with_new_code = self.get_charge_code_by_code(
                    current_code_in_data
                )
                if (
                    existing_with_new_code
                    and existing_with_new_code.charge_code_id != charge_code_id
                ):
                    return (
                        False,
                        f"Validation failed: Charge Code '{current_code_in_data}' already exists for another record.",
                    )

            # For other validations, pass all data
            is_valid, errors = self.validate_charge_code_data(charge_data, is_new=False)
            if not is_valid:
                # Filter out potential duplicate error if code wasn't actually changed
                if current_code_in_data == original_code:
                    errors = [
                        e
                        for e in errors
                        if not e.startswith(
                            f"Charge Code '{original_code}' already exists."
                        )
                    ]
                if errors:  # If other errors remain
                    return False, "Validation failed: " + "; ".join(errors)

            charge_code_to_update.code = charge_data.get(
                "code", charge_code_to_update.code
            ).strip()
            charge_code_to_update.description = charge_data.get(
                "description", charge_code_to_update.description
            ).strip()

            if (
                "standard_charge" in charge_data
            ):  # Ensure it's present before trying to convert
                charge_code_to_update.standard_charge = Decimal(
                    str(charge_data["standard_charge"]).strip()
                )

            charge_code_to_update.alternate_code = charge_data.get(
                "alternate_code", charge_code_to_update.alternate_code
            )
            if charge_code_to_update.alternate_code:
                charge_code_to_update.alternate_code = (
                    charge_code_to_update.alternate_code.strip()
                )

            charge_code_to_update.category = charge_data.get(
                "category", charge_code_to_update.category
            )
            if charge_code_to_update.category:
                charge_code_to_update.category = charge_code_to_update.category.strip()

            if "is_active" in charge_data:
                charge_code_to_update.is_active = charge_data["is_active"]

            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code_to_update.code}' (ID: {charge_code_id}) updated."
            )
            return True, "Charge code updated successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating charge code ID {charge_code_id}: {e}", exc_info=True
            )
            return False, f"Failed to update charge code: {str(e)}"
        finally:
            session.close()

    def toggle_charge_code_status(self, charge_code_id: int) -> Tuple[bool, str]:
        """Toggles the is_active status of a charge code."""
        session = db_manager.get_session()
        try:
            charge_code = (
                session.query(ChargeCode)
                .filter(ChargeCode.charge_code_id == charge_code_id)
                .first()
            )
            if not charge_code:
                return False, "Charge code not found."

            charge_code.is_active = not charge_code.is_active
            new_status = "active" if charge_code.is_active else "inactive"
            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code.code}' (ID: {charge_code_id}) status changed to {new_status}."
            )
            return True, f"Charge code '{charge_code.code}' status set to {new_status}."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error toggling status for charge code ID {charge_code_id}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle charge code status: {str(e)}"
        finally:
            session.close()
