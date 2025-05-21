# controllers/user_controller.py
"""
EDSI Veterinary Management System - User Controller
Version: 1.2.1 (Based on GitHub v1.1.1)
Purpose: Handles user authentication, CRUD operations.
         Aligned with User model v1.1.0 (String user_id as PK/login, user_name for display name).
         Fixed circular import by moving AddEditUserDialog import into methods.
Last Updated: May 20, 2025
Author: Gemini

Changelog:
- v1.2.1 (2025-05-20):
    - (Based on GitHub v1.1.1, incorporating v1.2.0 changes)
    - Fixed circular import with `AddEditUserDialog` by moving the import
      statement into the methods (`validate_user_data`, `create_user`, `update_user`)
      that require access to `AddEditUserDialog.USER_ROLES`.
- v1.2.0 (2025-05-20):
    - Aligned all User model attribute access with user_models.py v1.1.0:
        - `User.user_id` (String Primary Key) is now correctly used for login identification.
        - `User.user_name` is now correctly used for the user's display name.
    - `validate_password`: Now queries against `User.user_id` (string login ID).
    - `get_user_by_login_id`: Fetches by `User.user_id` (string PK).
    - `create_user`, `update_user`, `validate_user_data` updated for correct field mapping.
    - Temporarily simplified direct role string assignment.
- v1.1.1 (2025-05-18):
    - Modified `validate_password` to return a dictionary of user details.
"""

import logging
import hashlib
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, exc as sqlalchemy_exc
from datetime import datetime

from config.database_config import db_manager
from models.user_models import User, Role, UserRole

# Removed top-level import that caused circular dependency:
# from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog


class UserController:
    """Controller for user management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def validate_password(
        self, login_id_str: str, password_attempt: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        self.logger.debug(
            f"Attempting to validate password for login_id: {login_id_str}"
        )
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .filter(func.upper(User.user_id) == login_id_str.upper())
                .first()
            )
            if not user:
                self.logger.warning(
                    f"Login ID '{login_id_str}' not found during password validation."
                )
                return False, "Invalid Login ID or Password.", None
            hashed_attempt = self._hash_password(password_attempt)
            if user.password_hash != hashed_attempt:
                self.logger.warning(
                    f"Incorrect password attempt for login ID '{login_id_str}'."
                )
                return False, "Invalid Login ID or Password.", None

            user_is_active = user.is_active
            actual_login_id = user.user_id
            user_display_name = user.user_name

            if not user_is_active:
                self.logger.warning(
                    f"Login attempt for inactive user '{actual_login_id}'."
                )
                return (
                    False,
                    f"User account '{actual_login_id}' is inactive.",
                    {
                        "login_id": actual_login_id,
                        "user_name": user_display_name,
                        "is_active": user_is_active,
                    },
                )

            user.last_login = datetime.utcnow()
            session.commit()
            self.logger.info(
                f"Password validated successfully for active user '{actual_login_id}'."
            )
            return (
                True,
                "Login successful.",
                {
                    "login_id": actual_login_id,
                    "user_name": user_display_name,
                    "is_active": user_is_active,
                },
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error during password validation for login_id '{login_id_str}': {e}",
                exc_info=True,
            )
            return False, "An error occurred during login. Please try again.", None
        finally:
            session.close()

    def get_all_users(self, include_inactive: bool = True) -> List[User]:
        session = db_manager.get_session()
        try:
            query = session.query(User).options(
                joinedload(User.roles)
            )  # Eager load roles for display
            if not include_inactive:
                query = query.filter(User.is_active == True)
            users = query.order_by(User.user_id).all()
            return users
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all users: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_user_by_login_id(self, login_id_str: str) -> Optional[User]:
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(func.upper(User.user_id) == login_id_str.upper())
                .first()
            )
            return user
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching user by login_id '{login_id_str}': {e}", exc_info=True
            )
            return None
        finally:
            session.close()

    def validate_user_data(
        self,
        user_data: Dict[str, Any],
        is_new: bool = True,
        original_login_id_to_ignore: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        # Import here to avoid circular dependency at module level
        from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

        errors = []
        login_id = user_data.get("user_id", "").strip()
        display_name = user_data.get("user_name", "").strip()
        password = user_data.get("password", "")
        email = user_data.get("email", "").strip()

        if not login_id:
            errors.append("Login ID is required.")
        elif len(login_id) > 20:
            errors.append("Login ID cannot exceed 20 characters.")
        elif " " in login_id:
            errors.append("Login ID cannot contain spaces.")
        else:
            session = db_manager.get_session()
            try:
                query = session.query(User).filter(
                    func.upper(User.user_id) == login_id.upper()
                )
                if not is_new and original_login_id_to_ignore is not None:
                    query = query.filter(
                        func.upper(User.user_id) != original_login_id_to_ignore.upper()
                    )
                if query.first():
                    errors.append(f"Login ID '{login_id}' already exists.")
            except sqlalchemy_exc.SQLAlchemyError as e_db:
                self.logger.error(
                    f"DB error validating login_id uniqueness: {e_db}", exc_info=True
                )
                errors.append("Error validating login_id uniqueness.")
            finally:
                session.close()

        if not display_name:
            errors.append("Display Name (user_name) is required.")
        elif len(display_name) > 100:
            errors.append("Display Name (user_name) cannot exceed 100 characters.")

        if is_new:
            if not password:
                errors.append("Password is required for new users.")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters long.")
        elif password and len(password) < 6:
            errors.append("New password must be at least 6 characters long.")

        if email and (
            len(email) > 100 or ("@" not in email or "." not in email.split("@")[-1])
        ):
            errors.append(
                "Invalid email format or email too long (max 100 characters)."
            )

        role_str = user_data.get("role")
        if role_str and role_str not in AddEditUserDialog.USER_ROLES:
            errors.append(
                f"Selected role '{role_str}' is not a recognized role option."
            )

        return not errors, errors

    def create_user(
        self, user_data: Dict[str, Any], current_admin_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        # Import here to avoid circular dependency at module level
        from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

        if (
            user_data.get("role") not in AddEditUserDialog.USER_ROLES
        ):  # Check against dialog's defined roles
            return False, f"Invalid role: {user_data.get('role')}", None

        is_valid, errors = self.validate_user_data(user_data, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            new_user = User(
                user_id=user_data["user_id"].strip().upper(),
                user_name=user_data["user_name"].strip(),
                password_hash=self._hash_password(user_data["password"]),
                email=user_data.get("email", "").strip() or None,
                is_active=user_data.get("is_active", True),
                created_by=current_admin_id,  # Add audit field
                modified_by=current_admin_id,  # Add audit field
            )

            role_to_assign = user_data.get("role")
            if role_to_assign:
                role_obj = (
                    session.query(Role).filter(Role.name == role_to_assign).first()
                )
                if role_obj:
                    new_user.roles.append(role_obj)  # Manages UserRole association
                else:
                    self.logger.warning(
                        f"Role object for '{role_to_assign}' not found. Cannot assign to new user."
                    )
                    # Optionally, you could make this a hard error by returning False

            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            self.logger.info(
                f"User '{new_user.user_id}' created successfully by {current_admin_id}."
            )
            return True, "User created successfully.", new_user
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            self.logger.error(
                f"Error creating user '{user_data.get('user_id')}': {e.orig}",
                exc_info=True,
            )
            if "UNIQUE constraint failed: users.user_id" in str(e.orig).lower():
                return False, f"Login ID '{user_data['user_id']}' already exists.", None
            return False, f"Database integrity error: {e.orig}", None
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error creating user '{user_data.get('user_id')}': {e}", exc_info=True
            )
            return False, f"Failed to create user: {e}", None
        finally:
            session.close()

    def update_user(
        self,
        login_id_str_pk: str,
        user_data: Dict[str, Any],
        current_admin_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        # Import here to avoid circular dependency at module level
        from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(func.upper(User.user_id) == login_id_str_pk.upper())
                .first()
            )
            if not user:
                return False, f"User with Login ID '{login_id_str_pk}' not found."

            # Role check using USER_ROLES from dialog
            if (
                "role" in user_data
                and user_data.get("role") not in AddEditUserDialog.USER_ROLES
            ):
                return False, f"Invalid role: {user_data.get('role')}"

            validation_payload = {
                "user_id": login_id_str_pk,
                "user_name": user_data.get("user_name", user.user_name),
                "email": user_data.get("email", user.email),
                "role": user_data.get(
                    "role"
                ),  # For validation against AddEditUserDialog.USER_ROLES
            }
            if "password" in user_data and user_data["password"]:
                validation_payload["password"] = user_data["password"]

            is_valid, errors = self.validate_user_data(
                validation_payload,
                is_new=False,
                original_login_id_to_ignore=login_id_str_pk,
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            if "user_name" in user_data:
                user.user_name = user_data["user_name"].strip()
            if "email" in user_data:
                user.email = user_data["email"].strip() or None

            new_role_str = user_data.get("role")
            if new_role_str:
                current_role_names = [r.name for r in user.roles]
                if (
                    new_role_str not in current_role_names
                ):  # Basic check if single role changed
                    user.roles.clear()  # Clear existing roles before adding new one
                    role_obj = (
                        session.query(Role).filter(Role.name == new_role_str).first()
                    )
                    if role_obj:
                        user.roles.append(role_obj)
                    else:
                        self.logger.warning(
                            f"Role object for '{new_role_str}' not found. Cannot update role for user '{user.user_id}'."
                        )

            if "password" in user_data and user_data["password"]:
                user.password_hash = self._hash_password(user_data["password"])

            if "is_active" in user_data:
                if user.user_id.upper() == "ADMIN" and not user_data["is_active"]:
                    active_admin_query = session.query(func.count(User.user_id)).filter(
                        User.is_active == True,
                        func.upper(User.user_id) == "ADMIN",
                        User.user_id != user.user_id,
                    )
                    active_admin_count_others = active_admin_query.scalar()
                    if active_admin_count_others == 0:
                        self.logger.warning(
                            f"Attempt to deactivate the last active ADMIN user ('{user.user_id}') was prevented."
                        )
                        return False, "Cannot deactivate the last active ADMIN user."
                user.is_active = user_data["is_active"]

            user.modified_by = current_admin_id  # Add audit field

            session.commit()
            self.logger.info(
                f"User '{user.user_id}' updated successfully by {current_admin_id}."
            )
            return True, "User updated successfully."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error updating user '{login_id_str_pk}': {e}", exc_info=True
            )
            return False, f"Failed to update user: {e}"
        finally:
            session.close()

    def change_password(
        self,
        login_id_str: str,
        new_password: str,
        current_admin_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        if not new_password or len(new_password) < 6:
            return False, "New password must be at least 6 characters long."
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .filter(func.upper(User.user_id) == login_id_str.upper())
                .first()
            )
            if not user:
                return False, f"User '{login_id_str}' not found."
            user.password_hash = self._hash_password(new_password)
            user.modified_by = current_admin_id  # Audit password change
            session.commit()
            self.logger.info(
                f"Password changed successfully for user '{login_id_str}' by {current_admin_id}."
            )
            return True, "Password changed successfully."
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error changing password for user '{login_id_str}': {e}", exc_info=True
            )
            return False, f"Failed to change password: {e}"
        finally:
            session.close()

    def get_user_roles(self, login_id_str: str) -> List[str]:
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(func.upper(User.user_id) == login_id_str.upper())
                .first()
            )
            if user and user.roles:  # Check if user.roles is not empty
                return [role.name for role in user.roles]
            return []  # Return empty list if no user or no roles
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching roles for user '{login_id_str}': {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    # Placeholder for full Role CRUD if needed later, not fleshed out to avoid further import issues now.
    # def create_role ...
    # def assign_role_to_user (would take login_id_str, role_name_str) ...
    # def remove_role_from_user ...
