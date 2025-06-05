# models/financial_models.py
"""
EDSI Veterinary Management System - Financial Models
Version: 1.0.1
Purpose: Defines SQLAlchemy models for financial transactions and invoices.
         Corrected ForeignKey in Transaction.charge_code_id to point to charge_codes.id.
Last Updated: June 4, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-06-04):
    - Corrected the ForeignKey for `Transaction.charge_code_id` to reference
      `charge_codes.id` instead of the non-existent `charge_codes.charge_code_id`.
- v1.0.0 (2025-06-04):
    - Initial creation.
    - Added Transaction model to record individual billable charges.
    - Added Invoice model to group transactions for billing owners.
    - Defined relationships between Transaction, Invoice, Horse, Owner, ChargeCode, User.
"""

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Numeric,
    Boolean,
    Text,
    Enum,  # Not currently used, but kept for potential future use
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func  # For server-side date defaults

from .base_model import BaseModel


class Transaction(BaseModel):
    """
    Represents an individual billable event (charge, payment, adjustment).
    Each charge line item from the 'mini-spreadsheet' will be a Transaction.
    """

    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Unique transaction identifier",
    )

    horse_id = Column(
        Integer,
        ForeignKey("horses.horse_id"),
        nullable=False,
        index=True,
        doc="Horse associated with this transaction",
    )
    owner_id = Column(
        Integer,
        ForeignKey("owners.owner_id"),
        nullable=False,
        index=True,
        doc="Owner responsible for this transaction",
    )

    # CORRECTED ForeignKey to point to "charge_codes.id"
    charge_code_id = Column(
        Integer,
        ForeignKey("charge_codes.id"),
        nullable=True,
        index=True,
        doc="Charge code for this transaction (if applicable)",
    )

    transaction_type = Column(
        String(50),
        nullable=False,
        default="Charge",
        index=True,
        doc="Type of transaction (e.g., Charge, Payment, Adjustment)",
    )

    service_date = Column(
        Date,
        nullable=False,
        default=datetime.date.today,
        doc="Date the service was rendered or item sold",
    )
    billing_date = Column(
        Date,
        nullable=True,
        default=datetime.date.today,
        doc="Date for inclusion in a billing cycle/invoice",
    )

    description = Column(
        String(500),
        nullable=False,
        doc="Description of the transaction (can be pre-filled from ChargeCode, but editable)",
    )
    quantity = Column(
        Numeric(10, 3),
        nullable=False,
        default=1.000,
        doc="Quantity of items or services",
    )
    unit_price = Column(
        Numeric(10, 2),
        nullable=False,
        doc="Price per unit (can be pre-filled from ChargeCode, but editable)",
    )
    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
        doc="Calculated total amount (quantity * unit_price)",
    )

    administered_by_id = Column(
        String(20),
        ForeignKey("users.user_id"),
        nullable=True,
        doc="User ID of the person who administered/recorded the service",
    )

    notes = Column(
        Text, nullable=True, doc="Additional internal notes for this transaction"
    )
    print_on_statement = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag to indicate if notes/details should print on the owner's statement",
    )

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=True,
        index=True,
        doc="Invoice this transaction is part of (if billed)",
    )

    # Relationships
    horse = relationship("Horse")
    owner = relationship("Owner")
    charge_code = relationship("ChargeCode")
    administered_by_user = relationship("User")

    invoice = relationship("Invoice", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', horse_id={self.horse_id}, amount={self.total_amount})>"

    @staticmethod
    def calculate_total_amount(quantity: Numeric, unit_price: Numeric) -> Numeric:
        if quantity is None or unit_price is None:
            return Numeric("0.00")
        return quantity * unit_price


class Invoice(BaseModel):
    """
    Represents an invoice generated for an owner, grouping multiple transactions.
    """

    __tablename__ = "invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Unique invoice identifier",
    )
    invoice_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        doc="User-friendly invoice number (can be auto-generated)",
    )

    owner_id = Column(
        Integer,
        ForeignKey("owners.owner_id"),
        nullable=False,
        index=True,
        doc="Owner this invoice is for",
    )

    invoice_date = Column(
        Date,
        nullable=False,
        default=func.current_date(),
        doc="Date the invoice was generated",
    )
    due_date = Column(Date, nullable=True, doc="Date the invoice payment is due")

    subtotal_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        doc="Sum of all transaction totals before tax/discounts",
    )
    tax_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        doc="Total tax amount for the invoice",
    )
    discount_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        doc="Total discount amount for the invoice",
    )
    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        doc="Final amount due for the invoice (subtotal + tax - discount)",
    )
    amount_paid = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.00,
        doc="Total amount paid towards this invoice",
    )

    status = Column(
        String(50),
        nullable=False,
        default="Draft",
        index=True,
        doc="Status of the invoice (e.g., Draft, Sent, Paid, Partially Paid, Void)",
    )

    notes_to_owner = Column(
        Text,
        nullable=True,
        doc="Notes that will appear on the printed invoice for the owner",
    )
    internal_notes = Column(
        Text, nullable=True, doc="Internal notes about this invoice"
    )

    # Relationships
    owner = relationship("Owner", backref=backref("invoices", lazy="dynamic"))
    transactions = relationship(
        "Transaction",
        back_populates="invoice",
        cascade="all, delete-orphan",
        doc="Transactions included in this invoice",
    )

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', owner_id={self.owner_id}, total={self.total_amount}, status='{self.status}')>"

    @property
    def balance_due(self) -> Numeric:
        return (self.total_amount or Numeric("0.00")) - (
            self.amount_paid or Numeric("0.00")
        )
