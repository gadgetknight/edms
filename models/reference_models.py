# models/reference_models.py
"""
EDSI Veterinary Management System - Reference Data Models
Version: 1.1.13
Purpose: Defines SQLAlchemy models for various reference tables.
         SystemConfig class definition removed to defer implementation.
Last Updated: May 23, 2025
Author: Gemini (based on user's v1.1.8 by Claude Assistant)

Changelog:
- v1.1.13 (2025-05-23):
    - Removed SystemConfig class definition.
- v1.1.8 (2025-05-20 - User Uploaded Version):
    - Further enhanced `Location` model to include:
        - address_line1, address_line2, city, state_code (ForeignKey),
          zip_code, country_code, phone, email, contact_person.
    - Ensured `state = relationship("StateProvince", backref="locations")` is present.
- v1.1.7 (2025-05-20):
    - Added `is_active = Column(Boolean, default=True, nullable=False)`
      to the `StateProvince` model.
- v1.1.6 (2025-05-19):
    - Added `from datetime import datetime` to resolve NameError for 'datetime'.
- v1.1.5 (2025-05-19):
    - Enhanced `Location` model (initial address fields).
- v1.1.4 (2025-05-18):
    - Removed GenericPayment model.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    Date,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class Species(BaseModel):
    __tablename__ = "species"
    species_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Species(species_id={self.species_id}, name='{self.name}')>"


class StateProvince(BaseModel):
    __tablename__ = "state_provinces"
    state_code = Column(String(10), primary_key=True, index=True)
    state_name = Column(String(100), nullable=False, unique=True)
    country_code = Column(String(10), nullable=False, default="USA")
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        return f"<StateProvince(state_code='{self.state_code}', state_name='{self.state_name}', is_active={self.is_active})>"


class ChargeCode(BaseModel):
    __tablename__ = "charge_codes"
    charge_code_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    alternate_code = Column(String(20), nullable=True, index=True)
    description = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True, index=True)
    standard_charge = Column(Numeric(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ChargeCode(code='{self.code}', description='{self.description}', charge={self.standard_charge})>"


class Veterinarian(BaseModel):
    __tablename__ = "veterinarians"
    vet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    license_number = Column(String(50), unique=True, nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Veterinarian(name='{self.first_name} {self.last_name}', license='{self.license_number}')>"


class Location(BaseModel):
    __tablename__ = "locations"
    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String(100), unique=True, nullable=False, index=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_code = Column(
        String(10), ForeignKey("state_provinces.state_code"), nullable=True, index=True
    )
    zip_code = Column(String(20), nullable=True)
    country_code = Column(String(10), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(100), nullable=True, index=True)
    contact_person = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    state = relationship("StateProvince", backref="locations")

    def __repr__(self):
        return (
            f"<Location(location_id={self.location_id}, name='{self.location_name}')>"
        )


# --- SystemConfig class definition is intentionally OMITTED from this file ---
# --- It will be added back when the user is ready to implement it. ---


# --- Transaction and Billing Related Models (from user's v1.1.8) ---
class Transaction(BaseModel):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_date = Column(
        Date, nullable=False, default=lambda: datetime.utcnow().date()
    )
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    notes = Column(Text, nullable=True)


class TransactionDetail(BaseModel):
    __tablename__ = "transaction_details"
    detail_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(
        Integer, ForeignKey("transactions.transaction_id"), nullable=False, index=True
    )
    charge_code_id = Column(
        Integer, ForeignKey("charge_codes.charge_code_id"), nullable=True, index=True
    )
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1.00)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)


class Invoice(BaseModel):
    __tablename__ = "invoices"
    invoice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    invoice_date = Column(
        Date, nullable=False, default=lambda: datetime.utcnow().date()
    )
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), default=0.00)
    status = Column(String(20), default="Unpaid")


# --- Medical Record Related Models (from user's v1.1.8) ---
class Procedure(BaseModel):
    __tablename__ = "procedures"
    procedure_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class Drug(BaseModel):
    __tablename__ = "drugs"
    drug_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class TreatmentLog(BaseModel):
    __tablename__ = "treatment_logs"
    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(
        Integer, ForeignKey("horses.horse_id"), nullable=False, index=True
    )
    vet_id = Column(
        Integer, ForeignKey("veterinarians.vet_id"), nullable=True, index=True
    )
    log_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=False)


class CommunicationLog(BaseModel):
    __tablename__ = "communication_logs"
    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    log_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    communication_type = Column(String(50))
    summary = Column(Text, nullable=False)
    follow_up_needed = Column(Boolean, default=False)


class Document(BaseModel):
    __tablename__ = "documents"
    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    document_type = Column(String(50))
    file_name = Column(String(255))
    file_path = Column(String(512))
    upload_date = Column(Date, default=lambda: datetime.utcnow().date())
    description = Column(Text, nullable=True)


class Reminder(BaseModel):
    __tablename__ = "reminders"
    reminder_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    reminder_date = Column(Date, nullable=False)
    reminder_type = Column(String(100))
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_date = Column(Date, nullable=True)


class Appointment(BaseModel):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    vet_id = Column(
        Integer, ForeignKey("veterinarians.vet_id"), nullable=True, index=True
    )
    appointment_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    reason = Column(String(255))
    status = Column(String(20), default="Scheduled")
    notes = Column(Text, nullable=True)
