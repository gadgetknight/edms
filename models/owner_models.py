# models/owner_models.py
"""
EDSI Veterinary Management System - Owner Related Models
Version: 1.1.6
Purpose: Defines SQLAlchemy models for Owner and related entities.
         - Ensured Invoice model is correctly defined and func is imported for date default.
Last Updated: May 23, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.6 (2025-05-23):
    - Ensured the `Invoice` class is correctly defined.
    - Imported `sqlalchemy.sql.func` for `func.current_date()` default in `Invoice.invoice_date`.
- v1.1.5 (2025-05-23):
    - Owner.horses (many-to-many): Added `viewonly=True` to prevent conflicts
      with other relationships managing the `horse_owners` association table,
      addressing SQLAlchemy overlap warnings.
- v1.1.4 (2025-05-23):
    - Renamed the direct relationship from Owner to HorseOwner objects
      from `horses` to `horse_associations` for clarity and consistency.
    - Added a new many-to-many relationship `Owner.horses` (linking to Horse objects)
      to correctly pair with `Horse.owners`.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    Text,
    ForeignKey,
    Date,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # Added for func.current_date()
from datetime import (
    datetime,
)  # Keep for default values if not using sqlalchemy.sql.func

from .base_model import BaseModel


class Owner(BaseModel):
    """Model for horse owners (master list)."""

    __tablename__ = "owners"

    owner_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account_number = Column(String(20), unique=True, nullable=True, index=True)
    farm_name = Column(String(100), nullable=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True, index=True)

    address_line1 = Column(String(100))
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50))

    state_code = Column(
        String(10), ForeignKey("state_provinces.state_code"), index=True
    )

    zip_code = Column(String(20))

    phone = Column(String(20), nullable=True)
    mobile_phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True, index=True)

    is_active = Column(Boolean, default=True, nullable=False)

    balance = Column(Numeric(10, 2), default=0.00)
    credit_limit = Column(Numeric(10, 2), nullable=True)
    billing_terms = Column(String(50), nullable=True)
    service_charge_rate = Column(Numeric(5, 2), nullable=True)
    discount_rate = Column(Numeric(5, 2), nullable=True)

    notes = Column(Text, nullable=True)

    state = relationship("StateProvince", foreign_keys=[state_code], backref="owners")

    horse_associations = relationship(
        "HorseOwner", back_populates="owner", cascade="all, delete-orphan"
    )

    horses = relationship(
        "Horse", secondary="horse_owners", back_populates="owners", viewonly=True
    )

    billing_history = relationship(
        "OwnerBillingHistory", back_populates="owner", cascade="all, delete-orphan"
    )
    payments_made = relationship(
        "OwnerPayment", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self):
        display_name = (
            self.farm_name
            or f"{self.first_name or ''} {self.last_name or ''}".strip()
            or f"ID:{self.owner_id}"
        )
        return f"<Owner(owner_id={self.owner_id}, name='{display_name}')>"


class OwnerBillingHistory(BaseModel):
    """Billing history entries for an owner."""  # Corrected docstring slightly

    __tablename__ = "owner_billing_history"

    history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    entry_date = Column(
        DateTime, default=datetime.utcnow
    )  # sqlalchemy.sql.func.now() is better for server default
    description = Column(String(255), nullable=False)
    amount_change = Column(Numeric(10, 2))  # Should probably be nullable=False
    new_balance = Column(Numeric(10, 2))  # Should probably be nullable=False

    owner = relationship("Owner", back_populates="billing_history")

    def __repr__(self):
        return f"<OwnerBillingHistory(owner_id={self.owner_id}, date='{self.entry_date}', desc='{self.description}')>"


class OwnerPayment(BaseModel):
    """Payments made by an owner."""

    __tablename__ = "owner_payments"

    payment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    payment_date = Column(Date, nullable=False, default=func.current_date)  # Using func
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50))  # Consider nullable=False if always present
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text)

    owner = relationship(
        "Owner", foreign_keys=[owner_id], back_populates="payments_made"
    )

    def __repr__(self):
        return f"<OwnerPayment(owner_id={self.owner_id}, date='{self.payment_date}', amount={self.amount})>"


class Invoice(BaseModel):  # Ensured Invoice model is present
    """Invoices for an owner."""

    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    invoice_date = Column(Date, nullable=False, default=func.current_date)  # Using func
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0.00)
    status = Column(
        String(50), nullable=False, default="Draft"
    )  # E.g., Draft, Sent, Paid, Void

    # If Invoice can have multiple TransactionDetails or line items, define relationship here
    # details = relationship("TransactionDetail", back_populates="invoice") # Example

    # Relationship to Owner
    # owner = relationship("Owner", back_populates="invoices") # Add 'invoices' to Owner model if needed

    def __repr__(self):
        return f"<Invoice(invoice_id={self.invoice_id}, owner_id={self.owner_id}, total={self.total_amount}, status='{self.status}')>"
