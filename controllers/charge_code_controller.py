# controllers/charge_code_controller.py
"""
EDSI Veterinary Management System - Charge Code Controller
Version: 1.0.3
Purpose: Business logic for charge code operations including CRUD and validation.
         - Corrected sorting in get_all_charge_codes to use ChargeCodeCategory.name.
Last Updated: June 2, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.0.3 (2025-06-02):
    - Modified `get_all_charge_codes` to correctly sort by the related
      `ChargeCodeCategory.name` by performing an explicit join.
    - Ensured `ChargeCodeCategory` model is imported.
- v1.0.2 (2025-06-02):
    - Added `from datetime import datetime` to resolve AttributeError for
      `datetime.utcnow()` when setting `modified_date`.
- v1.0.1 (2025-06-02):
    - Added handling for 'taxable' field and audit fields.
- v1.0.0 (2025-05-17) (from bundle):
    - Initial implementation.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import (
    Session,
    joinedload,
)  # Added joinedload for potential future use here
from sqlalchemy import or_, func, exc as sqlalchemy_exc

from config.database_config import db_manager
from models import ChargeCode, ChargeCodeCategory  # ADDED ChargeCodeCategory


class ChargeCodeController:
    """Controller for charge code operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_charge_code_data(
        self, charge_data: dict, is_new: bool = True
    ) -> Tuple[bool, List[str]]:
        # This method remains unchanged from v1.0.2
        errors = []
        code = charge_data.get("code", "").strip()
        description = charge_data.get("description", "").strip()
        standard_charge_str = str(charge_data.get("standard_charge", "")).strip()

        if not code:
            errors.append("Charge Code (Code) is required.")
        elif len(code) > 20:
            errors.append("Charge Code (Code) cannot exceed 20 characters.")

        if is_new and code:
            if self.get_charge_code_by_code(code.upper()):
                errors.append(f"Charge Code '{code.upper()}' already exists.")

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
            except InvalidOperation:
                errors.append("Standard Charge must be a valid number (e.g., 25.00).")

        alternate_code = charge_data.get("alternate_code")
        if alternate_code is not None and len(alternate_code) > 50:
            errors.append("Alternate Code cannot exceed 50 characters.")

        # category_id will be validated by checking its existence if provided by dialog
        # The flat 'category' string is no longer the primary way to handle this.
        # Validation of category_id would happen if it's part of charge_data.
        # For now, assuming the dialog will provide a valid category_id.

        if "taxable" in charge_data and not isinstance(
            charge_data.get("taxable"), bool
        ):
            errors.append("Taxable field must be a true/false value.")

        # Validation for category_id if it's passed (e.g., from a dialog that selects a category)
        category_id = charge_data.get("category_id")
        if category_id is not None:
            session = db_manager.get_session()
            try:
                category_exists = (
                    session.query(ChargeCodeCategory)
                    .filter(ChargeCodeCategory.category_id == category_id)
                    .first()
                )
                if not category_exists:
                    errors.append(
                        f"Selected category ID '{category_id}' does not exist."
                    )
                elif not category_exists.is_active:
                    errors.append(
                        f"Selected category '{category_exists.name}' is not active."
                    )
                # Optionally check if it's a level 3 category if that's a rule
                # elif category_exists.level != 3: # Assuming 3 is the most specific level
                #     errors.append(f"Charge codes must be assigned to a level 3 category. '{category_exists.name}' is level {category_exists.level}.")
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(
                    f"Error validating category_id '{category_id}': {e}", exc_info=True
                )
                errors.append("Database error validating category.")
            finally:
                session.close()
        elif is_new:  # If creating a new charge code, category_id might be required
            # This depends on business rules. For now, assume it's nullable.
            pass  # errors.append("Category is required for new charge codes.")

        return not errors, errors

    def create_charge_code(
        self, charge_data: dict, current_user_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ChargeCode]]:
        # This method will need to expect 'category_id' from charge_data
        # instead of 'category' string, once the dialog is updated.
        # For now, keeping it compatible with existing dialog that sends flat 'category'
        # and also 'taxable'. The add_initial_data.py uses category_id.

        # Pre-validation to set up for hierarchical categories later
        if "category" in charge_data and "category_id" not in charge_data:
            # If flat category string is provided, we might try to look it up
            # or log a warning. For now, this controller version focuses on
            # being ready for category_id.
            self.logger.warning(
                "create_charge_code received flat 'category' string. "
                "Hierarchical category_id is expected for future compatibility."
            )

        is_valid, errors = self.validate_charge_code_data(charge_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_charge_code = ChargeCode(
                code=charge_data["code"].strip().upper(),
                alternate_code=charge_data.get("alternate_code", "").strip().upper()
                or None,
                description=charge_data["description"].strip(),
                # category field is gone from ChargeCode model, now uses category_id
                category_id=charge_data.get(
                    "category_id"
                ),  # Expects this from dialog eventually
                standard_charge=Decimal(str(charge_data["standard_charge"]).strip()),
                is_active=charge_data.get("is_active", True),
                taxable=charge_data.get("taxable", False),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_charge_code)
            session.commit()
            session.refresh(new_charge_code)
            self.logger.info(
                f"Charge Code '{new_charge_code.code}' created successfully (ID: {new_charge_code.charge_code_id}) by {current_user_id}."
            )
            return True, "Charge code created successfully.", new_charge_code
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating charge code: {ie.orig}", exc_info=True
            )
            if "UNIQUE constraint failed: charge_codes.code" in str(ie.orig).lower():
                return (
                    False,
                    f"Charge Code '{charge_data['code'].strip().upper()}' already exists.",
                    None,
                )
            return False, f"Database integrity error: {ie.orig}", None
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
                .options(
                    joinedload(ChargeCode.category)
                )  # Eager load category for display
                .filter(ChargeCode.charge_code_id == charge_code_id)
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code by ID {charge_code_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_charge_code_by_code(self, code: str) -> Optional[ChargeCode]:
        session = db_manager.get_session()
        try:
            return (
                session.query(ChargeCode)
                .options(joinedload(ChargeCode.category))  # Eager load category
                .filter(ChargeCode.code == code.upper())
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code by code '{code}': {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_all_charge_codes(
        self, search_term: str = "", status_filter: str = "all"
    ) -> List[ChargeCode]:
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCode).options(
                joinedload(ChargeCode.category)
            )  # Eager load category

            if status_filter == "active":
                query = query.filter(ChargeCode.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(ChargeCode.is_active == False)

            if search_term:
                like_pattern = f"%{search_term}%"
                # Search in ChargeCode fields and related ChargeCodeCategory name
                query = query.outerjoin(
                    ChargeCode.category
                ).filter(  # outerjoin to include those with null category_id
                    or_(
                        ChargeCode.code.ilike(like_pattern),
                        ChargeCode.alternate_code.ilike(like_pattern),
                        ChargeCode.description.ilike(like_pattern),
                        ChargeCodeCategory.name.ilike(
                            like_pattern
                        ),  # Search in category name
                    )
                )

            # MODIFIED: Corrected sorting for related category name
            # Sorting by category name, then by charge code.
            # If category is None, those might sort first or last depending on DB.
            query = query.outerjoin(ChargeCode.category).order_by(
                ChargeCodeCategory.name.asc().nullsfirst(), ChargeCode.code.asc()
            )

            return query.all()
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all charge codes: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def update_charge_code(
        self,
        charge_code_id: int,
        charge_data: dict,
        current_user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            charge_code_to_update = (
                session.query(ChargeCode)
                .filter(ChargeCode.charge_code_id == charge_code_id)
                .first()
            )
            if not charge_code_to_update:
                return False, "Charge code not found."

            validation_data = charge_data.copy()
            validation_data["code"] = (
                charge_code_to_update.code
            )  # Ensure code is part of validation if needed

            is_valid, errors = self.validate_charge_code_data(
                validation_data, is_new=False
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            if "description" in charge_data:
                charge_code_to_update.description = charge_data["description"].strip()
            if (
                "standard_charge" in charge_data
                and charge_data["standard_charge"] is not None
            ):
                try:
                    charge_code_to_update.standard_charge = Decimal(
                        str(charge_data["standard_charge"])
                    )
                except InvalidOperation:
                    self.logger.error(
                        f"Invalid standard_charge value during update: {charge_data['standard_charge']}"
                    )
                    return False, "Invalid Standard Charge value provided for update."

            if "alternate_code" in charge_data:
                charge_code_to_update.alternate_code = charge_data[
                    "alternate_code"
                ]  # Assumes already processed

            # Handle category_id update
            if (
                "category_id" in charge_data
            ):  # This is what the dialog will send eventually
                charge_code_to_update.category_id = charge_data.get("category_id")
            elif (
                "category" in charge_data
            ):  # Fallback if old dialog sends flat string (will be removed)
                self.logger.warning(
                    "update_charge_code received flat 'category' string. "
                    "This path should be updated to use category_id."
                )
                # Here you might try to find category_id based on the string, or ignore it.
                # For now, ignoring it if only flat category string is sent.

            if "is_active" in charge_data:
                charge_code_to_update.is_active = charge_data["is_active"]
            if "taxable" in charge_data:
                charge_code_to_update.taxable = charge_data["taxable"]

            charge_code_to_update.modified_by = current_user_id
            charge_code_to_update.modified_date = datetime.utcnow()

            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code_to_update.code}' (ID: {charge_code_id}) updated by {current_user_id}."
            )
            return True, "Charge code updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating charge code ID {charge_code_id}: {ie.orig}",
                exc_info=True,
            )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating charge code ID {charge_code_id}: {e}", exc_info=True
            )
            return False, f"Failed to update charge code: {str(e)}"
        finally:
            session.close()

    def toggle_charge_code_status(
        self, charge_code_id: int, current_user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
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
            charge_code.modified_by = current_user_id
            charge_code.modified_date = datetime.utcnow()
            new_status = "active" if charge_code.is_active else "inactive"

            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code.code}' (ID: {charge_code_id}) status changed to {new_status} by {current_user_id}."
            )
            return True, f"Charge code '{charge_code.code}' status set to {new_status}."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error toggling status for charge code ID {charge_code_id}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle charge code status: {str(e)}"
        finally:
            session.close()

    # --- Methods for managing ChargeCodeCategory (NEW) ---
    def get_charge_code_categories(
        self, parent_id: Optional[int] = None, level: Optional[int] = None
    ) -> List[ChargeCodeCategory]:
        """
        Fetches charge code categories, optionally filtered by parent_id and/or level.
        - If parent_id is None and level is 1, fetches top-level categories.
        - If parent_id is provided, fetches children of that parent.
        - If level is provided, filters by that level.
        """
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCodeCategory).filter(
                ChargeCodeCategory.is_active == True
            )
            if (
                parent_id is None and level == 1
            ):  # Common case: get top-level main categories
                query = query.filter(
                    ChargeCodeCategory.parent_id.is_(None),
                    ChargeCodeCategory.level == 1,
                )
            else:
                if parent_id is not None:
                    query = query.filter(ChargeCodeCategory.parent_id == parent_id)
                if level is not None:
                    query = query.filter(ChargeCodeCategory.level == level)

            categories = query.order_by(ChargeCodeCategory.name).all()
            self.logger.debug(
                f"Fetched {len(categories)} categories for parent_id={parent_id}, level={level}"
            )
            return categories
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code categories: {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def get_category_path(self, category_id: Optional[int]) -> List[ChargeCodeCategory]:
        """
        Retrieves the full path (list of category objects from root to specific category)
        for a given category_id.
        """
        path = []
        if category_id is None:
            return path

        session = db_manager.get_session()
        try:
            current_cat_id = category_id
            while current_cat_id is not None:
                category = (
                    session.query(ChargeCodeCategory)
                    .filter(ChargeCodeCategory.category_id == current_cat_id)
                    .first()
                )
                if category:
                    path.insert(0, category)  # Prepend to get root -> child order
                    current_cat_id = category.parent_id
                else:
                    break  # Should not happen if category_id is valid
            return path
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching category path for ID {category_id}: {e}", exc_info=True
            )
            return []  # Return empty path on error
        finally:
            session.close()

    # CRUD for ChargeCodeCategory itself (basic versions, can be expanded)
    def create_charge_code_category(
        self, category_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[ChargeCodeCategory]]:
        session = db_manager.get_session()
        try:
            name = category_data.get("name", "").strip()
            level = category_data.get("level")
            parent_id = category_data.get("parent_id")

            if not name:
                return False, "Category name is required.", None
            if level is None:
                return False, "Category level is required.", None
            # Add more validation (e.g., name uniqueness at same level under same parent)

            new_category = ChargeCodeCategory(
                name=name,
                level=level,
                parent_id=parent_id,
                is_active=category_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_category)
            session.commit()
            session.refresh(new_category)
            self.logger.info(
                f"Charge Code Category '{new_category.name}' created by {current_user_id}."
            )
            return True, "Category created successfully.", new_category
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error creating charge code category: {e}", exc_info=True
            )
            return False, f"Failed to create category: {e}", None
        finally:
            session.close()
