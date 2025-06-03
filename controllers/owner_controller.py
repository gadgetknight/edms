# controllers/owner_controller.py
"""
EDSI Veterinary Management System - Owner Controller
Version: 1.3.4
Purpose: Business logic for owner master file operations.
         - Added missing 'import re' for email validation.
Last Updated: June 02, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.3.4 (2025-06-02):
    - Added `import re` to resolve NameError during email validation
      in `validate_owner_data`.
- v1.3.3 (2025-06-02):
    - Modified `validate_owner_data` to correctly handle optional fields that
      might be `None` before calling `len()` on them, preventing TypeError.
- v1.3.2 (2025-05-17):
    - Removed `country_name` from Owner instantiation/update and validation.
- v1.3.1 (2025-05-17):
    - Removed phone number requirement from `validate_owner_data`.
    - Added `mobile_phone` handling.
- v1.2.1 (2025-05-15): Removed credit_rating.
- v1.2.0 (2025-05-15): Added delete_master_owner method.
"""

import logging
import re  # ADDED for email validation
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation  # Added for create/update
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, exc as sqlalchemy_exc

from config.database_config import db_manager
from models import Owner, StateProvince, HorseOwner
from datetime import datetime


class OwnerController:
    """Controller for owner master file operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_master_owners(self, include_inactive: bool = False) -> List[Owner]:
        session = db_manager.get_session()
        try:
            query = session.query(Owner)
            if not include_inactive:
                query = query.filter(Owner.is_active == True)
            owners = query.order_by(
                Owner.farm_name, Owner.last_name, Owner.first_name
            ).all()
            return owners
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all master owners: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_all_owners_for_lookup(self, search_term: str = "") -> List[Dict[str, Any]]:
        session = db_manager.get_session()
        try:
            query = session.query(
                Owner.owner_id,
                Owner.first_name,
                Owner.last_name,
                Owner.farm_name,
                Owner.account_number,
            ).filter(Owner.is_active == True)

            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Owner.first_name.ilike(search_pattern),
                        Owner.last_name.ilike(search_pattern),
                        Owner.farm_name.ilike(search_pattern),
                        Owner.account_number.ilike(search_pattern),
                    )
                )

            owners_data = query.order_by(
                Owner.farm_name, Owner.last_name, Owner.first_name
            ).all()

            lookup_list = []
            for (
                owner_id,
                first_name,
                last_name,
                farm_name,
                account_number,
            ) in owners_data:
                name_parts = [name for name in [first_name, last_name] if name]
                individual_name = " ".join(name_parts)
                display_text = farm_name if farm_name else ""
                if individual_name:
                    display_text = (
                        f"{display_text} ({individual_name})"
                        if farm_name
                        else individual_name
                    )
                if not display_text:
                    display_text = "Unnamed Owner"
                if account_number:
                    display_text += f" [{account_number}]"
                lookup_list.append({"id": owner_id, "name_account": display_text})
            return lookup_list
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching owners for lookup: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_owner_by_id(self, owner_id: int) -> Optional[Owner]:
        session = db_manager.get_session()
        try:
            owner = (
                session.query(Owner)
                .options(joinedload(Owner.state))
                .filter(Owner.owner_id == owner_id)
                .first()
            )
            return owner
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owner by ID '{owner_id}': {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def validate_owner_data(
        self, owner_data: dict, is_new: bool = True
    ) -> Tuple[bool, List[str]]:
        errors = []
        first_name = owner_data.get("first_name")
        last_name = owner_data.get("last_name")
        farm_name = owner_data.get("farm_name")
        account_number_val = owner_data.get("account_number")

        if not first_name and not last_name and not farm_name:
            errors.append(
                "It's recommended to provide at least one of: First Name, Last Name, or Farm Name."
            )

        if not owner_data.get("address_line1"):
            errors.append("Address Line 1 is required.")
        if not owner_data.get("city"):
            errors.append("City is required.")
        if not owner_data.get("state_code"):
            errors.append("State is required.")
        if not owner_data.get("zip_code"):
            errors.append("Zip Code is required.")

        field_max_lengths = {
            "first_name": 50,
            "last_name": 50,
            "farm_name": 100,
            "address_line1": 100,
            "address_line2": 100,
            "city": 50,
            "zip_code": 20,
            "phone": 20,
            "mobile_phone": 20,
            "email": 100,
            "account_number": 20,
            "billing_terms": 50,
        }

        for field, max_len in field_max_lengths.items():
            value = owner_data.get(field)
            if value is not None and len(value) > max_len:
                errors.append(
                    f"{field.replace('_', ' ').title()} cannot exceed {max_len} characters."
                )

        email_val = owner_data.get("email")
        # MODIFIED: Check if re module is available (it is now, due to import)
        if email_val and not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_val
        ):
            errors.append("Invalid email format.")

        if is_new and account_number_val:
            session = db_manager.get_session()
            try:
                existing = (
                    session.query(Owner)
                    .filter(
                        Owner.account_number.collate("NOCASE") == account_number_val
                    )  # Case insensitive check for account number
                    .first()
                )
                if existing:
                    errors.append(
                        f"Account Number '{account_number_val}' already exists."
                    )
            except sqlalchemy_exc.SQLAlchemyError as e:
                self.logger.error(
                    f"DB error validating account_number: {e}", exc_info=True
                )
                errors.append("Error validating account number uniqueness.")
            finally:
                session.close()

        credit_limit = owner_data.get("credit_limit")
        if credit_limit is not None:
            if not isinstance(
                credit_limit, (Decimal, float, int)
            ):  # Check if it's a number type
                try:  # Attempt conversion if it's string-like from form
                    credit_limit_decimal = Decimal(str(credit_limit))
                    if credit_limit_decimal < Decimal("0.00"):
                        errors.append("Credit Limit cannot be negative.")
                except InvalidOperation:
                    errors.append("Credit Limit must be a valid number.")
            elif isinstance(
                credit_limit, (float, int)
            ):  # Convert to Decimal if float/int
                if Decimal(str(credit_limit)) < Decimal("0.00"):
                    errors.append("Credit Limit cannot be negative.")
            elif isinstance(credit_limit, Decimal):  # Already Decimal
                if credit_limit < Decimal("0.00"):
                    errors.append("Credit Limit cannot be negative.")

        return not errors, errors

    def create_master_owner(
        self, owner_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Owner]]:
        is_valid, errors = self.validate_owner_data(owner_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_owner_params = {
                key: owner_data.get(key)
                for key in [
                    "account_number",
                    "first_name",
                    "last_name",
                    "farm_name",
                    "address_line1",
                    "address_line2",
                    "city",
                    "state_code",
                    "zip_code",
                    "phone",
                    "mobile_phone",
                    "email",
                    "credit_limit",
                    "billing_terms",
                    "is_active",
                ]  # No filtering for None, controller handles None based on model nullability
            }
            # Ensure numeric fields are correctly typed if they come from a form as string
            if new_owner_params.get("credit_limit") is not None:
                try:
                    new_owner_params["credit_limit"] = Decimal(
                        str(new_owner_params["credit_limit"])
                    )
                except InvalidOperation:
                    self.logger.error(
                        f"Invalid credit_limit value during create: {new_owner_params['credit_limit']}"
                    )
                    return False, "Invalid Credit Limit value.", None

            new_owner = Owner(**new_owner_params)
            new_owner.created_by = current_user
            new_owner.modified_by = current_user

            session.add(new_owner)
            session.commit()
            session.refresh(new_owner)

            log_name_parts = [
                name for name in [new_owner.first_name, new_owner.last_name] if name
            ]
            log_individual_name = " ".join(log_name_parts)
            display_name_for_log = new_owner.farm_name if new_owner.farm_name else ""
            if log_individual_name:
                display_name_for_log = (
                    f"{display_name_for_log} ({log_individual_name})"
                    if new_owner.farm_name
                    else log_individual_name
                )
            if not display_name_for_log:
                display_name_for_log = f"Owner ID {new_owner.owner_id}"

            self.logger.info(
                f"Master Owner '{display_name_for_log}' (ID: {new_owner.owner_id}) created by {current_user}."
            )
            return True, "Owner created successfully.", new_owner
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError creating master owner: {ie.orig}", exc_info=True
            )
            if "UNIQUE constraint failed: owners.account_number" in str(
                ie.orig
            ).lower() and owner_data.get("account_number"):
                return (
                    False,
                    f"Account Number '{owner_data['account_number']}' already exists.",
                    None,
                )
            return False, f"Database integrity error: {ie.orig}", None
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating master owner: {e}", exc_info=True)
            return False, f"Failed to create owner: {e}", None
        finally:
            session.close()

    def update_master_owner(
        self, owner_id: int, owner_data: dict, current_user: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            owner = session.query(Owner).filter(Owner.owner_id == owner_id).first()
            if not owner:
                return False, f"Owner with ID {owner_id} not found."

            is_valid, errors = self.validate_owner_data(owner_data, is_new=False)
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            updatable_fields = [
                "account_number",
                "first_name",
                "last_name",
                "farm_name",
                "address_line1",
                "address_line2",
                "city",
                "state_code",
                "zip_code",
                "phone",
                "mobile_phone",
                "email",
                "is_active",
                "balance",
                "credit_limit",
                "billing_terms",
            ]

            for key in updatable_fields:
                if key in owner_data:
                    value = owner_data[key]
                    if key in ["credit_limit", "balance"] and value is not None:
                        try:
                            setattr(owner, key, Decimal(str(value)))
                        except InvalidOperation:
                            self.logger.warning(
                                f"Invalid decimal value for {key}: {value} during update. Skipping."
                            )
                    elif isinstance(value, str):
                        setattr(owner, key, value.strip() or None)
                    else:
                        setattr(owner, key, value)

            owner.modified_by = current_user
            owner.modified_date = datetime.utcnow()

            session.commit()

            log_name_parts = [
                name for name in [owner.first_name, owner.last_name] if name
            ]
            log_individual_name = " ".join(log_name_parts)
            display_name_for_log = owner.farm_name if owner.farm_name else ""
            if log_individual_name:
                display_name_for_log = (
                    f"{display_name_for_log} ({log_individual_name})"
                    if owner.farm_name
                    else log_individual_name
                )
            if not display_name_for_log:
                display_name_for_log = f"Owner ID {owner.owner_id}"

            self.logger.info(
                f"Master Owner '{display_name_for_log}' (ID: {owner.owner_id}) updated by {current_user}."
            )
            return True, "Owner updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            session.rollback()
            self.logger.error(
                f"IntegrityError updating owner ID {owner_id}: {ie.orig}", exc_info=True
            )
            if "UNIQUE constraint failed: owners.account_number" in str(
                ie.orig
            ).lower() and owner_data.get("account_number"):
                return (
                    False,
                    f"Account Number '{owner_data['account_number']}' already exists for another owner.",
                )
            return False, f"Database integrity error: {ie.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating master owner ID {owner_id}: {e}", exc_info=True
            )
            return False, f"Failed to update owner: {e}"
        finally:
            session.close()

    def delete_master_owner(
        self, owner_id_to_delete: int, current_admin_id: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            owner = (
                session.query(Owner)
                .filter(Owner.owner_id == owner_id_to_delete)
                .first()
            )
            if not owner:
                return False, f"Owner with ID {owner_id_to_delete} not found."

            linked_horses_count = (
                session.query(HorseOwner)
                .filter(HorseOwner.owner_id == owner_id_to_delete)
                .count()
            )
            if linked_horses_count > 0:
                self.logger.warning(
                    f"Attempt to delete owner ID {owner_id_to_delete} who is linked to {linked_horses_count} horse(s)."
                )
                return (
                    False,
                    f"Cannot delete owner. They are currently linked to {linked_horses_count} horse(s). Please unlink them from all horses first.",
                )

            owner_name_for_log_parts = [
                name
                for name in [owner.farm_name, owner.last_name, owner.first_name]
                if name
            ]
            owner_name_for_log = (
                " ".join(owner_name_for_log_parts) or f"ID {owner_id_to_delete}"
            )

            session.delete(owner)
            session.commit()
            self.logger.info(
                f"Master Owner '{owner_name_for_log}' (ID: {owner_id_to_delete}) permanently deleted by admin '{current_admin_id}'."
            )
            return True, f"Owner '{owner_name_for_log}' deleted successfully."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error deleting master owner ID {owner_id_to_delete}: {e}",
                exc_info=True,
            )
            if isinstance(e, sqlalchemy_exc.IntegrityError):
                return (
                    False,
                    f"Cannot delete owner. It might be in use or referenced by other records. ({e.orig})",
                )
            return False, f"Failed to delete owner due to a database error: {e}"
        finally:
            session.close()

    def get_owner_form_reference_data(self) -> Dict[str, List[Dict[str, Any]]]:
        session = db_manager.get_session()
        try:
            states_query = (
                session.query(
                    StateProvince.state_code,
                    StateProvince.state_name,
                    StateProvince.country_code,
                )
                .filter(StateProvince.is_active == True)
                .order_by(StateProvince.country_code, StateProvince.state_name)
                .all()
            )
            states = [
                {
                    "id": s.state_code,
                    "name": s.state_name,
                    "country_code": s.country_code,
                }
                for s in states_query
            ]
            return {"states": states}
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owner form reference data: {e}", exc_info=True
            )
            return {"states": []}
        finally:
            session.close()
