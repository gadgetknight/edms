# models/owner_models.py

"""
EDSI Veterinary Management System - Owner Related Models
Version: 1.1.3
Purpose: Defines SQLAlchemy models for Owner and related entities.
         Explicitly sets foreign_keys for OwnerPayment.owner relationship.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.3 (2025-05-18):
    - Added `foreign_keys=[OwnerPayment.owner_id]` to the `OwnerPayment.owner` relationship.
- v1.1.2 (2025-05-18):
    - Ensured Owner.payments_made relationship targets "OwnerPayment".
    - Ensured OwnerPayment.owner relationship correctly back_populates "payments_made".
- v1.1.1 (2025-05-18):
    - Added `DateTime` to the import from `sqlalchemy` to resolve NameError.
- v1.1.0 (2025-05-18):
    - Added `foreign_keys=[Owner.state_code]` to the `Owner.state` relationship.
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
from datetime import datetime

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
    horses = relationship(
        "HorseOwner", back_populates="owner", cascade="all, delete-orphan"
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
    """Placeholder for owner's billing history entries."""

    __tablename__ = "owner_billing_history"

    history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    entry_date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255), nullable=False)
    amount_change = Column(Numeric(10, 2))
    new_balance = Column(Numeric(10, 2))

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
    payment_date = Column(Date, nullable=False, default=datetime.utcnow)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50))
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text)

    # --- MODIFIED RELATIONSHIP: Explicitly state foreign_keys ---
    owner = relationship(
        "Owner", foreign_keys=[owner_id], back_populates="payments_made"
    )
    # --- END MODIFICATION ---

    def __repr__(self):
        return f"<OwnerPayment(owner_id={self.owner_id}, date='{self.payment_date}', amount={self.amount})>"
