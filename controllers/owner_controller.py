# controllers/owner_controller.py

"""
EDSI Veterinary Management System - Owner Controller
Version: 1.0.3
Purpose: Business logic for owner master file operations.
         Corrected handling of owner_name to use model's actual fields
         (first_name, last_name, farm_name) instead of hybrid_property in constructor.
Last Updated: May 14, 2025
Author: Claude Assistant

Changelog:
- v1.0.3 (2025-05-14): Fixed TypeError for 'owner_name' argument.
  - `create_master_owner`: Instantiates Owner using first_name, last_name, farm_name.
  - `get_all_owners_for_lookup`: Queries individual name fields and constructs display name.
                                 Search filter updated to target individual name fields.
  - `validate_owner_data`: Validates individual name fields.
- v1.0.2 (2025-05-13): Revised to align with existing Owner/StateProvince models.
- v1.0.1 (2025-05-13): Temporarily removed Country and OwnerType model dependencies.
- v1.0.0 (2025-05-13): Initial implementation
"""

import logging
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func  # Added func
from config.database_config import db_manager
from models import Owner, StateProvince


class OwnerController:
    """Controller for owner master file operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_owners_for_lookup(self, search_term: str = "") -> List[Dict[str, any]]:
        """
        Fetches all active owners, filtered by search term, for lookup purposes.
        Returns a list of dictionaries with 'id' (owner_id) and 'name_account'.
        """
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

            # Order by farm_name, then last_name, then first_name for consistent sorting
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
                name_parts = []
                if first_name:
                    name_parts.append(first_name)
                if last_name:
                    name_parts.append(last_name)
                individual_name = " ".join(name_parts)

                display_text = ""
                if farm_name:
                    display_text = farm_name
                    if individual_name:
                        display_text += f" ({individual_name})"
                elif individual_name:
                    display_text = individual_name
                else:  # Fallback if all name parts are empty
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
        """
        Fetches a single owner by their owner_id.
        Includes related StateProvince.
        """
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
        """
        Validates owner data based on existing Owner model fields.
        """
        errors = []

        first_name = owner_data.get("first_name", "").strip()
        last_name = owner_data.get("last_name", "").strip()
        farm_name = owner_data.get("farm_name", "").strip()

        if not first_name and not last_name and not farm_name:
            errors.append(
                "At least one name field (First, Last, or Farm Name) is required."
            )

        # Other required fields based on your model and UI
        if not owner_data.get("address_line1", "").strip():
            errors.append("Address Line 1 is required.")
        if not owner_data.get("city", "").strip():
            errors.append("City is required.")
        if not owner_data.get("state_code", "").strip():
            errors.append("State is required.")
        if not owner_data.get("zip_code", "").strip():
            errors.append("Zip Code is required.")
        if not owner_data.get("phone", "").strip():
            errors.append("Phone is required.")

        # Example length checks (adjust as per your model constraints)
        if len(first_name) > 50:
            errors.append("First Name too long.")
        if len(last_name) > 50:
            errors.append("Last Name too long.")
        if len(farm_name) > 100:
            errors.append("Farm Name too long.")
        if len(owner_data.get("address_line1", "")) > 100:
            errors.append("Address 1 too long.")
        # ... other length checks ...

        if is_new and owner_data.get("account_number"):
            session = db_manager.get_session()
            try:
                existing = (
                    session.query(Owner)
                    .filter(
                        Owner.account_number == owner_data["account_number"].strip()
                    )
                    .first()
                )
                if existing:
                    errors.append(
                        f"Account Number '{owner_data['account_number']}' already exists."
                    )
            finally:
                session.close()

        return len(errors) == 0, errors

    def create_master_owner(
        self, owner_data: dict, current_user: str
    ) -> Tuple[bool, str, Optional[Owner]]:
        """
        Creates a new master owner record using existing Owner model fields.
        """
        # The dialog already constructs a combined 'owner_name' for display/logging,
        # but for validation and creation, we use the individual parts.
        validation_data = {
            "first_name": owner_data.get("first_name"),
            "last_name": owner_data.get("last_name"),
            "farm_name": owner_data.get("farm_name"),
            "address_line1": owner_data.get("address_line1"),
            "city": owner_data.get("city"),
            "state_code": owner_data.get("state_code"),
            "zip_code": owner_data.get("zip_code"),
            "phone": owner_data.get("phone"),
            "account_number": owner_data.get("account_number"),
        }
        is_valid, errors = self.validate_owner_data(validation_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            # Construct the Owner object using fields defined in the model
            new_owner = Owner(
                account_number=owner_data.get("account_number", "").strip() or None,
                first_name=owner_data.get("first_name", "").strip() or None,
                last_name=owner_data.get("last_name", "").strip() or None,
                farm_name=owner_data.get("farm_name", "").strip() or None,
                # The combined 'owner_name' from dialog is not passed to constructor
                address_line1=owner_data.get("address_line1", "").strip(),
                address_line2=owner_data.get("address_line2", "").strip() or None,
                city=owner_data.get("city", "").strip(),
                state_code=owner_data.get("state_code", "").strip() or None,
                zip_code=owner_data.get("zip_code", "").strip(),
                # country_name and owner_type_description are not in current Owner model
                # country_id and owner_type_id are also not in current Owner model
                phone=owner_data.get("phone", "").strip(),
                mobile_phone=owner_data.get("mobile_phone", "").strip() or None,
                email=owner_data.get("email", "").strip() or None,
                is_active=owner_data.get("is_active", True),
                # Assuming these fields exist in your Owner model based on common practice
                # If not, they need to be added to the model or removed here.
                # created_by=current_user,
                # modified_by=current_user
            )
            # Set created_by and modified_by if they exist on the model
            if hasattr(new_owner, "created_by"):
                new_owner.created_by = current_user
            if hasattr(new_owner, "modified_by"):
                new_owner.modified_by = current_user

            session.add(new_owner)
            session.commit()
            session.refresh(new_owner)

            # Use the hybrid property for logging the combined name
            display_name_for_log = new_owner.owner_name
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
        """
        Updates an existing master owner record using existing Owner model fields.
        """
        session = db_manager.get_session()
        try:
            owner = session.query(Owner).filter(Owner.owner_id == owner_id).first()
            if not owner:
                return False, f"Owner with ID {owner_id} not found."

            validation_data = {"owner_id": owner_id}
            update_fields = [
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
                "account_number",
                # Add other fields from your Owner model that are updatable
            ]
            for key in update_fields:
                if key in owner_data:
                    validation_data[key] = owner_data[key]

            is_valid, errors = self.validate_owner_data(validation_data, is_new=False)
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            for key in update_fields:
                if key in owner_data:
                    value = owner_data[key]
                    setattr(
                        owner, key, value.strip() if isinstance(value, str) else value
                    )

            if hasattr(owner, "modified_by"):
                owner.modified_by = current_user
            if hasattr(owner, "modified_date"):
                owner.modified_date = datetime.utcnow()

            session.commit()
            display_name_for_log = owner.owner_name  # Use hybrid property for log
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

    def get_owner_form_reference_data(self) -> Dict[str, List[Dict[str, any]]]:
        """Fetches reference data for owner forms (States only for now)."""
        session = db_manager.get_session()
        try:
            states = [
                {"id": s.state_code, "name": s.state_name}
                for s in session.query(StateProvince)
                .filter(StateProvince.is_active == True)
                .order_by(StateProvince.state_name)
                .all()
            ]
            countries = []
            owner_types = []

            return {
                "states": states,
                "countries": countries,
                "owner_types": owner_types,
            }
        except Exception as e:
            self.logger.error(
                f"Error fetching owner form reference data: {e}", exc_info=True
            )
            return {"states": [], "countries": [], "owner_types": []}
        finally:
            session.close()
