"""
EDSI Veterinary Management System - Initial Data Setup
Version: 1.0.0
Purpose: Adds initial reference data to the database for testing purposes.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.0 (2025-05-12): Initial implementation
  - Added sample species data
  - Added sample locations
  - Added sample charge codes
  - Added sample veterinarians
  - Added sample states/provinces
"""

# scripts/add_initial_data.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database_config import db_manager
from models import Species, StateProvince, ChargeCode, Veterinarian, Location


def add_initial_data():
    """Add initial reference data to the database"""
    print("Adding initial reference data...")

    # Initialize database
    db_manager.initialize_database()
    session = db_manager.get_session()

    try:
        # Add species
        species_data = [
            ("EQ", "Equine"),
            ("BO", "Bovine"),
            ("CA", "Canine"),
            ("FE", "Feline"),
            ("OV", "Ovine"),
            ("PO", "Porcine"),
            ("AV", "Avian"),
        ]

        for code, name in species_data:
            if not session.query(Species).filter(Species.species_code == code).first():
                species = Species(species_code=code, species_name=name)
                session.add(species)

        # Add states/provinces
        states_data = [
            ("AL", "Alabama"),
            ("AK", "Alaska"),
            ("AZ", "Arizona"),
            ("AR", "Arkansas"),
            ("CA", "California"),
            ("CO", "Colorado"),
            ("CT", "Connecticut"),
            ("DE", "Delaware"),
            ("FL", "Florida"),
            ("GA", "Georgia"),
            ("HI", "Hawaii"),
            ("ID", "Idaho"),
            ("IL", "Illinois"),
            ("IN", "Indiana"),
            ("IA", "Iowa"),
            ("KS", "Kansas"),
            ("KY", "Kentucky"),
            ("LA", "Louisiana"),
            ("ME", "Maine"),
            ("MD", "Maryland"),
            ("MA", "Massachusetts"),
            ("MI", "Michigan"),
            ("MN", "Minnesota"),
            ("MS", "Mississippi"),
            ("MO", "Missouri"),
            ("MT", "Montana"),
            ("NE", "Nebraska"),
            ("NV", "Nevada"),
            ("NH", "New Hampshire"),
            ("NJ", "New Jersey"),
            ("NM", "New Mexico"),
            ("NY", "New York"),
            ("NC", "North Carolina"),
            ("ND", "North Dakota"),
            ("OH", "Ohio"),
            ("OK", "Oklahoma"),
            ("OR", "Oregon"),
            ("PA", "Pennsylvania"),
            ("RI", "Rhode Island"),
            ("SC", "South Carolina"),
            ("SD", "South Dakota"),
            ("TN", "Tennessee"),
            ("TX", "Texas"),
            ("UT", "Utah"),
            ("VT", "Vermont"),
            ("VA", "Virginia"),
            ("WA", "Washington"),
            ("WV", "West Virginia"),
            ("WI", "Wisconsin"),
            ("WY", "Wyoming"),
        ]

        for code, name in states_data:
            if (
                not session.query(StateProvince)
                .filter(StateProvince.state_code == code)
                .first()
            ):
                state = StateProvince(state_code=code, state_name=name)
                session.add(state)

        # Add sample locations
        locations_data = [
            ("Main Barn", "123 Farm Road", "", "Lexington", "KY", "40508"),
            ("Paddock A", "Front Pasture", "", "Lexington", "KY", "40508"),
            ("Paddock B", "Back Pasture", "", "Lexington", "KY", "40508"),
            ("Quarantine Barn", "Isolation Area", "", "Lexington", "KY", "40508"),
            ("Training Facility", "Exercise Arena", "", "Lexington", "KY", "40508"),
        ]

        for name, addr1, addr2, city, state, zip_code in locations_data:
            if (
                not session.query(Location)
                .filter(Location.location_name == name)
                .first()
            ):
                location = Location(
                    location_name=name,
                    address_line1=addr1,
                    address_line2=addr2,
                    city=city,
                    state_code=state,
                    zip_code=zip_code,
                )
                session.add(location)

        # Add sample charge codes
        charge_codes_data = [
            ("EXAM", "Medical", "Routine Examination", 1.0, 75.00),
            ("VACC", "Medical", "Vaccination", 1.0, 45.00),
            ("BOARD", "Boarding", "Daily Boarding Fee", 1.0, 35.00),
            ("SHOE", "Farrier", "Shoeing", 4.0, 120.00),
            ("TRIM", "Farrier", "Hoof Trimming", 4.0, 60.00),
            ("DENTAL", "Medical", "Dental Work", 1.0, 150.00),
            ("LAB", "Medical", "Laboratory Testing", 1.0, 85.00),
            ("XRAY", "Medical", "X-Ray", 1.0, 125.00),
            ("SURGERY", "Medical", "Surgical Procedure", 1.0, 500.00),
            ("MEDICATION", "Medical", "Medication", 1.0, 25.00),
        ]

        for code, category, desc, units, amount in charge_codes_data:
            if (
                not session.query(ChargeCode)
                .filter(ChargeCode.charge_code == code)
                .first()
            ):
                charge = ChargeCode(
                    charge_code=code,
                    category=category,
                    description=desc,
                    default_units=units,
                    default_amount=amount,
                )
                session.add(charge)

        # Add sample veterinarians
        vets_data = [
            ("DR001", "Johnson", "Sarah", "Dr. Sarah Johnson, DVM"),
            ("DR002", "Williams", "Michael", "Dr. Michael Williams, DVM"),
            ("DR003", "Brown", "Emily", "Dr. Emily Brown, DVM"),
            ("DR004", "Davis", "Robert", "Dr. Robert Davis, DVM"),
        ]

        for vet_id, last, first, full in vets_data:
            if (
                not session.query(Veterinarian)
                .filter(Veterinarian.vet_id == vet_id)
                .first()
            ):
                vet = Veterinarian(
                    vet_id=vet_id,
                    last_name=last,
                    first_name=first,
                    full_name=full,
                    phone="555-0123",
                    email=f"{first.lower()}.{last.lower()}@vetclinic.com",
                )
                session.add(vet)

        # Commit all changes
        session.commit()
        print("Initial data added successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error adding initial data: {e}")
    finally:
        session.close()
        db_manager.close()


if __name__ == "__main__":
    add_initial_data()
