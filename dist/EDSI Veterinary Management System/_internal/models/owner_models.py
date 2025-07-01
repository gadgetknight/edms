# models/owner_models.py
"""
EDSI Veterinary Management System - Owner Related Models
Version: 1.1.7
Purpose: Defines SQLAlchemy models for Owner and related entities.
         - Removed the placeholder Invoice model to avoid conflict with the
           definitive Invoice model in financial_models.py.
Last Updated: June 4, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.7 (2025-06-04):
    - Removed the placeholder `Invoice` class definition. The definitive `Invoice`
      model is now in `models/financial_models.py`.
      The backref from Owner to the new Invoice model is handled in financial_models.py.
- v1.1.6 (2025-05-23):
    - Ensured the `Invoice` class is correctly defined.
    - Imported `sqlalchemy.sql.func` for `func.current_date()` default in `Invoice.invoice_date`.
# ... (rest of previous changelog)
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
from sqlalchemy.sql import func
from datetime import datetime

from .base_model import BaseModel


class Owner(BaseModel):
    """Model for horse owners (master list)."""

    __tablename__ = "owners"

    # Changed owner_id to id for potential consistency, but will keep owner_id if it's deeply embedded.
    # For now, keeping owner_id as per existing structure.
    # If financial_models.Transaction.owner_id refers to 'owners.id', then this needs to be 'id'.
    # Checking financial_models.py: owner_id = Column(Integer, ForeignKey("owners.owner_id") ...
    # So, owner_id is correct here.
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

    # The 'invoices' backref is now defined in financial_models.Invoice linking to this Owner model.
    # No need for: # invoices = relationship("Invoice", back_populates="owner")

    def __repr__(self):
        display_name = (
            self.farm_name
            or f"{self.first_name or ''} {self.last_name or ''}".strip()
            or f"ID:{self.owner_id}"
        )
        return f"<Owner(owner_id={self.owner_id}, name='{display_name}')>"


class OwnerBillingHistory(BaseModel):
    """Billing history entries for an owner."""

    __tablename__ = "owner_billing_history"

    history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    entry_date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255), nullable=False)
    amount_change = Column(Numeric(10, 2), nullable=False)  # Made non-nullable
    new_balance = Column(Numeric(10, 2), nullable=False)  # Made non-nullable

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
    payment_date = Column(Date, nullable=False, default=func.current_date)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # Made non-nullable
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)  # Nullable is fine for notes

    owner = relationship(
        "Owner", foreign_keys=[owner_id], back_populates="payments_made"
    )

    def __repr__(self):
        return f"<OwnerPayment(owner_id={self.owner_id}, date='{self.payment_date}', amount={self.amount})>"


# class Invoice(BaseModel): # REMOVED - Definitive model is in financial_models.py
#    pass
