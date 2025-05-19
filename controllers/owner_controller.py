# controllers/owner_controller.py

"""
EDSI Veterinary Management System - Owner Controller
Version: 1.3.2
Purpose: Business logic for owner master file operations.
         Removed direct handling of 'country_name' for Owner model
         as it's derived via StateProvince and not a direct Owner field.
Last Updated: May 17, 2025
Author: Claude Assistant

Changelog:
- v1.3.2 (2025-05-17):
    - Removed `country_name` from Owner instantiation in `create_master_owner`
      and from updatable fields in `update_master_owner` as it's not a direct DB field.
    - Removed `country_name` length validation in `validate_owner_data`.
- v1.3.1 (2025-05-17):
    - Removed phone number requirement from `validate_owner_data`.
    - Added `mobile_phone` handling to `create_master_owner` and `update_master_owner`.
- v1.2.1 (2025-05-15): Removed credit_rating from Owner constructor call and update logic.
- v1.2.0 (2025-05-15): Added delete_master_owner method.
"""

import logging
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
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
        except Exception as e:
            self.logger.error(f"Error fetching all master owners: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_all_owners_for_lookup(self, search_term: str = "") -> List[Dict[str, any]]:
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
        except Exception as e:
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
        except Exception as e:
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
        first_name = owner_data.get("first_name", "").strip()
        last_name = owner_data.get("last_name", "").strip()
        farm_name = owner_data.get("farm_name", "").strip()
        account_number_val = owner_data.get("account_number", "").strip()

        if not first_name and not last_name and not farm_name:
            errors.append(
                "It's recommended to provide at least one of: First Name, Last Name, or Farm Name."
            )
        elif first_name and not last_name:
            errors.append("If First Name is provided, Last Name is recommended.")

        if not owner_data.get("address_line1", "").strip():
            errors.append("Address Line 1 is required.")
        if not owner_data.get("city", "").strip():
            errors.append("City is required.")
        if not owner_data.get("state_code"):
            errors.append("State is required.")
        if not owner_data.get("zip_code", "").strip():
            errors.append("Zip Code is required.")

        if len(first_name) > 50:
            errors.append("First Name cannot exceed 50 characters.")
        if len(last_name) > 50:
            errors.append("Last Name cannot exceed 50 characters.")
        if len(farm_name) > 100:
            errors.append("Farm Name cannot exceed 100 characters.")
        if len(owner_data.get("address_line1", "")) > 100:
            errors.append("Address Line 1 cannot exceed 100 characters.")
        if len(owner_data.get("address_line2", "")) > 100:
            errors.append("Address Line 2 cannot exceed 100 characters.")
        if len(owner_data.get("city", "")) > 50:
            errors.append("City cannot exceed 50 characters.")
        if len(owner_data.get("zip_code", "")) > 20:
            errors.append("Zip Code cannot exceed 20 characters.")
        # country_name is informational, so length validation might still be useful if displayed
        # but it's not a DB constraint on Owner table.
        # if len(owner_data.get("country_name", "")) > 50:
        #     errors.append("Country Name cannot exceed 50 characters (informational).")
        if len(owner_data.get("phone", "")) > 20:
            errors.append("Primary Phone cannot exceed 20 characters.")
        if len(owner_data.get("mobile_phone", "")) > 20:
            errors.append("Mobile Phone cannot exceed 20 characters.")
        if len(owner_data.get("email", "")) > 100:
            errors.append("Email cannot exceed 100 characters.")
        if len(account_number_val) > 20:
            errors.append("Account Number cannot exceed 20 characters.")

        if is_new and account_number_val:
            session = db_manager.get_session()
            try:
                existing = (
                    session.query(Owner)
                    .filter(Owner.account_number == account_number_val)
                    .first()
                )
                if existing:
                    errors.append(
                        f"Account Number '{account_number_val}' already exists."
                    )
            finally:
                session.close()
        return len(errors) == 0, errors

    def create_master_owner(
        self, owner_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Owner]]:
        is_valid, errors = self.validate_owner_data(owner_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            # Create Owner object without country_name
            new_owner = Owner(
                account_number=owner_data.get("account_number", "").strip() or None,
                first_name=owner_data.get("first_name", "").strip() or None,
                last_name=owner_data.get("last_name", "").strip() or None,
                farm_name=owner_data.get("farm_name", "").strip() or None,
                address_line1=owner_data.get("address_line1", "").strip() or None,
                address_line2=owner_data.get("address_line2", "").strip() or None,
                city=owner_data.get("city", "").strip() or None,
                state_code=owner_data.get("state_code"),
                zip_code=owner_data.get("zip_code", "").strip() or None,
                # country_name is NOT passed to the constructor
                phone=owner_data.get("phone", "").strip() or None,
                mobile_phone=owner_data.get("mobile_phone", "").strip() or None,
                email=owner_data.get("email", "").strip() or None,
                is_active=owner_data.get("is_active", True),
            )
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

            validation_data = owner_data.copy()
            if "address_line1" not in validation_data:
                validation_data["address_line1"] = owner.address_line1
            if "city" not in validation_data:
                validation_data["city"] = owner.city
            if "state_code" not in validation_data:
                validation_data["state_code"] = owner.state_code
            if "zip_code" not in validation_data:
                validation_data["zip_code"] = owner.zip_code

            is_valid, errors = self.validate_owner_data(validation_data, is_new=False)
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
                "zip_code",  # country_name removed
                "phone",
                "mobile_phone",
                "email",
                "is_active",
                "balance",
                "credit_limit",
                "billing_terms",
                "service_charge_rate",
                "discount_rate",
            ]

            for key in updatable_fields:
                if key in owner_data:
                    value = owner_data[key]
                    setattr(
                        owner, key, value.strip() if isinstance(value, str) else value
                    )

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
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error deleting master owner ID {owner_id_to_delete}: {e}",
                exc_info=True,
            )
            return False, f"Failed to delete owner: {e}"
        finally:
            session.close()

    def get_owner_form_reference_data(self) -> Dict[str, List[Dict[str, any]]]:
        session = db_manager.get_session()
        try:
            states = [
                {
                    "id": s.state_code,
                    "name": s.state_name,
                    "country_code": s.country_code,
                }
                for s in session.query(StateProvince)
                .filter(StateProvince.is_active == True)
                .order_by(StateProvince.state_name)
                .all()
            ]
            return {
                "states": states
            }  # Removed countries from here as it's free text now
        except Exception as e:
            self.logger.error(
                f"Error fetching owner form reference data: {e}", exc_info=True
            )
            return {"states": []}
        finally:
            session.close()
