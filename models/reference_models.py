# models/reference_models.py

"""
EDSI Veterinary Management System - Reference Data Models
Version: 1.1.4
Purpose: Defines various reference data models.
         Generic 'Payment' model is definitively removed.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.4 (2025-05-18):
    - Confirmed placeholder `Payment` class is removed.
- v1.1.3 (2025-05-18):
    - Ensured the placeholder `Payment` class is removed to avoid naming conflicts
      with `OwnerPayment` in `owner_models.py`.
- v1.1.2 (2025-05-18):
    - (Previous attempt to fix Payment.owner relationship)
- v1.1.1 (2025-05-18):
    - Added `from datetime import datetime` to resolve NameError for `datetime.utcnow`.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    DateTime,
    Text,
    ForeignKey,
    Date,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .base_model import BaseModel

# Import Owner model for the relationship in Invoice model (if needed, or use string)
# This import might cause circular dependency if Owner also imports from reference_models.
# It's often safer to use string names for relationship targets: relationship("Owner", ...)
# from .owner_models import Owner


class Species(BaseModel):
    __tablename__ = "species"
    species_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    def __repr__(self):
        return f"<Species(species_id={self.species_id}, name='{self.name}')>"


class StateProvince(BaseModel):
    __tablename__ = "state_provinces"
    state_code = Column(String(10), primary_key=True, index=True)
    state_name = Column(String(100), nullable=False, unique=True)
    country_code = Column(String(10))
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return (
            f"<StateProvince(state_code='{self.state_code}', name='{self.state_name}')>"
        )


class ChargeCode(BaseModel):
    __tablename__ = "charge_codes"
    charge_code_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    alternate_code = Column(String(50), nullable=True, index=True)
    description = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    standard_charge = Column(Numeric(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ChargeCode(code='{self.code}', description='{self.description}')>"


class Veterinarian(BaseModel):
    __tablename__ = "veterinarians"
    vet_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    license_number = Column(String(50), unique=True, nullable=True)
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Veterinarian(vet_id={self.vet_id}, name='{self.first_name} {self.last_name}')>"


class Location(BaseModel):
    __tablename__ = "locations"
    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return (
            f"<Location(location_id={self.location_id}, name='{self.location_name}')>"
        )


class Transaction(BaseModel):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_type = Column(String(50))
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True, index=True)
    transaction_date = Column(Date, default=datetime.utcnow)
    amount = Column(Numeric(10, 2), default=0.00)
    notes = Column(Text)
    # Relationships can be added here, e.g., to Owner, Horse
    # owner = relationship("Owner") # Requires Owner import or string "Owner"
    # horse = relationship("Horse") # Requires Horse import or string "Horse"


class TransactionDetail(BaseModel):
    __tablename__ = "transaction_details"
    transaction_detail_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    transaction_id = Column(
        Integer, ForeignKey("transactions.transaction_id"), nullable=False, index=True
    )
    charge_code_id = Column(
        Integer, ForeignKey("charge_codes.charge_code_id"), nullable=True, index=True
    )
    description = Column(String(255))
    quantity = Column(Numeric(10, 2), default=1.00)
    unit_price = Column(Numeric(10, 2), default=0.00)
    total_price = Column(Numeric(10, 2), default=0.00)
    # transaction = relationship("Transaction", backref="details")
    # charge_code = relationship("ChargeCode")


class Invoice(BaseModel):
    __tablename__ = "invoices"
    invoice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(
        Integer, ForeignKey("transactions.transaction_id"), nullable=True, index=True
    )  # Optional link to a master transaction
    owner_id = Column(
        Integer, ForeignKey("owners.owner_id"), nullable=False, index=True
    )
    invoice_date = Column(Date, nullable=False, default=datetime.utcnow)
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    # Relationship to Owner
    owner = relationship(
        "Owner", backref="invoices"
    )  # This assumes 'invoices' is a desired collection on Owner model


class Procedure(BaseModel):
    __tablename__ = "procedures"
    procedure_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_charge_code_id = Column(
        Integer, ForeignKey("charge_codes.charge_code_id"), nullable=True
    )
    charge_code = relationship("ChargeCode")  # Simple relationship


class Drug(BaseModel):
    __tablename__ = "drugs"
    drug_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_charge_code_id = Column(
        Integer, ForeignKey("charge_codes.charge_code_id"), nullable=True
    )
    charge_code = relationship("ChargeCode")  # Simple relationship


class TreatmentLog(BaseModel):
    __tablename__ = "treatment_logs"
    treatment_log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    horse_id = Column(
        Integer, ForeignKey("horses.horse_id"), nullable=False, index=True
    )
    vet_id = Column(
        Integer, ForeignKey("veterinarians.vet_id"), nullable=True, index=True
    )
    treatment_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=False)
    # horse = relationship("Horse", backref="treatment_logs")
    # veterinarian = relationship("Veterinarian")


class CommunicationLog(BaseModel):
    __tablename__ = "communication_logs"
    communication_log_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    related_to_type = Column(String(50))  # E.g., 'Horse', 'Owner'
    related_to_id = Column(Integer)  # ID of the horse or owner
    communication_date = Column(DateTime, default=datetime.utcnow)
    method = Column(String(50))  # E.g., 'Phone', 'Email'
    notes = Column(Text, nullable=False)
    user_id = Column(
        String(20), ForeignKey("users.user_id"), nullable=True
    )  # User who logged it
    # user = relationship("User")


class Document(BaseModel):
    __tablename__ = "documents"
    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    related_to_type = Column(String(50))
    related_to_id = Column(Integer)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # Relative or absolute path
    description = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)


class Reminder(BaseModel):
    __tablename__ = "reminders"
    reminder_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        String(20), ForeignKey("users.user_id"), nullable=False, index=True
    )
    horse_id = Column(Integer, ForeignKey("horses.horse_id"), nullable=True, index=True)
    reminder_date = Column(Date, nullable=False)
    reminder_time = Column(String(10), nullable=True)
    notes = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    # user = relationship("User", backref="reminders")
    # horse = relationship("Horse", backref="reminders")


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
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(
        String(50), default="Scheduled"
    )  # E.g., Scheduled, Completed, Cancelled
    # horse = relationship("Horse", backref="appointments")
    # owner = relationship("Owner", backref="appointments")
    # veterinarian = relationship("Veterinarian", backref="appointments")
