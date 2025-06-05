# controllers/financial_controller.py
"""
EDSI Veterinary Management System - Financial Controller
Version: 1.0.0
Purpose: Handles business logic related to financial transactions, invoicing, and payments.
Last Updated: June 4, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-06-04):
    - Initial creation.
    - Added initial structure and placeholder methods for managing charges.
    - Includes methods for fetching lookup data (ChargeCodes, Owners, Users).
    - Added `add_charge_batch_to_horse` for handling multiple charge entries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation
from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from config.database_config import db_manager
from models import (
    Transaction,
    Invoice,
    Horse,
    Owner,
    ChargeCode,
    User,
    ChargeCodeCategory,  # For deriving category paths if needed
)

# BaseModel might be needed if we directly interact with its methods, but usually not in controllers.


class FinancialController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_charge_data(
        self, charge_item: Dict[str, Any], line_number: int
    ) -> List[str]:
        """
        Validates a single charge item from a batch.
        Args:
            charge_item: A dictionary containing details for one charge.
                         Expected keys: 'charge_code_id', 'description',
                                        'quantity', 'unit_price', 'service_date'.
            line_number: The line number of this item in the batch for error reporting.
        Returns:
            A list of error messages. Empty if valid.
        """
        errors = []
        if not charge_item.get("charge_code_id"):
            errors.append(f"Line {line_number}: Charge Code is required.")

        description = charge_item.get("description", "").strip()
        if not description:
            errors.append(f"Line {line_number}: Description is required.")
        elif len(description) > 500:
            errors.append(
                f"Line {line_number}: Description cannot exceed 500 characters."
            )

        quantity_str = str(charge_item.get("quantity", "0"))
        try:
            quantity = Decimal(quantity_str)
            if quantity <= Decimal("0"):
                errors.append(
                    f"Line {line_number}: Quantity must be greater than zero."
                )
        except InvalidOperation:
            errors.append(
                f"Line {line_number}: Quantity '{quantity_str}' is not a valid number."
            )

        unit_price_str = str(charge_item.get("unit_price", "0"))
        try:
            unit_price = Decimal(unit_price_str)
            if unit_price < Decimal("0"):  # Allow zero price, but not negative
                errors.append(f"Line {line_number}: Unit Price cannot be negative.")
        except InvalidOperation:
            errors.append(
                f"Line {line_number}: Unit Price '{unit_price_str}' is not a valid number."
            )

        service_date = charge_item.get("service_date")
        if not isinstance(service_date, date):
            errors.append(f"Line {line_number}: Service Date is invalid or missing.")
        elif service_date > date.today():
            errors.append(f"Line {line_number}: Service Date cannot be in the future.")

        return errors

    def add_charge_batch_to_horse(
        self,
        horse_id: int,
        owner_id: int,
        charge_items: List[Dict[str, Any]],  # List of dicts, each for one charge line
        batch_service_date: date,  # Common service date for the batch
        batch_billing_date: Optional[date],  # Common billing date for the batch
        administered_by_user_id: str,
        batch_notes: Optional[str] = None,  # Overall notes for this batch entry, if any
        batch_print_on_statement: bool = True,
    ) -> Tuple[bool, str, Optional[List[Transaction]]]:
        """
        Adds a batch of charges for a specific horse and owner.
        Each item in charge_items will become a Transaction record.
        Args:
            horse_id: ID of the horse.
            owner_id: ID of the owner to be billed.
            charge_items: A list of dictionaries, where each dictionary represents a charge.
                          Expected keys per item: 'charge_code_id', 'description',
                                                  'quantity', 'unit_price',
                                                  'item_notes' (optional),
                                                  'item_print_on_statement' (optional, defaults to batch_print_on_statement).
            batch_service_date: The primary service date for all items in this batch.
            batch_billing_date: The billing date for all items in this batch. Can be None.
            administered_by_user_id: User ID of the person entering these charges.
            batch_notes: Optional notes that might apply to the whole entry session (not stored directly, for context).
            batch_print_on_statement: Default for print_on_statement for items if not specified per item.
        Returns:
            A tuple: (success_flag, message, list_of_created_transactions_or_None)
        """
        session = db_manager.get_session()
        created_transactions: List[Transaction] = []

        # Validate common data
        if not horse_id:
            return False, "Horse ID is required.", None
        if not owner_id:
            return False, "Owner ID is required.", None
        if not administered_by_user_id:
            return False, "Administered by User ID is required.", None
        if not isinstance(batch_service_date, date):
            return False, "Valid Batch Service Date is required.", None
        if batch_billing_date and not isinstance(batch_billing_date, date):
            return False, "Batch Billing Date, if provided, must be a valid date.", None

        if not charge_items:
            return False, "No charge items provided.", None

        # Validate each charge item
        all_errors = []
        for i, item_data in enumerate(charge_items):
            item_data["service_date"] = (
                batch_service_date  # Ensure each item gets the batch service date for validation
            )
            errors = self.validate_charge_data(item_data, line_number=i + 1)
            all_errors.extend(errors)

        if all_errors:
            return (
                False,
                "Validation errors in charge items:\n- " + "\n- ".join(all_errors),
                None,
            )

        try:
            for item_data in charge_items:
                quantity = Decimal(str(item_data["quantity"]))
                unit_price = Decimal(str(item_data["unit_price"]))
                total_amount = Transaction.calculate_total_amount(quantity, unit_price)

                new_transaction = Transaction(
                    horse_id=horse_id,
                    owner_id=owner_id,
                    charge_code_id=item_data["charge_code_id"],
                    transaction_type="Charge",  # Default for this method
                    service_date=batch_service_date,
                    billing_date=batch_billing_date
                    or batch_service_date,  # Default to service_date if not provided
                    description=item_data["description"].strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=total_amount,
                    administered_by_id=administered_by_user_id,
                    notes=item_data.get(
                        "item_notes"
                    ),  # Specific notes for this line item
                    print_on_statement=item_data.get(
                        "item_print_on_statement", batch_print_on_statement
                    ),
                    created_by=administered_by_user_id,  # From BaseModel
                    modified_by=administered_by_user_id,  # From BaseModel
                )
                session.add(new_transaction)
                created_transactions.append(new_transaction)

            session.commit()
            for t in created_transactions:  # Refresh to get IDs
                session.refresh(t)

            self.logger.info(
                f"{len(created_transactions)} charges added successfully for horse ID {horse_id}, owner ID {owner_id}."
            )
            return (
                True,
                f"{len(created_transactions)} charges added successfully.",
                created_transactions,
            )

        except SQLAlchemyError as e:
            self.logger.error(
                f"SQLAlchemyError adding charge batch: {e}", exc_info=True
            )
            session.rollback()
            return False, f"Database error occurred: {e}", None
        except Exception as e:
            self.logger.error(
                f"Unexpected error adding charge batch: {e}", exc_info=True
            )
            session.rollback()
            return False, f"An unexpected error occurred: {e}", None
        finally:
            session.close()

    def get_transactions_for_horse(
        self, horse_id: int, invoiced: Optional[bool] = None
    ) -> List[Transaction]:
        """
        Retrieves transactions for a given horse.
        Args:
            horse_id: The ID of the horse.
            invoiced: If True, only invoiced. If False, only unbilled. If None, all.
        Returns:
            A list of Transaction objects.
        """
        session = db_manager.get_session()
        try:
            query = session.query(Transaction).filter(Transaction.horse_id == horse_id)
            if invoiced is True:
                query = query.filter(Transaction.invoice_id != None)
            elif invoiced is False:
                query = query.filter(Transaction.invoice_id == None)

            # Eager load related data for display
            query = query.options(
                joinedload(Transaction.charge_code)
                .joinedload(ChargeCode.category)
                .joinedload(
                    ChargeCodeCategory.parent
                ),  # Load charge code and its category path
                joinedload(Transaction.owner),
                joinedload(Transaction.administered_by_user),
            )

            transactions = query.order_by(
                Transaction.service_date.desc(), Transaction.created_date.desc()
            ).all()
            self.logger.info(
                f"Retrieved {len(transactions)} transactions for horse ID {horse_id}."
            )
            return transactions
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving transactions for horse ID {horse_id}: {e}",
                exc_info=True,
            )
            return []
        finally:
            session.close()

    def get_charge_codes_for_lookup(self, active_only: bool = True) -> List[ChargeCode]:
        """Retrieves charge codes for dropdowns/lookups."""
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCode).options(
                joinedload(ChargeCode.category).joinedload(
                    ChargeCodeCategory.parent
                )  # Eager load category path
            )
            if active_only:
                query = query.filter(ChargeCode.is_active == True)

            charge_codes = query.order_by(ChargeCode.code).all()
            self.logger.info(f"Retrieved {len(charge_codes)} charge codes for lookup.")
            return charge_codes
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving charge codes: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_active_owners_for_lookup(self) -> List[Owner]:
        """Retrieves active owners for dropdowns/lookups."""
        session = db_manager.get_session()
        try:
            owners = (
                session.query(Owner)
                .filter(Owner.is_active == True)
                .order_by(Owner.farm_name, Owner.last_name, Owner.first_name)
                .all()
            )
            self.logger.info(f"Retrieved {len(owners)} active owners for lookup.")
            return owners
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving active owners: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_active_users_for_lookup(self) -> List[User]:
        """Retrieves active users (staff/vets) for 'administered by' dropdowns."""
        session = db_manager.get_session()
        try:
            users = (
                session.query(User)
                .filter(User.is_active == True)
                .order_by(User.user_name)
                .all()
            )
            self.logger.info(f"Retrieved {len(users)} active users for lookup.")
            return users
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving active users: {e}", exc_info=True)
            return []
        finally:
            session.close()

    # --- Placeholder methods for future Invoicing and Payment logic ---
    def create_invoice_for_owner(
        self, owner_id: int, transaction_ids: List[int]
    ) -> Tuple[bool, str, Optional[Invoice]]:
        """Placeholder for creating an invoice from selected transactions."""
        self.logger.warning("create_invoice_for_owner: Not yet implemented.")
        return False, "Invoicing not yet implemented.", None

    def record_payment(
        self,
        owner_id: int,
        amount: Decimal,
        payment_date: date,
        method: str,
        notes: Optional[str],
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """Placeholder for recording a payment."""
        self.logger.warning("record_payment: Not yet implemented.")
        return False, "Payment recording not yet implemented.", None

    def apply_payment_to_invoice(
        self, payment_id: int, invoice_id: int
    ) -> Tuple[bool, str]:
        """Placeholder for applying a payment to an invoice."""
        self.logger.warning("apply_payment_to_invoice: Not yet implemented.")
        return False, "Applying payments not yet implemented."
