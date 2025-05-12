# models/owner_models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class Owner(BaseModel):
    """Owner master file"""

    __tablename__ = "owners"

    owner_id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(20), unique=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50))
    farm_name = Column(String(100))
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state_code = Column(String(10), ForeignKey("states_provinces.state_code"))
    zip_code = Column(String(20))
    phone = Column(String(20))
    mobile_phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0)
    credit_limit = Column(Float, default=0)
    billing_terms = Column(String(50))
    service_charge_rate = Column(Float)
    discount_rate = Column(Float)

    # Relationships
    state = relationship("StateProvince")
    horses = relationship("HorseOwner", back_populates="owner")
    billing_history = relationship("OwnerBillingHistory", back_populates="owner")
    payments = relationship("OwnerPayment", back_populates="owner")


class OwnerBillingHistory(BaseModel):
    """Owner billing history"""

    __tablename__ = "owner_billing_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    charge_date = Column(DateTime)
    charge_code = Column(String(20), ForeignKey("charge_codes.charge_code"))
    description = Column(String(255))
    units = Column(Float)
    amount = Column(Float)
    balance_after = Column(Float)
    billing_period = Column(String(20))
    is_paid = Column(Boolean, default=False)
    payment_date = Column(DateTime)

    # Relationships
    owner = relationship("Owner", back_populates="billing_history")
    charge = relationship("ChargeCode")


class OwnerPayment(BaseModel):
    """Owner payments"""

    __tablename__ = "owner_payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    payment_date = Column(DateTime)
    amount = Column(Float)
    payment_method = Column(String(50))
    reference_number = Column(String(50))
    notes = Column(String(255))

    # Relationships
    owner = relationship("Owner", back_populates="payments")
