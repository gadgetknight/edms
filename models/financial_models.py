# models/financial_models.py
"""
EDSI Veterinary Management System - Financial Data Models
Version: 1.1.0
Purpose: Defines SQLAlchemy models for financial records like Transactions and Invoices.
         - Added fields for per-line taxable flag, item notes, and total invoice tax.
Last Updated: June 5, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-05):
    - Added `taxable` (Boolean) and `item_notes` (Text) columns to the `Transaction`
      model to support per-item tax flagging and notes.
    - Added `tax_total` (Numeric) column to the `Invoice` model to store the
      manually entered total tax amount for an invoice.
- v1.0.0 (2025-06-04):
    - Initial creation of definitive Transaction and Invoice models.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    Date,
    Numeric,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date

from .base_model import BaseModel


class Transaction(BaseModel):
    """
    Represents a single billable line item for a horse.
    This is the core of all financial activity.
    """

    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(
        Integer, ForeignKey("horses.horse_id"), nullable=False, index=True
    )
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    invoice_id = Column(
        Integer, ForeignKey("invoices.invoice_id"), nullable=True, index=True
    )

    # Links to the specific charge code from the reference table
    charge_code_id = Column(
        Integer, ForeignKey("charge_codes.id"), nullable=False, index=True
    )

    # Who administered or recorded the charge
    administered_by_user_id = Column(
        String(20), ForeignKey("users.user_id"), nullable=True
    )

    transaction_date = Column(Date, nullable=False, default=date.today)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # New fields for enhanced billing UI
    taxable = Column(Boolean, default=False, nullable=False)
    item_notes = Column(Text, nullable=True)

    # Relationships
    horse = relationship("Horse")
    owner = relationship("Owner")
    invoice = relationship("Invoice", back_populates="transactions")
    charge_code = relationship("ChargeCode")
    administered_by = relationship("User")

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, horse_id={self.horse_id}, total={self.total_price})>"


class Invoice(BaseModel):
    """
    Represents a bill sent to an owner, grouping multiple transactions.
    """

    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )

    invoice_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=True)

    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)

    # New field for manually entered tax
    tax_total = Column(Numeric(10, 2), nullable=True)

    grand_total = Column(Numeric(10, 2), nullable=False, default=0.00)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0.00)
    balance_due = Column(Numeric(10, 2), nullable=False, default=0.00)

    status = Column(
        String(50), nullable=False, default="Unpaid", index=True
    )  # e.g., Unpaid, Paid, Overdue, Void

    # Relationships
    owner = relationship("Owner", backref="invoices")
    transactions = relationship(
        "Transaction", back_populates="invoice", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice(id={self.invoice_id}, owner_id={self.owner_id}, total={self.grand_total}, status='{self.status}')>"
