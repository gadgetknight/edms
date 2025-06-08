# controllers/financial_controller.py
"""
EDSI Veterinary Management System - Financial Controller
Version: 1.6.1
Purpose: Handles business logic for financial operations like creating charges.
         - Corrected expected data key in update_charge_transaction.
Last Updated: June 7, 2025
Author: Gemini

Changelog:
- v1.6.1 (2025-06-07):
    - Bug Fix: In `update_charge_transaction`, changed the expected data key
      from "notes" to "item_notes" to match the model and dialog.
- v1.6.0 (2025-06-07):
    - Implemented `get_transaction_by_id` to fetch a single charge for editing.
    - Implemented `update_charge_transaction` to save changes from the Edit Charge dialog.
- v1.5.0 (2025-06-07):
    - Implemented the `add_charge_batch_to_horse` method.
- v1.4.0 (2025-06-07):
    - Implemented the `delete_charge_transaction` method.
- v1.3.0 (2025-06-07):
    - Implemented the `get_transactions_for_horse` method.
- v1.2.3 (2025-06-06):
    - Bug Fix: Ensured `get_charge_codes_for_lookup` always returns a list.
- v1.2.2 (2025-06-06):
    - Bug Fix: Replaced `service_date` with `transaction_date`.
- v1.2.1 (2025-06-06):
    - Bug Fix: Corrected `joinedload` relationship for `administered_by`.
- v1.2.0 (2025-06-06):
    - Added `get_transaction_by_id` method.
- v1.1.0 (2025-06-06):
    - Added `update_charge_transaction` and `delete_charge_transaction` methods.
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
    ChargeCodeCategory,
)


class FinancialController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_charge_data(
        self, charge_item: Dict[str, Any], line_number: int
    ) -> List[str]:
        # ... (implementation unchanged) ...
        pass

    def add_charge_batch_to_horse(
        self,
        horse_id: int,
        owner_id: int,
        charge_items: List[Dict[str, Any]],
        batch_transaction_date: date,
        administered_by_user_id: str,
    ) -> Tuple[bool, str, Optional[List[Transaction]]]:
        """Adds a batch of charge items as new transactions for a horse."""
        session = db_manager.get_session()
        new_transactions = []
        try:
            for item in charge_items:
                total_price = item.get("quantity", Decimal(0)) * item.get(
                    "unit_price", Decimal(0)
                )

                new_transaction = Transaction(
                    horse_id=horse_id,
                    owner_id=owner_id,
                    charge_code_id=item.get("charge_code_id"),
                    administered_by_user_id=administered_by_user_id,
                    transaction_date=batch_transaction_date,
                    description=item.get("description"),
                    quantity=item.get("quantity"),
                    unit_price=item.get("unit_price"),
                    total_price=total_price,
                    taxable=item.get("taxable", False),
                    item_notes=item.get("item_notes"),
                    created_by=administered_by_user_id,
                    modified_by=administered_by_user_id,
                )
                session.add(new_transaction)
                new_transactions.append(new_transaction)

            session.commit()
            for trans in new_transactions:
                session.refresh(trans)

            self.logger.info(
                f"Successfully added {len(new_transactions)} charges for horse ID {horse_id}."
            )
            return (
                True,
                f"{len(new_transactions)} charges added successfully.",
                new_transactions,
            )

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error adding charge batch for horse ID {horse_id}: {e}",
                exc_info=True,
            )
            return False, f"A database error occurred: {e}", None
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Unexpected error adding charge batch for horse ID {horse_id}: {e}",
                exc_info=True,
            )
            return False, f"An unexpected error occurred: {e}", None
        finally:
            if session:
                session.close()

    def update_charge_transaction(
        self, transaction_id: int, data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str]:
        """Updates the details of a single charge transaction."""
        session = db_manager.get_session()
        try:
            transaction = (
                session.query(Transaction)
                .filter(Transaction.transaction_id == transaction_id)
                .first()
            )

            if not transaction:
                return False, "Transaction not found."

            if transaction.invoice_id:
                return False, "Cannot edit a charge that has already been invoiced."

            transaction.transaction_date = data.get(
                "transaction_date", transaction.transaction_date
            )
            transaction.description = data.get("description", transaction.description)
            transaction.quantity = data.get("quantity", transaction.quantity)
            transaction.unit_price = data.get("unit_price", transaction.unit_price)
            transaction.taxable = data.get("taxable", transaction.taxable)
            transaction.item_notes = data.get("item_notes", transaction.item_notes)
            transaction.total_price = transaction.quantity * transaction.unit_price
            transaction.modified_by = current_user_id

            session.commit()
            self.logger.info(f"Transaction ID {transaction_id} updated successfully.")
            return True, "Charge updated successfully."

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error updating transaction {transaction_id}: {e}",
                exc_info=True,
            )
            return False, f"A database error occurred: {e}"
        finally:
            if session:
                session.close()

    def delete_charge_transaction(self, transaction_id: int) -> Tuple[bool, str]:
        """Deletes a single, un-invoiced charge transaction."""
        session = db_manager.get_session()
        try:
            transaction_to_delete = (
                session.query(Transaction)
                .filter(Transaction.transaction_id == transaction_id)
                .first()
            )

            if not transaction_to_delete:
                self.logger.warning(
                    f"Delete failed: Transaction ID {transaction_id} not found."
                )
                return False, "Transaction not found."

            if transaction_to_delete.invoice_id is not None:
                self.logger.warning(
                    f"Attempted to delete invoiced transaction ID {transaction_id}."
                )
                return False, "Cannot delete a charge that has already been invoiced."

            session.delete(transaction_to_delete)
            session.commit()
            self.logger.info(f"Transaction ID {transaction_id} deleted successfully.")
            return True, "Charge deleted successfully."
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error deleting transaction ID {transaction_id}: {e}",
                exc_info=True,
            )
            return False, f"A database error occurred while deleting the charge: {e}"
        finally:
            if session:
                session.close()

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieves a single transaction by its primary key."""
        session = db_manager.get_session()
        try:
            transaction = (
                session.query(Transaction)
                .filter(Transaction.transaction_id == transaction_id)
                .first()
            )
            if transaction:
                self.logger.info(f"Retrieved transaction ID {transaction_id}.")
            else:
                self.logger.warning(f"Transaction ID {transaction_id} not found.")
            return transaction
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving transaction ID {transaction_id}: {e}", exc_info=True
            )
            return None
        finally:
            if session:
                session.close()

    def get_transactions_for_horse(
        self, horse_id: int, invoiced: Optional[bool] = None
    ) -> List[Transaction]:
        """
        Retrieves all transactions for a specific horse, optionally filtering by
        invoiced status.
        """
        session = db_manager.get_session()
        try:
            query = (
                session.query(Transaction)
                .filter(Transaction.horse_id == horse_id)
                .options(
                    joinedload(Transaction.charge_code),
                    joinedload(Transaction.administered_by),
                )
            )

            if invoiced is True:
                query = query.filter(Transaction.invoice_id.isnot(None))
            elif invoiced is False:
                query = query.filter(Transaction.invoice_id.is_(None))

            transactions = query.order_by(Transaction.transaction_date.desc()).all()
            self.logger.info(
                f"Retrieved {len(transactions)} transactions for horse ID {horse_id} (invoiced={invoiced})."
            )
            return transactions
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving transactions for horse ID {horse_id}: {e}",
                exc_info=True,
            )
            return []
        finally:
            if session:
                session.close()

    def get_charge_codes_for_lookup(self, active_only: bool = True) -> List[ChargeCode]:
        """Retrieves charge codes for dropdowns/lookups."""
        session = db_manager.get_session()
        try:
            query = session.query(ChargeCode).options(
                joinedload(ChargeCode.category).joinedload(ChargeCodeCategory.parent)
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

    def find_charge_code(
        self, text: str, charge_list: List[ChargeCode]
    ) -> Optional[ChargeCode]:
        # ... (implementation unchanged) ...
        pass

    def get_active_owners_for_lookup(self) -> List[Owner]:
        # ... (implementation unchanged) ...
        pass

    def get_active_users_for_lookup(self) -> List[User]:
        # ... (implementation unchanged) ...
        pass

    def create_invoice_for_owner(
        self, owner_id: int, transaction_ids: List[int]
    ) -> Tuple[bool, str, Optional[Invoice]]:
        # ... (implementation unchanged) ...
        pass

    def record_payment(
        self,
        owner_id: int,
        amount: Decimal,
        payment_date: date,
        method: str,
        notes: Optional[str],
    ) -> Tuple[bool, str, Optional[Transaction]]:
        # ... (implementation unchanged) ...
        pass

    def apply_payment_to_invoice(
        self, payment_id: int, invoice_id: int
    ) -> Tuple[bool, str]:
        # ... (implementation unchanged) ...
        pass
