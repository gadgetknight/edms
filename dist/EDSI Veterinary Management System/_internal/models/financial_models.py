# models/financial_models.py
"""
EDSI Veterinary Management System - Financial Data Models
Version: 1.4.0
Purpose: Defines SQLAlchemy models for financial records like Transactions and Invoices.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v1.4.0 (2025-06-28):
    - [cite_start]Added `monthly_sequence_number` (Integer) and `invoice_period_ym` (String) columns to `Invoice` model. [cite: 584, 585, 587]
    - Implemented `display_invoice_id` as a `hybrid_property` in the `Invoice` model to generate
      [cite_start]a human-readable invoice number in the format `OWNER_ACCT-YYMM-SEQ` (e.g., `WC001-2506-0001`). [cite: 584, 585, 587]
    - [cite_start]Updated `Invoice.__repr__` to use the new `display_invoice_id` for better debugging. [cite: 584, 585, 587]
- v1.3.0 (2025-06-09):
    - Set `autoincrement=True` on the Invoice.invoice_id primary key to ensure
      [cite_start]the database engine never reuses an invoice number after it has been deleted. [cite: 584, 585]
- v1.2.0 (2025-06-09):
    - Added a `status` column to the `Transaction` model to explicitly track
      [cite_start]whether a charge is active or has been processed into an invoice. [cite: 585, 586, 587]
- v1.1.0 (2025-06-05):
    - [cite_start]Added `taxable` (Boolean) and `item_notes` (Text) columns to the `Transaction` model. [cite: 585, 586, 587]
    - [cite_start]Added `tax_total` (Numeric) column to the `Invoice` model. [cite: 585, 587]
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
from sqlalchemy.ext.hybrid import hybrid_property  # Added for display_invoice_id

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

    charge_code_id = Column(
        Integer, ForeignKey("charge_codes.id"), nullable=False, index=True
    )

    administered_by_user_id = Column(
        String(20), ForeignKey("users.user_id"), nullable=True
    )

    transaction_date = Column(Date, nullable=False, default=date.today)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    taxable = Column(Boolean, default=False, nullable=False)
    item_notes = Column(Text, nullable=True)

    status = Column(String(50), nullable=False, default="ACTIVE", index=True)

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

    invoice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )

    invoice_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=True)

    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax_total = Column(Numeric(10, 2), nullable=True)
    grand_total = Column(Numeric(10, 2), nullable=False, default=0.00)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0.00)
    balance_due = Column(Numeric(10, 2), nullable=False, default=0.00)

    status = Column(String(50), nullable=False, default="Unpaid", index=True)

    # NEW: Fields for derived invoice number format
    invoice_period_ym = Column(
        String(4),
        nullable=True,
        index=True,
        doc="Year and Month of invoice for sequencing (YYMM)",
    )
    monthly_sequence_number = Column(
        Integer,
        nullable=True,
        index=True,
        doc="Sequence number within the month for this owner",
    )

    # Relationships
    owner = relationship("Owner", backref="invoices")
    transactions = relationship(
        "Transaction", back_populates="invoice", cascade="all, delete-orphan"
    )

    @hybrid_property
    def display_invoice_id(self):
        """
        Generates a human-readable invoice ID.
        Format: OWNER_ACCT-YYMM-SEQ (e.g., WC001-2506-0001)
        """
        owner_prefix = "NOACCT"
        if self.owner:
            owner_prefix = self.owner.account_number or f"OWNER{self.owner.owner_id}"

        ym_part = self.invoice_period_ym or self.invoice_date.strftime("%y%m")
        seq_part = (
            f"{self.monthly_sequence_number:04d}"
            if self.monthly_sequence_number is not None
            else "0000"
        )

        return f"{owner_prefix}-{ym_part}-{seq_part}"

    def __repr__(self):
        # Updated to use the new display_invoice_id
        return f"<Invoice(id={self.invoice_id}, display_id='{self.display_invoice_id}', owner_id={self.owner_id}, total={self.grand_total}, status='{self.status}')>"
