# controllers/financial_controller.py
"""
EDSI Veterinary Management System - Financial Controller
Version: 2.4.0
Purpose: Handles business logic for financial operations like creating invoices and recording payments.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v2.4.0 (2025-06-10):
    - Refactored `generate_invoices_from_transactions` to ensure a unique set of
      owners is used for invoice creation for each horse. This prevents a bug
      where duplicate invoices were being generated for each owner.
- v2.3.0 (2025-06-10):
    - Added record_payment method to handle saving a payment transaction. This
      method updates the Owner and Invoice balances, creates an OwnerPayment
      record, and logs the event in OwnerBillingHistory.
- v2.2.0 (2025-06-10):
    - Refactored generate_invoices_from_transactions to be more robust. It now
      explicitly groups charges by horse before processing, ensuring that all
      charges for a single horse are correctly grouped onto one invoice per owner.
"""
# ... (imports remain the same) ...
import logging
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation
from datetime import date
from collections import defaultdict

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
    OwnerBillingHistory,
    HorseOwner,
    OwnerPayment,
)


class FinancialController:
    # ... (all existing methods like __init__, get_invoice_by_id, etc. remain unchanged) ...
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        session = db_manager.get_session()
        try:
            invoice = (
                session.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
            )
            return invoice
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving invoice {invoice_id}: {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def get_invoices_for_owner(self, owner_id: int) -> List[Invoice]:
        session = db_manager.get_session()
        try:
            invoices = (
                session.query(Invoice)
                .options(joinedload(Invoice.owner))
                .filter(
                    Invoice.owner_id == owner_id, Invoice.status != "INTERNAL_PROCESSED"
                )
                .order_by(Invoice.invoice_date.desc())
                .all()
            )
            return invoices
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving invoices for owner {owner_id}: {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def get_transactions_for_invoice(self, invoice_id: int) -> List[Transaction]:
        session = db_manager.get_session()
        try:
            transactions = (
                session.query(Transaction)
                .filter(Transaction.invoice_id == invoice_id)
                .options(joinedload(Transaction.charge_code))
                .order_by(Transaction.transaction_date.asc())
                .all()
            )
            return transactions
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error retrieving transactions for invoice {invoice_id}: {e}",
                exc_info=True,
            )
            return []
        finally:
            session.close()

    def generate_invoices_from_transactions(
        self, source_transaction_ids: List[int], current_user_id: str
    ) -> Tuple[bool, str, List[Invoice]]:
        self.logger.info(
            f"--- Starting Invoice Generation for transaction IDs: {source_transaction_ids} ---"
        )
        session = db_manager.get_session()
        try:
            if not source_transaction_ids:
                return False, "No charges were selected to be invoiced.", []

            source_transactions = (
                session.query(Transaction)
                .filter(Transaction.transaction_id.in_(source_transaction_ids))
                .options(
                    joinedload(Transaction.horse)
                    .selectinload(Horse.owner_associations)
                    .joinedload(HorseOwner.owner)
                )
                .all()
            )

            for t in source_transactions:
                if t.status != "ACTIVE":
                    return (
                        False,
                        f"Charge '{t.description}' (ID: {t.transaction_id}) has already been processed.",
                        [],
                    )

            generated_invoices = []

            transactions_by_horse = defaultdict(list)
            for t in source_transactions:
                transactions_by_horse[t.horse_id].append(t)

            self.logger.info(
                f"Generating invoices for {len(transactions_by_horse)} horse(s)."
            )

            # --- MODIFIED BLOCK START ---
            # Refactored loop to be more robust and prevent duplicate invoice creation.
            for horse_id, transactions_for_horse in transactions_by_horse.items():
                horse = transactions_for_horse[0].horse

                # Use a dictionary to ensure we process each owner only once.
                unique_associations = {
                    assoc.owner_id: assoc for assoc in horse.owner_associations
                }

                if not unique_associations:
                    self.logger.warning(
                        f"Horse '{horse.horse_name}' has no owners assigned, skipping."
                    )
                    continue

                # Now loop through the unique associations
                for owner_id, association in unique_associations.items():
                    owner = association.owner
                    ownership_percentage = association.percentage_ownership / Decimal(
                        "100"
                    )

                    # Create ONE invoice per owner
                    owner_invoice = Invoice(
                        owner_id=owner.owner_id,
                        invoice_date=date.today(),
                        created_by=current_user_id,
                        modified_by=current_user_id,
                        status="Unpaid",
                    )
                    session.add(owner_invoice)
                    session.flush()

                    invoice_total = Decimal("0.00")

                    # Add line items for all transactions for this horse
                    for src_trans in transactions_for_horse:
                        prorated_price = (
                            src_trans.total_price * ownership_percentage
                        ).quantize(Decimal("0.01"))
                        invoice_total += prorated_price

                        line_item_desc = src_trans.description
                        # Add percentage share to description if more than one owner
                        if len(unique_associations) > 1:
                            line_item_desc += (
                                f" ({association.percentage_ownership:.2f}% Share)"
                            )

                        new_line_item = Transaction(
                            horse_id=src_trans.horse_id,
                            owner_id=owner.owner_id,
                            invoice_id=owner_invoice.invoice_id,
                            charge_code_id=src_trans.charge_code_id,
                            administered_by_user_id=src_trans.administered_by_user_id,
                            transaction_date=src_trans.transaction_date,
                            description=line_item_desc,
                            quantity=src_trans.quantity,
                            unit_price=(src_trans.unit_price * ownership_percentage),
                            total_price=prorated_price,
                            taxable=src_trans.taxable,
                            item_notes=src_trans.item_notes,
                            created_by=current_user_id,
                            modified_by=current_user_id,
                            status="BILLED",
                        )
                        session.add(new_line_item)

                    # Finalize the invoice object
                    owner_invoice.subtotal = invoice_total
                    owner_invoice.grand_total = invoice_total
                    owner_invoice.balance_due = invoice_total
                    owner.balance = (owner.balance or Decimal("0.00")) + invoice_total

                    # Create billing history
                    history_entry = OwnerBillingHistory(
                        owner_id=owner.owner_id,
                        description=f"Invoice #{owner_invoice.invoice_id} generated for {horse.horse_name}.",
                        amount_change=invoice_total,
                        new_balance=owner.balance,
                        created_by=current_user_id,
                    )
                    session.add(history_entry)
                    generated_invoices.append(owner_invoice)
            # --- MODIFIED BLOCK END ---

            for src_trans in source_transactions:
                src_trans.status = "PROCESSED"
                self.logger.debug(
                    f"Marking source TXN ID {src_trans.transaction_id} as PROCESSED."
                )

            session.commit()
            self.logger.info(
                f"--- Invoice Generation Complete. {len(generated_invoices)} invoices created. ---"
            )
            return (
                True,
                f"{len(generated_invoices)} invoice(s) created successfully.",
                generated_invoices,
            )

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error during invoice generation: {e}", exc_info=True
            )
            return False, f"A database error occurred: {e}", []
        finally:
            session.close()

    def record_payment(self, payment_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Records a payment against an invoice and updates balances."""
        session = db_manager.get_session()
        try:
            invoice_id = payment_data.get("invoice_id")
            amount = payment_data.get("amount")
            current_user_id = payment_data.get("user_id")

            if not all([invoice_id, amount, current_user_id]):
                return False, "Missing required payment data."

            invoice = (
                session.query(Invoice)
                .options(joinedload(Invoice.owner))
                .filter(Invoice.invoice_id == invoice_id)
                .first()
            )
            if not invoice:
                return False, "Invoice not found."

            owner = invoice.owner
            if not owner:
                return False, "Owner for the invoice could not be found."

            # Create the payment record
            new_payment = OwnerPayment(
                owner_id=invoice.owner_id,
                amount=amount,
                payment_date=payment_data.get("payment_date", date.today()),
                payment_method=payment_data.get("payment_method", "Unknown"),
                reference_number=payment_data.get("reference_number"),
                notes=payment_data.get("notes"),
                created_by=current_user_id,
                modified_by=current_user_id,
            )
            session.add(new_payment)

            # Update invoice balances
            invoice.amount_paid = (invoice.amount_paid or Decimal("0.00")) + amount
            invoice.balance_due = (invoice.balance_due or Decimal("0.00")) - amount
            if invoice.balance_due <= Decimal("0.00"):
                invoice.status = "Paid"
                self.logger.info(f"Invoice #{invoice_id} marked as Paid.")

            # Update owner's total balance
            owner.balance = (owner.balance or Decimal("0.00")) - amount

            # Create billing history log for the payment
            history_entry = OwnerBillingHistory(
                owner_id=owner.owner_id,
                description=f"Payment received for Invoice #{invoice.invoice_id}. Ref: {new_payment.reference_number or new_payment.payment_method}",
                amount_change=-amount,
                new_balance=owner.balance,
                created_by=current_user_id,
            )
            session.add(history_entry)

            session.commit()
            self.logger.info(
                f"Payment of ${amount} successfully recorded for Invoice #{invoice_id}."
            )
            return True, "Payment recorded successfully."

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error recording payment for invoice {invoice_id}: {e}",
                exc_info=True,
            )
            return False, "A database error occurred while recording the payment."
        finally:
            if session:
                session.close()

    def get_transactions_for_horse(self, horse_id: int) -> List[Transaction]:
        session = db_manager.get_session()
        try:
            transactions = (
                session.query(Transaction)
                .filter(
                    Transaction.horse_id == horse_id, Transaction.status == "ACTIVE"
                )
                .options(
                    joinedload(Transaction.charge_code),
                    joinedload(Transaction.administered_by),
                )
                .order_by(Transaction.transaction_date.desc())
                .all()
            )
            self.logger.info(
                f"Retrieved {len(transactions)} ACTIVE transactions for horse ID {horse_id}."
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

    def add_charge_batch_to_horse(
        self,
        horse_id: int,
        owner_id: int,
        charge_items: List[Dict[str, Any]],
        batch_transaction_date: date,
        administered_by_user_id: str,
    ) -> Tuple[bool, str, Optional[List[Transaction]]]:
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
        session = db_manager.get_session()
        try:
            transaction = (
                session.query(Transaction)
                .options(joinedload(Transaction.charge_code))
                .filter(Transaction.transaction_id == transaction_id)
                .first()
            )
            if transaction:
                self.logger.info(
                    f"Retrieved transaction ID {transaction_id} with its charge code."
                )
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

    def delete_invoice(self, invoice_id: int, current_user_id: str) -> Tuple[bool, str]:
        """
        Deletes an invoice and reverses the owner's balance.
        NOTE: This does NOT make the original charges billable again.
        """
        session = db_manager.get_session()
        try:
            invoice_to_delete = (
                session.query(Invoice)
                .options(joinedload(Invoice.owner))
                .filter(Invoice.invoice_id == invoice_id)
                .first()
            )

            if not invoice_to_delete:
                return False, "Invoice not found."

            if not invoice_to_delete.owner:
                return (
                    False,
                    "Cannot delete invoice: Owner record is missing or detached.",
                )

            owner = invoice_to_delete.owner
            reversal_amount = invoice_to_delete.grand_total

            self.logger.info(
                f"Deleting Invoice #{invoice_id} for owner '{owner.owner_id}'. "
                f"Reversing balance by ${reversal_amount}."
            )

            owner.balance = (owner.balance or Decimal("0.00")) - reversal_amount

            history_entry = OwnerBillingHistory(
                owner_id=owner.owner_id,
                description=f"Invoice #{invoice_id} deleted by user. Reversal of charges.",
                amount_change=-reversal_amount,
                new_balance=owner.balance,
                created_by=current_user_id,
            )
            session.add(history_entry)

            session.delete(invoice_to_delete)
            session.commit()

            self.logger.info(
                f"Successfully deleted Invoice #{invoice_id} and adjusted owner balance."
            )
            return True, f"Invoice #{invoice_id} has been deleted."

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error deleting invoice {invoice_id}: {e}", exc_info=True
            )
            return False, f"A database error occurred during deletion: {e}"
        finally:
            if session:
                session.close()
