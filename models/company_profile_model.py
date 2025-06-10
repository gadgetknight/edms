# models/company_profile_model.py
"""
EDSI Veterinary Management System - Company Profile Model
Version: 1.0.0
Purpose: Defines the data model for storing the clinic's own profile information.
Last Updated: June 8, 2025
Author: Gemini
"""

from sqlalchemy import Column, Integer, String, Text
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

    def __repr__(self):
        return f"<CompanyProfile(id={self.id}, name='{self.company_name}')>"
