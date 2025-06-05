# controllers/owner_controller.py
"""
EDSI Veterinary Management System - Owner Controller
Version: 1.3.5
Purpose: Business logic for owner master file operations.
         - Added eager loading for Owner.state in get_all_master_owners.
Last Updated: June 4, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.3.5 (2025-06-04):
    - In `get_all_master_owners`, added `options(joinedload(Owner.state))`
      to eagerly load the related StateProvince object, preventing
      DetachedInstanceError when accessing owner.state in views.
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
import re
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session, joinedload  # Ensure joinedload is imported
from sqlalchemy import or_, func, exc as sqlalchemy_exc

from config.database_config import db_manager
from models import (
    Owner,
    StateProvince,
    HorseOwner,
)  # Assuming models are in a package 'models'
from datetime import datetime


class OwnerController:
    """Controller for owner master file operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_master_owners(self, include_inactive: bool = False) -> List[Owner]:
        session = db_manager.get_session()
        try:
            # MODIFIED: Added joinedload for Owner.state relationship
            query = session.query(Owner).options(joinedload(Owner.state))

            if not include_inactive:
                query = query.filter(Owner.is_active == True)

            owners = query.order_by(
                Owner.farm_name, Owner.last_name, Owner.first_name
            ).all()
            self.logger.info(
                f"Retrieved {len(owners)} master owners (include_inactive={include_inactive})."
            )
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
                    display_text = f"Owner ID {owner_id}"  # Fallback if no names
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
                .options(joinedload(Owner.state))  # Eager load state here too
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
        self,
        owner_data: dict,
        is_new: bool = True,
        owner_id_to_ignore: Optional[int] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        first_name = owner_data.get("first_name")
        last_name = owner_data.get("last_name")
        farm_name = owner_data.get("farm_name")
        account_number_val = owner_data.get("account_number")

        # It's okay if one of them is provided, but not strictly required if others are.
        # Dialog might enforce this more strictly if needed.
        # if not first_name and not last_name and not farm_name:
        #     errors.append(
        #         "It's recommended to provide at least one of: First Name, Last Name, or Farm Name."
        #     )

        if not owner_data.get(
            "address_line1", ""
        ).strip():  # Check for empty string too
            errors.append("Address Line 1 is required.")
        if not owner_data.get("city", "").strip():
            errors.append("City is required.")
        if not owner_data.get("state_code", "").strip():
            errors.append("State is required.")
        if not owner_data.get("zip_code", "").strip():
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
            if value is not None and isinstance(value, str) and len(value) > max_len:
                errors.append(
                    f"{field.replace('_', ' ').title()} cannot exceed {max_len} characters."
                )

        email_val = owner_data.get("email")
        if email_val and email_val.strip():  # only validate if not empty
            if not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_val
            ):
                errors.append("Invalid email format.")

        if account_number_val and account_number_val.strip():
            session = db_manager.get_session()
            try:
                query = session.query(Owner).filter(
                    Owner.account_number.collate("NOCASE") == account_number_val.strip()
                )
                if not is_new and owner_id_to_ignore is not None:
                    query = query.filter(Owner.owner_id != owner_id_to_ignore)

                existing_owner_with_account = query.first()
                if existing_owner_with_account:
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

        credit_limit_str = owner_data.get("credit_limit")
        if credit_limit_str is not None and str(credit_limit_str).strip() != "":
            try:
                credit_limit_decimal = Decimal(str(credit_limit_str))
                if credit_limit_decimal < Decimal("0.00"):
                    errors.append("Credit Limit cannot be negative.")
            except InvalidOperation:
                errors.append("Credit Limit must be a valid number (e.g., 1000.00).")

        return not errors, errors

    def create_master_owner(
        self, owner_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Owner]]:
        is_valid, errors = self.validate_owner_data(owner_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_owner_params = {}
            allowed_keys = [
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
                "balance",
                "service_charge_rate",
                "discount_rate",
                "notes",
            ]
            for key in allowed_keys:
                if key in owner_data:
                    value = owner_data[key]
                    if isinstance(value, str):
                        new_owner_params[key] = value.strip() or None
                    elif (
                        key == "credit_limit"
                        and value is not None
                        and str(value).strip() != ""
                    ):
                        try:
                            new_owner_params[key] = Decimal(str(value))
                        except InvalidOperation:
                            self.logger.warning(
                                f"Invalid decimal for credit_limit: {value}. Setting to None."
                            )
                            new_owner_params[key] = (
                                None  # Or raise error/return validation message
                            )
                    elif (
                        key == "balance"
                        and value is not None
                        and str(value).strip() != ""
                    ):
                        try:
                            new_owner_params[key] = Decimal(str(value))
                        except InvalidOperation:
                            new_owner_params[key] = Decimal("0.00")
                    elif (
                        key in ["service_charge_rate", "discount_rate"]
                        and value is not None
                        and str(value).strip() != ""
                    ):
                        try:
                            new_owner_params[key] = Decimal(str(value))
                        except InvalidOperation:
                            new_owner_params[key] = None
                    else:
                        new_owner_params[key] = value

            # Ensure balance defaults to 0.00 if not provided or invalid
            if new_owner_params.get("balance") is None:
                new_owner_params["balance"] = Decimal("0.00")

            # Ensure is_active defaults to True if not provided
            if new_owner_params.get("is_active") is None:
                new_owner_params["is_active"] = True

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

            # Use original account number for validation if it's not being changed
            original_account_number = owner.account_number
            if (
                "account_number" in owner_data
                and owner_data["account_number"] != original_account_number
            ):
                # If account number is changing, validate it against others
                is_valid, errors = self.validate_owner_data(
                    owner_data, is_new=False, owner_id_to_ignore=owner_id
                )
            else:
                # If account number not in data or not changing, validate other fields
                # but don't re-check account uniqueness against itself
                temp_data_for_validation = owner_data.copy()
                temp_data_for_validation.pop(
                    "account_number", None
                )  # remove account number for this specific validation scenario
                is_valid, errors = self.validate_owner_data(
                    temp_data_for_validation, is_new=False, owner_id_to_ignore=owner_id
                )

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
                "service_charge_rate",
                "discount_rate",
                "notes",
            ]

            for key in updatable_fields:
                if key in owner_data:
                    value = owner_data[key]
                    if isinstance(value, str):
                        # Allow setting required fields to empty if that's the intent, validation handles it
                        setattr(
                            owner,
                            key,
                            (
                                value.strip() or None
                                if key
                                not in [
                                    "last_name",
                                    "address_line1",
                                    "city",
                                    "state_code",
                                    "zip_code",
                                ]
                                else value.strip()
                            ),
                        )
                    elif (
                        key
                        in [
                            "credit_limit",
                            "balance",
                            "service_charge_rate",
                            "discount_rate",
                        ]
                        and value is not None
                    ):
                        if (
                            str(value).strip() == ""
                        ):  # Treat empty string for numerics as None or default
                            if key == "balance":
                                setattr(owner, key, Decimal("0.00"))
                            else:
                                setattr(owner, key, None)
                        else:
                            try:
                                setattr(owner, key, Decimal(str(value)))
                            except InvalidOperation:
                                self.logger.warning(
                                    f"Invalid decimal value for {key}: {value} during update. Field not updated."
                                )
                    else:
                        setattr(owner, key, value)

            owner.modified_by = current_user
            # owner.modified_date = datetime.utcnow() # Handled by SQLAlchemy onupdate in BaseModel

            session.commit()
            # ... (logging as before)
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
        except sqlalchemy_exc.SQLAlchemyError as e:  # Catch broader SQLAlchemy errors
            session.rollback()
            self.logger.error(
                f"Error deleting master owner ID {owner_id_to_delete}: {e}",
                exc_info=True,
            )
            # Check if it's an IntegrityError (e.g. foreign key constraint from other tables like Invoices)
            if isinstance(e, sqlalchemy_exc.IntegrityError):
                return (
                    False,
                    f"Cannot delete owner. It might be referenced by other records (e.g., invoices, payments). Details: {e.orig}",
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
            # Static billing terms, as they are not in the DB model explicitly
            billing_terms_list = [
                {"id": "NET30", "name": "Net 30 Days"},
                {"id": "NET15", "name": "Net 15 Days"},
                {"id": "NET60", "name": "Net 60 Days"},
                {"id": "COD", "name": "Cash on Delivery"},
                {"id": "PREPAID", "name": "Prepaid"},
                {"id": "EOM", "name": "End of Month"},
                {"id": "ONDELIVERY", "name": "Payment on Delivery"},
            ]
            return {"states": states, "billing_terms": billing_terms_list}
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owner form reference data: {e}", exc_info=True
            )
            return {"states": [], "billing_terms": []}
        finally:
            session.close()

    def toggle_owner_active_status(
        self, owner_id: int, current_user_id: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            owner = (
                session.query(OwnerModel)
                .filter(OwnerModel.owner_id == owner_id)
                .first()
            )
            if not owner:
                return False, "Owner not found."

            owner.is_active = not owner.is_active
            owner.modified_by = current_user_id
            # owner.modified_date = datetime.utcnow() # Should be handled by SQLAlchemy onupdate
            session.commit()
            status = "activated" if owner.is_active else "deactivated"
            self.logger.info(f"Owner ID {owner_id} {status} by {current_user_id}.")
            return True, f"Owner {status} successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error toggling active status for owner ID {owner_id}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle owner status: {e}"
        finally:
            session.close()
