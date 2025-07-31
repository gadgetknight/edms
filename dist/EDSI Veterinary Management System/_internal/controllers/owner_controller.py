# controllers/owner_controller.py
"""
EDSI Veterinary Management System - Owner Controller
Version: 1.4.2
Purpose: Business logic for owner master file operations.
         Methods now accept an optional session parameter for transactional control.
Last Updated: July 15, 2025
Author: Gemini

Changelog:
- v1.4.2 (2025-07-15):
    - **BUG FIX**: Removed `_session.refresh(new_owner)` from `create_master_owner` method when `_close_session` is False.
      The `refresh` call was happening before the object was committed in the external session,
      causing `InvalidRequestError: Instance is not persistent within this Session`.
      `_session.refresh(new_owner)` is now only called if the session was opened and committed internally.
    - **BUG FIX**: Added explicit `str()` conversion and `if value is not None` checks before `.strip()`
      in `validate_owner_data` for fields like `address_line1`, `city`, `state_code`, `zip_code`, `email`
      to prevent `AttributeError: 'NoneType' object has no attribute 'strip'` when CSV cells are empty (None).
- v1.4.1 (2025-07-15):
    - **Refactor**: Modified all database-interacting methods (`get_all_master_owners`,
      `get_all_owners_for_lookup`, `get_owner_by_id`, `validate_owner_data`,
      `create_master_owner`, `update_master_owner`, `delete_master_owner`,
      `get_owner_form_reference_data`, `toggle_owner_active_status`)
      to accept an optional `session: Session` parameter.
    - If a session is provided, it is used; otherwise, a new session is obtained
      from `db_manager()`. This allows for external transaction management
      (e.g., from import scripts) and resolves `RuntimeError: DatabaseManager instance not set`.
    - `db_manager().close()` is now called only if the session was opened internally by the method.
- v1.4.0 (2025-06-05):
    - Modified `get_all_master_owners` to accept a string `status_filter` ('active',
      'inactive', 'all') for consistency with other controllers.
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
- v1.2.1 (2025-05-15): Removed credit_rating. - v1.2.0 (2025-05-15): Added delete_master_owner method.
"""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, exc as sqlalchemy_exc
from datetime import datetime

from config.database_config import db_manager
import models  # Import models for direct use


class OwnerController:
    """Controller for owner master file operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_master_owners(
        self, status_filter: str = "all", session: Optional[Session] = None
    ) -> List[models.Owner]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            query = _session.query(models.Owner).options(joinedload(models.Owner.state))

            if status_filter == "active":
                query = query.filter(models.Owner.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(models.Owner.is_active == False)

            owners = query.order_by(
                models.Owner.farm_name, models.Owner.last_name, models.Owner.first_name
            ).all()
            self.logger.info(
                f"Retrieved {len(owners)} master owners (status_filter={status_filter})."
            )
            return owners
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all master owners: {e}", exc_info=True)
            return []
        finally:
            if _close_session:
                _session.close()

    def get_all_owners_for_lookup(
        self, search_term: str = "", session: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            query = _session.query(
                models.Owner.owner_id,
                models.Owner.first_name,
                models.Owner.last_name,
                models.Owner.farm_name,
                models.Owner.account_number,
            ).filter(models.Owner.is_active == True)

            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        models.Owner.first_name.ilike(search_pattern),
                        models.Owner.last_name.ilike(search_pattern),
                        models.Owner.farm_name.ilike(search_pattern),
                        models.Owner.account_number.ilike(search_pattern),
                    )
                )

            owners_data = query.order_by(
                models.Owner.farm_name, models.Owner.last_name, models.Owner.first_name
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
                    display_text = f"Owner ID {owner_id}"
                if account_number:
                    display_text += f" [{account_number}]"
                lookup_list.append({"id": owner_id, "name_account": display_text})
            return lookup_list
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching owners for lookup: {e}", exc_info=True)
            return []
        finally:
            if _close_session:
                _session.close()

    def get_owner_by_id(
        self, owner_id: int, session: Optional[Session] = None
    ) -> Optional[models.Owner]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            owner = (
                _session.query(models.Owner)
                .options(joinedload(models.Owner.state))
                .filter(models.Owner.owner_id == owner_id)
                .first()
            )
            return owner
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching owner by ID '{owner_id}': {e}", exc_info=True
            )
            return None
        finally:
            if _close_session:
                _session.close()

    def validate_owner_data(
        self,
        owner_data: dict,
        is_new: bool = True,
        owner_id_to_ignore: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        first_name = owner_data.get("first_name")
        last_name = owner_data.get("last_name")
        farm_name = owner_data.get("farm_name")
        account_number_val = owner_data.get("account_number")

        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            # Explicitly check if values are None before calling .strip()
            if not (
                owner_data.get("address_line1")
                and str(owner_data["address_line1"]).strip()
            ):
                errors.append("Address Line 1 is required.")
            if not (owner_data.get("city") and str(owner_data["city"]).strip()):
                errors.append("City is required.")
            if not (
                owner_data.get("state_code") and str(owner_data["state_code"]).strip()
            ):
                errors.append("State is required.")
            if not (owner_data.get("zip_code") and str(owner_data["zip_code"]).strip()):
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
                if (
                    value is not None
                    and isinstance(value, str)
                    and len(value) > max_len
                ):
                    errors.append(
                        f"{field.replace('_', ' ').title()} cannot exceed {max_len} characters."
                    )

            email_val = owner_data.get("email")
            if (
                email_val and str(email_val).strip()
            ):  # Ensure it's a string before strip
                if not re.match(
                    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    str(email_val).strip(),
                ):
                    errors.append("Invalid email format.")

            if account_number_val and str(account_number_val).strip():
                query = _session.query(models.Owner).filter(
                    models.Owner.account_number.collate("NOCASE")
                    == str(account_number_val).strip()
                )
                if not is_new and owner_id_to_ignore is not None:
                    query = query.filter(models.Owner.owner_id != owner_id_to_ignore)

                existing_owner_with_account = query.first()
                if existing_owner_with_account:
                    errors.append(
                        f"Account Number '{account_number_val}' already exists."
                    )

            credit_limit_str = owner_data.get("credit_limit")
            if credit_limit_str is not None and str(credit_limit_str).strip() != "":
                try:
                    credit_limit_decimal = Decimal(str(credit_limit_str))
                    if credit_limit_decimal < Decimal("0.00"):
                        errors.append("Credit Limit cannot be negative.")
                except InvalidOperation:
                    errors.append(
                        "Credit Limit must be a valid number (e.g., 1000.00)."
                    )

            return not errors, errors
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"DB error validating owner data: {e}", exc_info=True)
            errors.append("Database error during validation.")
            return False, errors
        finally:
            if _close_session:
                _session.close()

    def create_master_owner(
        self, owner_data: dict, current_user: str, session: Optional[Session] = None
    ) -> Tuple[bool, str, Optional[models.Owner]]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            is_valid, errors = self.validate_owner_data(
                owner_data, is_new=True, session=_session
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors), None

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
                        key
                        in [
                            "credit_limit",
                            "balance",
                            "service_charge_rate",
                            "discount_rate",
                        ]
                        and value is not None
                    ):
                        try:
                            new_owner_params[key] = Decimal(str(value))
                        except InvalidOperation:
                            self.logger.warning(
                                f"Invalid decimal for {key}: {value}. Setting to None."
                            )
                            new_owner_params[key] = None
                    else:
                        new_owner_params[key] = value

            if new_owner_params.get("balance") is None:
                new_owner_params["balance"] = Decimal("0.00")

            if new_owner_params.get("is_active") is None:
                new_owner_params["is_active"] = True

            new_owner = models.Owner(**new_owner_params)
            new_owner.created_by = current_user
            new_owner.modified_by = current_user

            _session.add(new_owner)
            if _close_session:
                _session.commit()
                _session.refresh(new_owner)  # Refresh here if committed internally

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
            _session.rollback()
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
            _session.rollback()
            self.logger.error(f"Error creating master owner: {e}", exc_info=True)
            return False, f"Failed to create owner: {e}", None
        finally:
            if _close_session:
                _session.close()

    def update_master_owner(
        self,
        owner_id: int,
        owner_data: dict,
        current_user: str,
        session: Optional[Session] = None,
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            owner = (
                _session.query(models.Owner)
                .filter(models.Owner.owner_id == owner_id)
                .first()
            )
            if not owner:
                return False, f"Owner with ID {owner_id} not found."

            original_account_number = owner.account_number
            if (
                "account_number" in owner_data
                and owner_data["account_number"] != original_account_number
            ):
                is_valid, errors = self.validate_owner_data(
                    owner_data,
                    is_new=False,
                    owner_id_to_ignore=owner_id,
                    session=_session,
                )
            else:
                temp_data_for_validation = owner_data.copy()
                temp_data_for_validation.pop("account_number", None)
                is_valid, errors = self.validate_owner_data(
                    temp_data_for_validation,
                    is_new=False,
                    owner_id_to_ignore=owner_id,
                    session=_session,
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
                        if str(value).strip() == "":
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

            if _close_session:
                _session.commit()
            return True, "Owner updated successfully."
        except sqlalchemy_exc.IntegrityError as ie:
            _session.rollback()
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
            _session.rollback()
            self.logger.error(
                f"Error updating master owner ID {owner_id}: {e}", exc_info=True
            )
            return False, f"Failed to update owner: {e}"
        finally:
            if _close_session:
                _session.close()

    def delete_master_owner(
        self,
        owner_id_to_delete: int,
        current_admin_id: str,
        session: Optional[Session] = None,
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            owner = (
                _session.query(models.Owner)
                .filter(models.Owner.owner_id == owner_id_to_delete)
                .first()
            )
            if not owner:
                return False, f"Owner with ID {owner_id_to_delete} not found."

            linked_horses_count = (
                _session.query(models.HorseOwner)
                .filter(models.HorseOwner.owner_id == owner_id_to_delete)
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

            _session.delete(owner)
            if _close_session:
                _session.commit()
            self.logger.info(
                f"Master Owner '{owner_name_for_log}' (ID: {owner_id_to_delete}) permanently deleted by admin '{current_admin_id}'."
            )
            return True, f"Owner '{owner_name_for_log}' deleted successfully."
        except sqlalchemy_exc.SQLAlchemyError as e:
            _session.rollback()
            self.logger.error(
                f"Error deleting master owner ID {owner_id_to_delete}: {e}",
                exc_info=True,
            )
            if isinstance(e, sqlalchemy_exc.IntegrityError):
                return (
                    False,
                    f"Cannot delete owner. It might be referenced by other records (e.g., invoices, payments). Details: {e.orig}",
                )
            return False, f"Failed to delete owner due to a database error: {e}"
        finally:
            if _close_session:
                _session.close()

    def get_owner_form_reference_data(
        self, session: Optional[Session] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            states_query = (
                _session.query(
                    models.StateProvince.state_code,
                    models.StateProvince.state_name,
                    models.StateProvince.country_code,
                )
                .filter(models.StateProvince.is_active == True)
                .order_by(
                    models.StateProvince.country_code, models.StateProvince.state_name
                )
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
            if _close_session:
                _session.close()

    def toggle_owner_active_status(
        self, owner_id: int, current_user_id: str, session: Optional[Session] = None
    ) -> Tuple[bool, str]:
        _session = session if session else db_manager().get_session()
        _close_session = session is None
        try:
            owner = (
                _session.query(models.Owner)
                .filter(models.Owner.owner_id == owner_id)
                .first()
            )
            if not owner:
                return False, "Owner not found."
            owner.is_active = not owner.is_active
            owner.modified_by = current_user_id
            if _close_session:
                _session.commit()
            status = "activated" if owner.is_active else "deactivated"
            self.logger.info(f"Owner ID {owner_id} {status} by {current_user_id}.")
            return True, f"Owner {status} successfully."
        except Exception as e:
            _session.rollback()
            self.logger.error(
                f"Error toggling active status for owner ID {owner_id}: {e}",
                exc_info=True,
            )
            return False, f"Failed to toggle owner status: {e}"
        finally:
            if _close_session:
                _session.close()
