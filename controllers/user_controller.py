# controllers/user_controller.py

"""
EDSI Veterinary Management System - User Controller
Version: 1.1.1
Purpose: Handles user authentication, CRUD operations, and role management.
         Modified validate_password to return a dict to avoid DetachedInstanceError.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.1 (2025-05-18):
    - Modified `validate_password` to return a dictionary of user details
      (user_id, is_active) instead of the ORM object to prevent DetachedInstanceError.
- v1.1.0 (User-Provided Version): Initial version with hashlib and validate_password.
"""

import logging
import hashlib
from typing import List, Optional, Tuple, Dict  # Added Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime  # Ensure datetime is imported for last_login

from config.database_config import db_manager
from models import User, Role, UserRole


class UserController:
    """Controller for user management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.lower().encode("utf-8")).hexdigest()

    def validate_password(
        self, user_id: str, password_attempt: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validates a user's password attempt.
        Returns: (is_valid, message, user_details_dict_if_valid_else_None)
        user_details_dict contains 'user_id' and 'is_active'.
        """
        self.logger.debug(f"Attempting to validate password for user: {user_id}")
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id.upper()).first()
            if not user:
                self.logger.warning(
                    f"User '{user_id}' not found during password validation."
                )
                return False, "Invalid User ID or Password.", None

            hashed_attempt = self._hash_password(password_attempt)
            if user.password_hash != hashed_attempt:
                self.logger.warning(f"Incorrect password attempt for user '{user_id}'.")
                return False, "Invalid User ID or Password.", None

            # Password is correct.
            # Capture necessary attributes before session closes.
            user_is_active = user.is_active
            actual_user_id = (
                user.user_id
            )  # Get the exact case from DB if needed, though we used .upper()

            if not user_is_active:
                self.logger.warning(f"Login attempt for inactive user '{user_id}'.")
                # Return user details even if inactive, for the dialog to handle the message.
                return (
                    False,
                    f"User account '{user_id}' is inactive.",
                    {"user_id": actual_user_id, "is_active": user_is_active},
                )

            # Update last_login for active user
            user.last_login = datetime.utcnow()
            session.commit()

            self.logger.info(
                f"Password validated successfully for active user '{user_id}'."
            )
            return (
                True,
                "Login successful.",
                {"user_id": actual_user_id, "is_active": user_is_active},
            )
        except Exception as e:
            session.rollback()  # Ensure rollback on error
            self.logger.error(
                f"Error during password validation for user '{user_id}': {e}",
                exc_info=True,
            )
            return False, "An error occurred during login. Please try again.", None
        finally:
            session.close()

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        session = db_manager.get_session()
        try:
            query = session.query(User)
            if not include_inactive:
                query = query.filter(User.is_active == True)
            users = query.order_by(User.user_id).all()
            return users
        except Exception as e:
            self.logger.error(f"Error fetching all users: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id.upper()).first()
            return user
        except Exception as e:
            self.logger.error(
                f"Error fetching user by ID '{user_id}': {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def validate_user_data(
        self,
        user_data: dict,
        is_new: bool = True,
        original_user_id: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        errors = []
        user_id = user_data.get("user_id", "").strip().upper()
        user_name = user_data.get("user_name", "").strip()
        password = user_data.get("password", "")

        if not user_id:
            errors.append("User ID is required.")
        elif len(user_id) > 20:
            errors.append("User ID cannot exceed 20 characters.")
        elif " " in user_id:
            errors.append("User ID cannot contain spaces.")
        elif is_new:
            existing_user = self.get_user_by_id(user_id)
            if existing_user:
                errors.append(f"User ID '{user_id}' already exists.")

        if not user_name:
            errors.append("User Name is required.")
        elif len(user_name) > 100:
            errors.append("User Name cannot exceed 100 characters.")

        if is_new:
            if not password:
                errors.append("Password is required for new users.")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters long.")

        return len(errors) == 0, errors

    def create_user(self, user_data: dict) -> Tuple[bool, str, Optional[User]]:
        is_valid, errors = self.validate_user_data(user_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            user_id = user_data["user_id"].strip().upper()
            password = user_data["password"]
            password_hash = self._hash_password(password)

            new_user = User(
                user_id=user_id,
                user_name=user_data["user_name"].strip(),
                password_hash=password_hash,
                is_active=user_data.get("is_active", True),
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            self.logger.info(f"User '{new_user.user_id}' created successfully.")
            return True, "User created successfully.", new_user
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error creating user '{user_data.get('user_id')}': {e}", exc_info=True
            )
            if "UNIQUE constraint failed" in str(e).upper():
                return False, f"User ID '{user_data['user_id']}' already exists.", None
            return False, f"Failed to create user: {e}", None
        finally:
            session.close()

    def update_user(self, user_id_orig: str, user_data: dict) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            user_to_update_id = user_id_orig.upper()
            user = session.query(User).filter(User.user_id == user_to_update_id).first()
            if not user:
                return False, f"User '{user_to_update_id}' not found."

            temp_validation_data = {"user_id": user_to_update_id}
            if "user_name" in user_data:
                temp_validation_data["user_name"] = user_data["user_name"]

            is_valid, errors = self.validate_user_data(
                temp_validation_data, is_new=False
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            if "user_name" in user_data:
                user.user_name = user_data["user_name"].strip()
            if "is_active" in user_data:
                if user.user_id == "ADMIN" and not user_data["is_active"]:
                    active_admin_count = (
                        session.query(func.count(User.user_id))
                        .filter(User.is_active == True, User.user_id == "ADMIN")
                        .scalar()
                    )
                    if active_admin_count <= 1:
                        self.logger.warning(
                            f"Attempt to deactivate the last active ADMIN user ('{user_to_update_id}') was prevented."
                        )
                        return False, "Cannot deactivate the last active ADMIN user."
                user.is_active = user_data["is_active"]

            session.commit()
            self.logger.info(f"User '{user.user_id}' updated successfully.")
            return True, "User updated successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating user '{user_id_orig}': {e}", exc_info=True
            )
            return False, f"Failed to update user: {e}"
        finally:
            session.close()

    def change_password(self, user_id: str, new_password: str) -> Tuple[bool, str]:
        if not new_password or len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id.upper()).first()
            if not user:
                return False, f"User '{user_id}' not found."

            new_password_hash = self._hash_password(new_password)
            user.password_hash = new_password_hash
            session.commit()
            self.logger.info(f"Password changed successfully for user '{user_id}'.")
            return True, "Password changed successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error changing password for user '{user_id}': {e}", exc_info=True
            )
            return False, f"Failed to change password: {e}"
        finally:
            session.close()

    def delete_user_permanently(
        self, user_id_to_delete: str, current_admin_id: str
    ) -> Tuple[bool, str]:
        user_id_to_delete_upper = user_id_to_delete.upper()
        current_admin_id_upper = current_admin_id.upper()

        if user_id_to_delete_upper == current_admin_id_upper:
            self.logger.warning(
                f"Admin user '{current_admin_id_upper}' attempted to delete themselves."
            )
            return False, "Cannot delete the currently logged-in user."

        session = db_manager.get_session()
        try:
            user_to_delete = (
                session.query(User)
                .filter(User.user_id == user_id_to_delete_upper)
                .first()
            )
            if not user_to_delete:
                return False, f"User '{user_id_to_delete_upper}' not found."

            if user_id_to_delete_upper == "ADMIN":
                admin_count = (
                    session.query(func.count(User.user_id))
                    .filter(User.user_id == "ADMIN", User.is_active == True)
                    .scalar()
                )
                if admin_count <= 1:
                    self.logger.warning(
                        "Attempt to delete the last ADMIN user was prevented."
                    )
                    return False, "Cannot delete the last ADMIN user."

            active_user_count = (
                session.query(func.count(User.user_id))
                .filter(User.is_active == True)
                .scalar()
            )
            if user_to_delete.is_active and active_user_count <= 1:
                self.logger.warning(
                    f"Attempt to delete the last active user ('{user_id_to_delete_upper}') was prevented."
                )
                return False, "Cannot delete the last active user."

            session.delete(user_to_delete)
            session.commit()
            self.logger.info(
                f"User '{user_id_to_delete_upper}' permanently deleted by '{current_admin_id_upper}'."
            )
            return True, f"User '{user_id_to_delete_upper}' deleted successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error deleting user '{user_id_to_delete_upper}': {e}", exc_info=True
            )
            return False, f"Failed to delete user: {e}"
        finally:
            session.close()

    # --- Role Management (Basic Stubs - ensure Role, UserRole models are defined) ---
    def create_role(
        self, name: str, description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Role]]:
        session = db_manager.get_session()
        try:
            if not name:
                return False, "Role name cannot be empty.", None
            existing_role = session.query(Role).filter(Role.name == name).first()
            if existing_role:
                return False, f"Role '{name}' already exists.", None

            new_role = Role(name=name, description=description)
            session.add(new_role)
            session.commit()
            session.refresh(new_role)
            self.logger.info(f"Role '{name}' created with ID {new_role.role_id}.")
            return True, "Role created successfully.", new_role
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating role '{name}': {e}", exc_info=True)
            return False, f"Failed to create role: {str(e)}", None
        finally:
            session.close()

    def get_role_by_name(self, name: str) -> Optional[Role]:
        session = db_manager.get_session()
        try:
            return session.query(Role).filter(Role.name == name).first()
        finally:
            session.close()

    def get_all_roles(self) -> List[Role]:
        session = db_manager.get_session()
        try:
            return session.query(Role).order_by(Role.name).all()
        finally:
            session.close()

    def assign_role_to_user(self, user_id: str, role_name: str) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, f"User '{user_id}' not found."
            role = self.get_role_by_name(role_name)
            if not role:
                return False, f"Role '{role_name}' not found."

            existing_assoc = (
                session.query(UserRole)
                .filter_by(user_id=user_id, role_id=role.role_id)
                .first()
            )
            if existing_assoc:
                return True, f"User '{user_id}' already has role '{role_name}'."

            user_role_assoc = UserRole(user_id=user_id, role_id=role.role_id)
            session.add(user_role_assoc)
            session.commit()
            self.logger.info(f"Assigned role '{role_name}' to user '{user_id}'.")
            return True, f"Role '{role_name}' assigned to user '{user_id}'."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error assigning role '{role_name}' to user '{user_id}': {e}",
                exc_info=True,
            )
            return False, f"Failed to assign role: {str(e)}"
        finally:
            session.close()

    def remove_role_from_user(self, user_id: str, role_name: str) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, f"User '{user_id}' not found."
            role = self.get_role_by_name(role_name)
            if not role:
                return False, f"Role '{role_name}' not found."

            assoc = (
                session.query(UserRole)
                .filter_by(user_id=user_id, role_id=role.role_id)
                .first()
            )
            if not assoc:
                return False, f"User '{user_id}' does not have role '{role_name}'."

            session.delete(assoc)
            session.commit()
            self.logger.info(f"Removed role '{role_name}' from user '{user_id}'.")
            return True, f"Role '{role_name}' removed from user '{user_id}'."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error removing role '{role_name}' from user '{user_id}': {e}",
                exc_info=True,
            )
            return False, f"Failed to remove role: {str(e)}"
        finally:
            session.close()

    def get_user_roles(self, user_id: str) -> List[str]:
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id == user_id)
                .first()
            )
            if user:
                return [role.name for role in user.roles]
            return []
        finally:
            session.close()

    def delete_role(self, role_name: str) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            role = (
                session.query(Role)
                .options(joinedload(Role.users))
                .filter(Role.name == role_name)
                .first()
            )
            if not role:
                return False, f"Role '{role_name}' not found."
            if role.users:
                return (
                    False,
                    f"Role '{role_name}' cannot be deleted, it is assigned to {len(role.users)} user(s).",
                )

            session.delete(role)
            session.commit()
            self.logger.info(f"Role '{role_name}' deleted.")
            return True, f"Role '{role_name}' deleted successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error deleting role '{role_name}': {e}", exc_info=True)
            return False, f"Failed to delete role: {str(e)}"
        finally:
            session.close()
