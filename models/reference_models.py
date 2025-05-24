# models/reference_models.py
"""
EDSI Veterinary Management System - Reference Data Models
Version: 1.1.16
Purpose: Defines SQLAlchemy models for various reference data entities.
         - Removed duplicate Invoice model definition (now solely in owner_models.py).
Last Updated: May 23, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.16 (2025-05-23):
    - Removed the placeholder `Invoice` class definition. The authoritative `Invoice`
      model is defined in `owner_models.py`. This resolves the "Table 'invoices' is
      already defined" error.
- v1.1.15 (2025-05-23):
    - Removed the `Species` class definition as it's not needed for this application.
- v1.1.14 (2025-05-23):
    - Location model: Temporarily commented out the `horses_at_location` relationship.
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
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base_model import Base, BaseModel


# Species class was REMOVED in v1.1.15


class StateProvince(BaseModel, Base):
    __tablename__ = "state_provinces"
    state_province_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    state_code = Column(String(10), nullable=False, unique=True, index=True)
    state_name = Column(String(50), nullable=False)
    country_code = Column(String(10), nullable=False, default="USA")
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return (
            f"<StateProvince(state_code='{self.state_code}', name='{self.state_name}')>"
        )


class ChargeCode(BaseModel, Base):
    __tablename__ = "charge_codes"
    charge_code_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=False)
    category = Column(String(50), index=True)
    standard_charge = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    taxable = Column(Boolean, default=False)

    def __repr__(self):
        return f"<ChargeCode(code='{self.code}', description='{self.description}')>"


class Veterinarian(BaseModel, Base):
    __tablename__ = "veterinarians"
    vet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False, index=True)
    license_number = Column(String(50), unique=True)
    specialty = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Veterinarian(vet_id={self.vet_id}, name='{self.first_name} {self.last_name}')>"


class Location(BaseModel, Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String(100), nullable=False, unique=True, index=True)
    address_line1 = Column(String(100), nullable=True)
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=True)
    state_code = Column(
        String(10), ForeignKey("state_provinces.state_code"), nullable=True, index=True
    )
    zip_code = Column(String(20), nullable=True)
    country_code = Column(String(10), default="USA", nullable=True)
    phone = Column(String(20), nullable=True)
    contact_person = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    state = relationship("StateProvince")

    # horses_at_location = relationship(
    # "Horse", secondary="horse_locations", back_populates="locations"
    # ) # Still commented out from previous diagnostic step

    current_horses = relationship("HorseLocation", back_populates="location")

    def __repr__(self):
        return (
            f"<Location(location_id={self.location_id}, name='{self.location_name}')>"
        )


class Transaction(BaseModel, Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True)
    description = Column(String(100))  # Basic placeholder


class TransactionDetail(BaseModel, Base):
    __tablename__ = "transaction_details"
    detail_id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))
    notes = Column(String(100))  # Basic placeholder


# REMOVED Invoice class definition from here. It is defined in owner_models.py
# class Invoice(BaseModel, Base):
#     __tablename__ = "invoices"
#     invoice_id = Column(Integer, primary_key=True)
#     owner_id = Column(Integer, ForeignKey("owners.owner_id"))
#     invoice_date = Column(Date, default=func.current_date)
#     total_amount = Column(Numeric(10,2))


class Procedure(BaseModel, Base):
    __tablename__ = "procedures"
    procedure_id = Column(Integer, primary_key=True)
    name = Column(String(100))  # Basic placeholder


class Drug(BaseModel, Base):
    __tablename__ = "drugs"
    drug_id = Column(Integer, primary_key=True)
    name = Column(String(100))  # Basic placeholder


class TreatmentLog(BaseModel, Base):
    __tablename__ = "treatment_logs"
    log_id = Column(Integer, primary_key=True)
    details = Column(String(255))  # Basic placeholder


class CommunicationLog(BaseModel, Base):
    __tablename__ = "communication_logs"
    log_id = Column(Integer, primary_key=True)
    summary = Column(String(255))  # Basic placeholder


class Document(BaseModel, Base):
    __tablename__ = "documents"
    document_id = Column(Integer, primary_key=True)
    file_path = Column(String(255))  # Basic placeholder


class Reminder(BaseModel, Base):
    __tablename__ = "reminders"
    reminder_id = Column(Integer, primary_key=True)
    due_date = Column(Date)  # Basic placeholder


class Appointment(BaseModel, Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True)
    vet_id = Column(Integer, ForeignKey("veterinarians.vet_id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=True)
    appointment_datetime = Column(DateTime, nullable=False, server_default=func.now())
    duration_minutes = Column(Integer, default=30)
    reason = Column(String(255))
    notes = Column(Text)
    status = Column(String(50), default="Scheduled")
    is_confirmed = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Appointment(id={self.appointment_id}, datetime='{self.appointment_datetime}', reason='{self.reason}')>"


# SystemConfig model is defined in user_models.py (as per user's v1.1.1)
