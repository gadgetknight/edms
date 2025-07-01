# models/company_profile_model.py
"""
EDSI Veterinary Management System - Company Profile Model
Version: 1.0.1
Purpose: Defines the data model for storing the clinic's own profile information.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-06-28):
    - Added `use_stripe_payments` (Boolean) column to allow enabling/disabling
      Stripe payment link generation from the application settings.
- v1.0.0 (2025-06-08):
    - Initial creation of the model.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean
from .base_model import BaseModel


class CompanyProfile(BaseModel):
    """
    Represents the company's profile information.
    This table is expected to contain only a single row (id=1).
    """

    __tablename__ = "company_profile"

    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    logo_path = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)

    # NEW: Stripe payment integration toggle
    use_stripe_payments = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="If true, enables Stripe payment link generation features.",
    )

    def __repr__(self):
        return f"<CompanyProfile(id={self.id}, name='{self.company_name}')>"
