# controllers/company_profile_controller.py
"""
EDSI Veterinary Management System - Company Profile Controller
Version: 1.0.0
Purpose: Business logic for managing the company's profile information.
Last Updated: June 8, 2025
Author: Gemini
"""

import logging
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.exc import SQLAlchemyError

from config.database_config import db_manager
from models import CompanyProfile


class CompanyProfileController:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_company_profile(self) -> Optional[CompanyProfile]:
        """
        Retrieves the company profile. Assumes a single profile with id=1.
        """
        session = db_manager().get_session()  # Corrected line
        try:
            profile = (
                session.query(CompanyProfile).filter(CompanyProfile.id == 1).first()
            )
            return profile
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving company profile: {e}", exc_info=True)
            return None
        finally:
            db_manager().close()  # Corrected line

    def update_company_profile(
        self, data: Dict[str, Any], current_user_id: str
    ) -> Tuple[bool, str]:
        """
        Creates or updates the company profile. Assumes a single profile with id=1.
        """
        session = db_manager().get_session()  # Corrected line
        try:
            profile = (
                session.query(CompanyProfile).filter(CompanyProfile.id == 1).first()
            )

            if not profile:
                self.logger.info("No existing company profile found. Creating new one.")
                profile = CompanyProfile(id=1, created_by=current_user_id)
                session.add(profile)

            for key, value in data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            profile.modified_by = current_user_id
            session.commit()
            self.logger.info(f"Company profile updated by {current_user_id}.")
            return True, "Company profile updated successfully."

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error updating company profile: {e}", exc_info=True
            )
            return False, f"A database error occurred: {e}"
        finally:
            db_manager().close()  # Corrected line
