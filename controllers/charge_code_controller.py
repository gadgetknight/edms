# controllers/charge_code_controller.py
"""
EDSI Veterinary Management System - Charge Code Controller
Version: 1.1.3
Purpose: Business logic for charge code and charge code category operations.
         - Added get_category_by_id method.
         - Corrected get_charge_code_by_id to use ChargeCode.id as primary key.
Last Updated: June 4, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.3 (2025-06-04):
    - Added `get_category_by_id` method to fetch a single category by its ID,
      as required by UserManagementScreen.
    - Modified `get_charge_code_by_id` to filter by `ChargeCode.id` (assuming 'id'
      is the current primary key attribute on the ChargeCode model) instead of
      `ChargeCode.charge_code_id` to resolve an AttributeError.
- v1.1.2 (2025-06-03):
    - Modified `get_all_charge_code_categories_hierarchical` to remove the
      `active_filter` parameter. It now always fetches all Level 1 categories
      (active and inactive) and their children. Filtering logic is handled by the view.
- v1.1.1 (2025-06-03):
    - Added `toggle_charge_code_category_status` method to specifically handle
      activating/deactivating ChargeCodeCategory items.
- v1.1.0 (2025-06-03):
    - Added full CRUD operations and validation for ChargeCodeCategory.
# ... (previous changelog entries)
"""

import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session, joinedload, aliased, selectinload
from sqlalchemy import or_, func, exc as sqlalchemy_exc, and_

from config.database_config import db_manager
from models import ChargeCode, ChargeCodeCategory  # Assuming from models package


class ChargeCodeController:
    """Controller for charge code and charge code category operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # --- ChargeCode Methods ---
    def validate_charge_code_data(
        self,
        charge_data: dict,
        is_new: bool = True,
        charge_code_id_to_ignore: Optional[
            int
        ] = None,  # Added charge_code_id_to_ignore for updates
    ) -> Tuple[bool, List[str]]:
        errors = []
        code = charge_data.get("code", "").strip()
        description = charge_data.get("description", "").strip()
        standard_charge_str = str(charge_data.get("standard_charge", "")).strip()

        if not code:
            errors.append("Charge Code (Code) is required.")
        elif len(code) > 20:
            errors.append("Charge Code (Code) cannot exceed 20 characters.")

        # Validate code uniqueness
        if code:  # Only check if code is provided
            session = db_manager.get_session()
            try:
                query = session.query(ChargeCode).filter(
                    ChargeCode.code.collate("NOCASE") == code.upper()
                )
                if not is_new and charge_code_id_to_ignore is not None:
                    # Assuming the PK is 'id' for ChargeCode based on previous context
                    query = query.filter(
                        ChargeCode.id != charge_code_id_to_ignore
                    )  # Use .id
                if query.first():
                    errors.append(f"Charge Code '{code.upper()}' already exists.")
            finally:
                if session:
                    session.close()

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
        if (
            alternate_code is not None and len(str(alternate_code).strip()) > 50
        ):  # check for strip()
            errors.append("Alternate Code cannot exceed 50 characters.")

        if "taxable" in charge_data and not isinstance(
            charge_data.get("taxable"), bool
        ):
            errors.append("Taxable field must be a true/false value.")

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
                # Removed active check for category here as per original v1.1.2 logic
                # Dialog might handle this if needed, or a separate business rule
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(
                    f"Error validating category_id '{category_id}': {e}", exc_info=True
                )
                errors.append("Database error validating category.")
            finally:
                if session:
                    session.close()
        elif (
            "category_id" not in charge_data
        ):  # If category_id is entirely missing from data dict
            errors.append("Category selection is required.")

        return not errors, errors

    def create_charge_code(
        self, charge_data: dict, current_user_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ChargeCode]]:
        # Pass None for charge_code_id_to_ignore as it's a new record
        is_valid, errors = self.validate_charge_code_data(
            charge_data, is_new=True, charge_code_id_to_ignore=None
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_charge_code = ChargeCode(
                code=charge_data["code"].strip().upper(),
                alternate_code=(
                    (charge_data.get("alternate_code", "").strip().upper() or None)
                    if charge_data.get("alternate_code") is not None
                    else None
                ),
                description=charge_data["description"].strip(),
                category_id=charge_data.get("category_id"),
                standard_charge=Decimal(str(charge_data["standard_charge"]).strip()),
                is_active=charge_data.get("is_active", True),
                taxable=charge_data.get("taxable", False),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_charge_code)
            session.commit()
            session.refresh(new_charge_code)
            # Assuming ChargeCode PK is 'id'
            self.logger.info(
                f"Charge Code '{new_charge_code.code}' created (ID: {new_charge_code.id}) by {current_user_id}."
            )
            return True, "Charge code created successfully.", new_charge_code
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating charge code: {str(ie.orig)}", exc_info=True
            )
            if "UNIQUE constraint failed: charge_codes.code" in str(ie.orig).lower():
                return (
                    False,
                    f"Charge Code '{charge_data['code'].strip().upper()}' already exists.",
                    None,
                )
            return False, f"Database integrity error: {str(ie.orig)}", None
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating charge code: {e}", exc_info=True)
            return False, f"Failed to create charge code: {str(e)}", None
        finally:
            if session:
                session.close()

    def get_charge_code_by_id(
        self, charge_code_pk_value: int
    ) -> Optional[ChargeCode]:  # Parameter is the PK value
        session = db_manager.get_session()
        try:
            # MODIFIED: Filter by ChargeCode.id (assuming 'id' is the PK)
            return (
                session.query(ChargeCode)
                .options(joinedload(ChargeCode.category))
                .filter(ChargeCode.id == charge_code_pk_value)
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code by ID {charge_code_pk_value}: {e}",
                exc_info=True,
            )
            return None
        finally:
            if session:
                session.close()

    def get_charge_code_by_code(self, code: str) -> Optional[ChargeCode]:
        session = db_manager.get_session()
        try:
            return (
                session.query(ChargeCode)
                .options(joinedload(ChargeCode.category))
                .filter(
                    ChargeCode.code.collate("NOCASE") == code.upper()
                )  # Made collate explicit & upper
                .first()
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code by code '{code}': {e}", exc_info=True
            )
            return None
        finally:
            if session:
                session.close()

    def get_all_charge_codes(
        self, search_term: str = "", status_filter: str = "all"
    ) -> List[ChargeCode]:
        session = db_manager.get_session()
        try:
            category_alias = aliased(ChargeCodeCategory)
            query = session.query(ChargeCode).options(
                joinedload(ChargeCode.category)
            )  # Eager load category

            if status_filter == "active":
                query = query.filter(ChargeCode.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(ChargeCode.is_active == False)

            # Ensure outerjoin is correctly linking ChargeCode.category relationship
            query = query.outerjoin(category_alias, ChargeCode.category)

            if search_term:
                like_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        ChargeCode.code.ilike(like_pattern),
                        ChargeCode.alternate_code.ilike(like_pattern),
                        ChargeCode.description.ilike(like_pattern),
                        category_alias.name.ilike(like_pattern),
                    )
                )
            query = query.order_by(
                category_alias.name.asc().nullsfirst(), ChargeCode.code.asc()
            )
            return query.all()
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all charge codes: {e}", exc_info=True)
            return []
        finally:
            if session:
                session.close()

    def update_charge_code(
        self,
        charge_code_pk_value: int,  # PK value, likely 'id'
        charge_data: dict,
        current_user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            charge_code_to_update = (
                session.query(ChargeCode)
                .filter(ChargeCode.id == charge_code_pk_value)  # Use .id
                .first()
            )
            if not charge_code_to_update:
                return False, "Charge code not found."

            self.logger.info(
                f"--- Updating Charge Code ID (PK): {charge_code_pk_value} ---"
            )
            self.logger.info(f"Received charge_data for update: {charge_data}")

            # Prepare data for validation, ensuring current PK is used for uniqueness check if code isn't changing
            validation_data = charge_data.copy()
            # 'code' is part of charge_data if it's being changed, otherwise use existing for validation
            if "code" not in validation_data:
                validation_data["code"] = charge_code_to_update.code

            is_valid, errors = self.validate_charge_code_data(
                validation_data,
                is_new=False,
                charge_code_id_to_ignore=charge_code_pk_value,
            )
            if not is_valid:
                self.logger.warning(
                    f"Validation failed for charge code PK {charge_code_pk_value}: {errors}"
                )
                return False, "Validation failed: " + "; ".join(errors)

            # Apply changes
            if "code" in charge_data:  # Only update if present in data
                charge_code_to_update.code = charge_data["code"].strip().upper()
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
                except (
                    InvalidOperation
                ):  # Should be caught by validation, but as safeguard
                    self.logger.error(
                        f"Invalid standard_charge value during update: {charge_data['standard_charge']}"
                    )
                    return False, "Invalid Standard Charge value provided for update."
            if "alternate_code" in charge_data:  # Handle if key exists
                alt_code = charge_data.get("alternate_code")
                charge_code_to_update.alternate_code = (
                    (alt_code.strip().upper() or None)
                    if isinstance(alt_code, str)
                    else None
                )

            # Allow category_id to be set to None
            if "category_id" in charge_data:
                charge_code_to_update.category_id = charge_data.get("category_id")

            # These are usually handled by toggle_charge_code_status
            if "is_active" in charge_data:
                charge_code_to_update.is_active = charge_data["is_active"]
            if "taxable" in charge_data:
                charge_code_to_update.taxable = charge_data["taxable"]

            charge_code_to_update.modified_by = current_user_id
            # charge_code_to_update.modified_date = datetime.utcnow() # BaseModel handles this

            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code_to_update.code}' (ID: {charge_code_pk_value}) updated by {current_user_id}."
            )
            return True, "Charge code updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating charge code ID {charge_code_pk_value}: {str(ie.orig)}",
                exc_info=True,
            )
            if "UNIQUE constraint failed: charge_codes.code" in str(ie.orig).lower():
                return (
                    False,
                    f"Charge Code '{charge_data.get('code', '').strip().upper()}' already exists.",
                )
            return False, f"Database integrity error: {str(ie.orig)}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating charge code ID {charge_code_pk_value}: {e}",
                exc_info=True,
            )
            return False, f"Failed to update charge code: {str(e)}"
        finally:
            if session:
                session.close()

    def toggle_charge_code_status(
        self,
        charge_code_pk_value: int,
        current_user_id: Optional[str] = None,  # Use PK value
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            charge_code = (
                session.query(ChargeCode)
                .filter(ChargeCode.id == charge_code_pk_value)  # Use .id
                .first()
            )
            if not charge_code:
                return False, "Charge code not found."

            charge_code.is_active = not charge_code.is_active
            charge_code.modified_by = current_user_id
            # charge_code.modified_date = datetime.utcnow() # BaseModel handles this
            new_status = "active" if charge_code.is_active else "inactive"
            session.commit()
            self.logger.info(
                f"Charge Code '{charge_code.code}' (ID: {charge_code_pk_value}) status changed to {new_status} by {current_user_id}."
            )
            return True, f"Charge code '{charge_code.code}' status set to {new_status}."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error toggling status for charge code ID {charge_code_pk_value}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle charge code status: {str(e)}"
        finally:
            if session:
                session.close()

    # --- ChargeCodeCategory Management Methods ---

    # ADDED method: get_category_by_id
    def get_category_by_id(self, category_id: int) -> Optional[ChargeCodeCategory]:
        session = db_manager.get_session()
        try:
            category = (
                session.query(ChargeCodeCategory)
                .options(
                    joinedload(ChargeCodeCategory.parent)
                )  # Optional: load parent for context
                .filter(ChargeCodeCategory.category_id == category_id)
                .first()
            )
            return category
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching category by ID {category_id}: {e}", exc_info=True
            )
            return None
        finally:
            if session:
                session.close()

    def validate_charge_code_category_data(
        self,
        category_data: dict,
        is_new: bool = True,
        category_id_to_ignore: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        name = category_data.get("name", "").strip()
        level = category_data.get("level")
        parent_id = category_data.get("parent_id")

        if not name:
            errors.append("Category/Process name is required.")
        elif len(name) > 100:
            errors.append("Category/Process name cannot exceed 100 characters.")

        if level not in [1, 2]:
            errors.append("Level must be 1 (for Category) or 2 (for Process).")

        if level == 1 and parent_id is not None:
            errors.append("A Level 1 Category cannot have a parent.")
        if level == 2 and parent_id is None:
            errors.append("A Level 2 Process must have a parent Category.")

        if name and level is not None:
            session = db_manager.get_session()
            try:
                query = session.query(ChargeCodeCategory.category_id).filter(
                    ChargeCodeCategory.name.collate("NOCASE") == name,
                    ChargeCodeCategory.level == level,
                )
                if parent_id:
                    query = query.filter(ChargeCodeCategory.parent_id == parent_id)
                else:
                    query = query.filter(ChargeCodeCategory.parent_id.is_(None))

                if not is_new and category_id_to_ignore is not None:
                    query = query.filter(
                        ChargeCodeCategory.category_id != category_id_to_ignore
                    )

                if query.first():
                    type_name = "Process" if level == 2 else "Category"
                    parent_info = f" under the selected parent" if parent_id else ""
                    errors.append(
                        f"{type_name} name '{name}' already exists{parent_info}."
                    )
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(
                    f"DB error validating category name uniqueness: {e}", exc_info=True
                )
                errors.append("Database error during name validation.")
            finally:
                if session:
                    session.close()
        return not errors, errors

    def create_charge_code_category(
        self, category_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str, Optional[ChargeCodeCategory]]:
        self.logger.info(
            f"Attempting to create charge code category with data: {category_data}"
        )
        is_valid, errors = self.validate_charge_code_category_data(
            category_data, is_new=True
        )
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_category = ChargeCodeCategory(
                name=category_data["name"].strip(),
                level=category_data["level"],
                parent_id=category_data.get("parent_id"),
                is_active=category_data.get("is_active", True),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_category)
            session.commit()
            session.refresh(new_category)
            cat_type = "Process" if new_category.level == 2 else "Category"
            self.logger.info(
                f"Charge Code {cat_type} '{new_category.name}' (ID: {new_category.category_id}, Level: {new_category.level}, ParentID: {new_category.parent_id}) created by {current_user_id}."
            )
            return True, f"{cat_type} created successfully.", new_category
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating charge code category: {str(ie.orig)}",
                exc_info=True,
            )
            return False, f"Database integrity error: {str(ie.orig)}", None
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error creating charge code category: {e}", exc_info=True
            )
            return False, f"Failed to create category/process: {str(e)}", None
        finally:
            if session:
                session.close()

    def update_charge_code_category(
        self, category_id: int, category_data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str]:
        self.logger.info(
            f"Attempting to update category ID {category_id} with data: {category_data}"
        )
        session = db_manager.get_session()
        try:
            category_to_update = (
                session.query(ChargeCodeCategory)
                .filter(ChargeCodeCategory.category_id == category_id)
                .first()
            )
            if not category_to_update:
                return False, "Category/Process not found."

            # Prepare validation_data using current values if not provided in category_data for update
            validation_data = {
                "name": category_data.get("name", category_to_update.name).strip(),
                "level": category_to_update.level,  # Level and parent typically not changed in simple edit
                "parent_id": category_to_update.parent_id,
            }

            is_valid, errors = self.validate_charge_code_category_data(
                validation_data, is_new=False, category_id_to_ignore=category_id
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            changed = False
            if (
                "name" in category_data
                and category_to_update.name != category_data["name"].strip()
            ):
                category_to_update.name = category_data["name"].strip()
                changed = True

            # is_active is handled by toggle_charge_code_category_status
            if (
                "is_active" in category_data
                and category_to_update.is_active != category_data["is_active"]
            ):
                category_to_update.is_active = category_data["is_active"]
                changed = True

            if changed:
                category_to_update.modified_by = current_user_id
                # category_to_update.modified_date = datetime.utcnow() # BaseModel handles this
                session.commit()
                cat_type = "Process" if category_to_update.level == 2 else "Category"
                self.logger.info(
                    f"Charge Code {cat_type} '{category_to_update.name}' (ID: {category_id}) updated by {current_user_id}."
                )
                return True, f"{cat_type} updated successfully."
            else:
                return True, "No changes detected to update."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating category ID {category_id}: {str(ie.orig)}",
                exc_info=True,
            )
            return False, f"Database integrity error: {str(ie.orig)}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating category ID {category_id}: {e}", exc_info=True
            )
            return False, f"Failed to update category/process: {str(e)}"
        finally:
            if session:
                session.close()

    def toggle_charge_code_category_status(
        self, category_id: int, current_user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        category = None
        try:
            category = (
                session.query(ChargeCodeCategory)
                .filter(ChargeCodeCategory.category_id == category_id)
                .first()
            )
            if not category:
                return False, "Category/Process not found."
            item_type = "Process" if category.level == 2 else "Category"
            original_name = category.name
            category.is_active = not category.is_active
            category.modified_by = current_user_id
            # category.modified_date = datetime.utcnow() # BaseModel handles this
            session.commit()
            new_status_str = "active" if category.is_active else "inactive"
            self.logger.info(
                f"{item_type} '{original_name}' (ID: {category.category_id}) status changed to {new_status_str} by {current_user_id}."
            )
            return (
                True,
                f"{item_type} '{original_name}' status set to {new_status_str}.",
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            if session:
                session.rollback()  # Ensure rollback on error
            err_item_type = "Category/Process"
            err_name = f"ID {category_id}"
            if category:  # Check if category object was fetched before error
                err_item_type = "Process" if category.level == 2 else "Category"
                err_name = category.name
            self.logger.error(
                f"Error toggling status for {err_item_type} {err_name}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle {err_item_type} status: {str(e)}"
        finally:
            if session:
                session.close()

    def delete_charge_code_category(
        self, category_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        category_to_delete = None
        try:
            category_to_delete = (
                session.query(ChargeCodeCategory)
                .filter(ChargeCodeCategory.category_id == category_id)
                .first()
            )
            if not category_to_delete:
                return False, "Category/Process not found."

            linked_charge_codes_count = (
                session.query(ChargeCode)
                .filter(ChargeCode.category_id == category_id)
                .count()
            )
            if linked_charge_codes_count > 0:
                msg = f"Cannot delete '{category_to_delete.name}'. It is assigned to {linked_charge_codes_count} charge code(s)."
                self.logger.warning(msg)
                return False, msg

            if category_to_delete.level == 1:  # If it's a Level 1 Category
                children_count = (
                    session.query(ChargeCodeCategory)
                    .filter(ChargeCodeCategory.parent_id == category_id)
                    .count()
                )
                if children_count > 0:
                    msg = f"Cannot delete Category '{category_to_delete.name}'. It has {children_count} child Process(es). Delete children first."
                    self.logger.warning(msg)
                    return False, msg

            cat_type_name = "Process" if category_to_delete.level == 2 else "Category"
            deleted_name = category_to_delete.name
            session.delete(category_to_delete)
            session.commit()
            self.logger.info(
                f"Charge Code {cat_type_name} '{deleted_name}' (ID: {category_id}) deleted by {current_user_id}."
            )
            return True, f"{cat_type_name} '{deleted_name}' deleted successfully."
        except sqlalchemy_exc.SQLAlchemyError as e:  # Broader catch for DB errors
            if session:
                session.rollback()
            self.logger.error(
                f"Error deleting category ID {category_id}: {e}", exc_info=True
            )
            name_for_error = (
                category_to_delete.name if category_to_delete else f"ID {category_id}"
            )
            # More specific check for IntegrityError which often includes foreign key issues
            if isinstance(e, sqlalchemy_exc.IntegrityError):
                return (
                    False,
                    f"Cannot delete '{name_for_error}'. It might still be referenced by other records. Details: {e.orig}",
                )
            return (
                False,
                f"Failed to delete category/process due to a database error: {str(e)}",
            )
        finally:
            if session:
                session.close()

    def get_all_charge_code_categories_hierarchical(
        self,
    ) -> List[ChargeCodeCategory]:
        """Fetches all Level 1 categories, with their Level 2 children (processes) eager-loaded."""
        session = db_manager.get_session()
        try:
            level1_categories = (
                session.query(ChargeCodeCategory)
                .filter(
                    ChargeCodeCategory.parent_id.is_(
                        None
                    ),  # Ensure it's a top-level category
                    ChargeCodeCategory.level == 1,  # Explicitly check level 1
                )
                .options(
                    selectinload(ChargeCodeCategory.children)
                )  # Eager load children
                .order_by(ChargeCodeCategory.name)
                .all()
            )
            self.logger.debug(
                f"Fetched {len(level1_categories)} top-level categories with all children for management UI."
            )
            return level1_categories
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching hierarchical charge code categories: {e}",
                exc_info=True,
            )
            return []
        finally:
            if session:
                session.close()

    def get_charge_code_categories(  # This is likely for populating dropdowns
        self,
        parent_id: Optional[int] = None,
        level: Optional[int] = None,
        active_only: bool = True,  # Added active_only filter
    ) -> List[ChargeCodeCategory]:
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCodeCategory)
            if active_only:
                query = query.filter(ChargeCodeCategory.is_active == True)

            if parent_id is None and level == 1:  # Explicitly for Level 1 categories
                query = query.filter(
                    ChargeCodeCategory.parent_id.is_(None),
                    ChargeCodeCategory.level == 1,
                )
            else:  # For other cases, like fetching children or specific level
                if parent_id is not None:
                    query = query.filter(ChargeCodeCategory.parent_id == parent_id)
                if level is not None:
                    query = query.filter(ChargeCodeCategory.level == level)

            categories = query.order_by(ChargeCodeCategory.name).all()
            self.logger.debug(
                f"Fetched {len(categories)} categories for parent_id={parent_id}, level={level}, active_only={active_only}"
            )
            return categories
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching charge code categories: {e}", exc_info=True
            )
            return []
        finally:
            if session:
                session.close()

    def get_category_path(self, category_id: Optional[int]) -> List[Dict[str, Any]]:
        """
        Retrieves the hierarchical path for a given category ID.
        Returns a list of dictionaries, each with 'id' and 'name'.
        """
        path_for_display = []
        if category_id is None:
            return path_for_display

        current_cat_id = category_id
        # Use a single session for all queries in this path lookup
        session = db_manager.get_session()
        try:
            while current_cat_id is not None:
                category = (
                    session.query(
                        ChargeCodeCategory.category_id,
                        ChargeCodeCategory.name,
                        ChargeCodeCategory.parent_id,
                    )
                    .filter(ChargeCodeCategory.category_id == current_cat_id)
                    .first()
                )
                if category:
                    path_for_display.insert(
                        0, {"id": category.category_id, "name": category.name}
                    )
                    current_cat_id = category.parent_id
                else:
                    self.logger.warning(
                        f"Could not find category part with ID: {current_cat_id} while building path for {category_id}."
                    )
                    break  # Category in path not found
            return path_for_display
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching category path for ID {category_id}: {e}", exc_info=True
            )
            return []  # Return empty path on error
        finally:
            if session:
                session.close()
