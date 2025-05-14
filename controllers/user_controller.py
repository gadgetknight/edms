# controllers/user_controller.py

"""
EDSI Veterinary Management System - User Controller
Version: 1.1.0
Purpose: Business logic for user management operations (listing, creating, updating, deleting users).
Last Updated: May 13, 2025
Author: Claude Assistant

Changelog:
- v1.1.0 (2025-05-13): Added delete_user_permanently method.
  - Implemented logic to permanently delete a user.
  - Added checks to prevent deletion of the currently logged-in admin
    or the last remaining active admin user.
- v1.0.0 (2025-05-13): Initial implementation
  - Methods for get_all_users, get_user_by_id, validate_user_data,
    create_user, update_user, change_password.
"""

import logging
import hashlib
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func  # For count
from config.database_config import db_manager
from models import User


class UserController:
    """Controller for user management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        """
        Fetches all users from the database.
        Args:
            include_inactive (bool): If True, includes inactive users. Defaults to False.
        Returns:
            List[User]: A list of User objects.
        """
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
        """
        Fetches a single user by their user_id.
        Args:
            user_id (str): The ID of the user to fetch.
        Returns:
            Optional[User]: The User object if found, else None.
        """
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
        """
        Validates user data for creation or update.
        Args:
            user_data (dict): Dictionary containing user information.
            is_new (bool): True if validating for a new user.
            original_user_id (str, optional): The original user ID if updating, to allow checking if user_id changed.
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
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
        elif is_new:  # Check for existence only if it's a new user
            existing_user = self.get_user_by_id(user_id)
            if existing_user:
                errors.append(f"User ID '{user_id}' already exists.")
        # If updating, user_id is not changeable via this validation, so no check for existing needed here.

        if not user_name:
            errors.append("User Name is required.")
        elif len(user_name) > 100:
            errors.append("User Name cannot exceed 100 characters.")

        if is_new:  # Password checks only for new users
            if not password:
                errors.append("Password is required for new users.")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters long.")

        return len(errors) == 0, errors

    def create_user(self, user_data: dict) -> Tuple[bool, str, Optional[User]]:
        """
        Creates a new user.
        Args:
            user_data (dict): User information including 'user_id', 'user_name', 'password'.
        Returns:
            Tuple[bool, str, Optional[User]]: (success, message, user_object)
        """
        is_valid, errors = self.validate_user_data(user_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            user_id = user_data["user_id"].strip().upper()
            password = user_data["password"]
            password_hash = hashlib.sha256(password.lower().encode("utf-8")).hexdigest()

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
            return False, f"Failed to create user: {e}", None
        finally:
            session.close()

    def update_user(self, user_id_orig: str, user_data: dict) -> Tuple[bool, str]:
        """
        Updates an existing user's details (user_name, is_active).
        Args:
            user_id_orig (str): The original User ID of the user to update.
            user_data (dict): Dictionary with 'user_name', and 'is_active'.
        Returns:
            Tuple[bool, str]: (success, message)
        """
        session = db_manager.get_session()
        try:
            user_to_update_id = user_id_orig.upper()
            user = session.query(User).filter(User.user_id == user_to_update_id).first()
            if not user:
                return False, f"User '{user_to_update_id}' not found."

            # Validate only the fields being updated
            temp_validation_data = {
                "user_id": user_to_update_id
            }  # Keep user_id for context
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
                # Prevent deactivating the last active admin
                if user.user_id == "ADMIN" and not user_data["is_active"]:
                    active_admin_count = (
                        session.query(func.count(User.user_id))
                        .filter(User.is_active == True, User.user_id == "ADMIN")
                        .scalar()
                    )  # Simplistic check for "ADMIN" role
                    if active_admin_count <= 1:  # If this is the last active admin
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
        """
        Changes a user's password.
        Args:
            user_id (str): The User ID.
            new_password (str): The new password.
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not new_password or len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id.upper()).first()
            if not user:
                return False, f"User '{user_id}' not found."

            new_password_hash = hashlib.sha256(
                new_password.lower().encode("utf-8")
            ).hexdigest()
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
        """
        Permanently deletes a user from the database.
        Prevents deletion of the currently logged-in admin or the last admin.

        Args:
            user_id_to_delete (str): The User ID of the user to be deleted.
            current_admin_id (str): The User ID of the admin performing the deletion.

        Returns:
            Tuple[bool, str]: (success, message)
        """
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

            # Check if this is the last ADMIN user (assuming 'ADMIN' is a special role/ID)
            # A more robust system might have roles, but for now, we check for 'ADMIN' ID.
            if user_to_delete_upper == "ADMIN":
                admin_count = (
                    session.query(func.count(User.user_id))
                    .filter(User.user_id == "ADMIN")
                    .scalar()
                )
                if admin_count <= 1:
                    self.logger.warning(
                        "Attempt to delete the last ADMIN user was prevented."
                    )
                    return False, "Cannot delete the last ADMIN user."

            # A more general check: count active users. If only one active user left, and it's this one, prevent deletion.
            # This is a simple check, a real system might need more complex role-based logic.
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
