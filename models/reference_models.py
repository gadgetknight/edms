# models/reference_models.py
"""
EDSI Veterinary Management System - Reference Data Models
Version: 1.1.19
Purpose: Defines SQLAlchemy models for various reference data entities.
         - Added ChargeCodeCategory model for hierarchical categories.
         - Modified ChargeCode model to use ForeignKey to ChargeCodeCategory.
Last Updated: June 2, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.19 (2025-06-02):
    - Added new `ChargeCodeCategory` model with `category_id`, `name`,
      `parent_id` (self-referential for hierarchy), `level`, and `is_active` fields.
      Inherits from `BaseModel`.
    - Modified `ChargeCode` model:
        - Removed the existing `category` (String) field.
        - Added `category_id` (Integer, ForeignKey to `charge_code_categories.category_id`).
        - Added `category` relationship to `ChargeCodeCategory`.
- v1.1.18 (2025-06-02):
    - Added `email = Column(String(100), nullable=True)` to the `Location` model.
- v1.1.17 (2025-05-31):
    - Added `alternate_code` to the `ChargeCode` model.
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
    Table,  # Retain for potential future use, though not directly used by these models
)
from sqlalchemy.orm import (
    relationship,
    backref,
)  # Added backref for self-referential relationship
from sqlalchemy.sql import func

from .base_model import Base, BaseModel


class StateProvince(BaseModel, Base):  # Unchanged
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


# ADDED: New ChargeCodeCategory model
class ChargeCodeCategory(BaseModel, Base):
    __tablename__ = "charge_code_categories"

    category_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Unique category identifier",
    )
    name = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Name of the category level (e.g., 'Veterinary', 'Anthelmintics')",
    )
    parent_id = Column(
        Integer,
        ForeignKey("charge_code_categories.category_id"),
        nullable=True,
        index=True,
        doc="ID of the parent category, if any",
    )
    level = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Hierarchy level (e.g., 1 for main, 2 for sub, 3 for detail)",
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Self-referential relationship for parent-child hierarchy
    parent = relationship(
        "ChargeCodeCategory",
        remote_side=[category_id],
        backref=backref("children", lazy="dynamic"),
    )

    # Relationship to ChargeCodes (one category can have many charge codes if linking this way)
    # If a ChargeCode links to its most specific category, this relationship might be less direct here,
    # or could be defined on ChargeCode as many-to-one.
    # For now, let's define the link from ChargeCode to ChargeCodeCategory.

    def __repr__(self):
        return f"<ChargeCodeCategory(id={self.category_id}, name='{self.name}', level={self.level}, parent_id={self.parent_id})>"


class ChargeCode(BaseModel, Base):
    __tablename__ = "charge_codes"
    charge_code_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    alternate_code = Column(String(50), nullable=True, index=True)
    description = Column(String(255), nullable=False)

    # REMOVED: category = Column(String(50), index=True)
    # ADDED: ForeignKey to the new ChargeCodeCategory table
    category_id = Column(
        Integer,
        ForeignKey("charge_code_categories.category_id"),
        nullable=True,
        index=True,
    )

    standard_charge = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    taxable = Column(Boolean, default=False)

    # ADDED: Relationship to ChargeCodeCategory
    category = relationship("ChargeCodeCategory")

    def __repr__(self):
        return f"<ChargeCode(code='{self.code}', description='{self.description}')>"


class Veterinarian(BaseModel, Base):  # Unchanged
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


class Location(BaseModel, Base):  # Unchanged from v1.1.18
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
    email = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    state = relationship("StateProvince")
    current_horses = relationship("HorseLocation", back_populates="location")

    def __repr__(self):
        return (
            f"<Location(location_id={self.location_id}, name='{self.location_name}')>"
        )


# ... (Other models: Transaction, TransactionDetail, Procedure, Drug, etc. remain unchanged) ...
class Transaction(BaseModel, Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True)
    description = Column(String(100))


class TransactionDetail(BaseModel, Base):
    __tablename__ = "transaction_details"
    detail_id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"))
    notes = Column(String(100))


class Procedure(BaseModel, Base):
    __tablename__ = "procedures"
    procedure_id = Column(Integer, primary_key=True)
    name = Column(String(100))


class Drug(BaseModel, Base):
    __tablename__ = "drugs"
    drug_id = Column(Integer, primary_key=True)
    name = Column(String(100))


class TreatmentLog(BaseModel, Base):
    __tablename__ = "treatment_logs"
    log_id = Column(Integer, primary_key=True)
    details = Column(String(255))


class CommunicationLog(BaseModel, Base):
    __tablename__ = "communication_logs"
    log_id = Column(Integer, primary_key=True)
    summary = Column(String(255))


class Document(BaseModel, Base):
    __tablename__ = "documents"
    document_id = Column(Integer, primary_key=True)
    file_path = Column(String(255))


class Reminder(BaseModel, Base):
    __tablename__ = "reminders"
    reminder_id = Column(Integer, primary_key=True)
    due_date = Column(Date)


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
