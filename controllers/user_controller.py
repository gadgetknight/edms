# controllers/user_controller.py
"""
EDSI Veterinary Management System - User Controller
Version: 1.2.4
Purpose: Handles user authentication, CRUD operations.
         - Aligned password handling with User model's bcrypt methods.
         - Ensured case-insensitive username login.
Last Updated: May 23, 2025
Author: Gemini (based on user's v1.2.3)

Changelog:
- v1.2.4 (2025-05-23):
    - Removed internal `_hash_password` method (used sha256).
    - Modified `authenticate_user` (was `validate_password`) to use `user.check_password()` (bcrypt)
      for password verification, ensuring compatibility with `User.set_password()`.
    - Maintained case-insensitive username lookup using `User.user_id.collate('NOCASE')`.
    - Modified `create_user` to use `new_user.set_password()` for new user passwords.
    - Modified `change_password` to use `user.set_password()` for password changes.
    - Ensured usage of `db_manager.get_session()` (already present in user's v1.2.3).
    - Standardized field name references (e.g., Role.name).
- v1.2.3 (2025-05-21 - User Uploaded version):
    - Modified `create_user` and `update_user` for email field.
    - Ensured role assignment logic is robust.
    - Uses sha256 for passwords.
"""

import logging

# REMOVED: import hashlib (no longer using sha256 here)
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import (
    Session,
    joinedload,
)  # Keep Session for type hinting if preferred
from sqlalchemy import func, exc as sqlalchemy_exc
from datetime import datetime

from config.database_config import db_manager
from models.user_models import User, Role, UserRole

# from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog # Keep as local import


class UserController:
    """Controller for user management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # REMOVED: def _hash_password(self, password: str) -> str:

    # Renamed for clarity to match typical authentication method naming,
    # and to reflect it now uses User model's check_password.
    def authenticate_user(
        self, login_id_attempt: str, password_attempt: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates a user.
        Username (login_id_attempt) comparison is case-insensitive.
        Password checking is case-sensitive (via bcrypt in User.check_password).
        """
        self.logger.debug(f"Attempting to authenticate user: {login_id_attempt}")
        session = db_manager.get_session()
        try:
            # Case-insensitive lookup for SQLite using COLLATE NOCASE.
            # User.user_id stores "ADMIN", this allows "admin", "Admin", "ADMIN" to match.
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == login_id_attempt)
                .first()
            )

            if not user:
                self.logger.warning(
                    f"Login ID '{login_id_attempt}' not found during authentication."
                )
                return False, "Invalid Login ID or Password.", None

            # MODIFIED: Use User model's check_password method (bcrypt)
            if not user.check_password(password_attempt):
                self.logger.warning(
                    f"Incorrect password attempt for login ID '{user.user_id}' (input was '{login_id_attempt}')."
                )
                return False, "Invalid Login ID or Password.", None

            if not user.is_active:
                self.logger.warning(
                    f"Login attempt for inactive user '{user.user_id}'."
                )
                return (
                    False,
                    f"User account '{user.user_id}' is inactive.",
                    {
                        "user_id": user.user_id,  # Return the actual stored user_id
                        "user_name": user.user_name,
                        "is_active": user.is_active,
                    },
                )

            # Update last_login if the field exists on your User model
            if hasattr(user, "last_login"):
                user.last_login = datetime.utcnow()

            session.commit()  # Commit last_login update
            self.logger.info(f"User '{user.user_id}' authenticated successfully.")
            return (
                True,
                "Login successful.",
                {
                    "user_id": user.user_id,  # Return the actual stored user_id
                    "user_name": user.user_name,
                    "is_active": user.is_active,
                    # Include roles if your login success handler needs them immediately
                    # "roles": [role.name for role in user.roles] # Example
                },
            )
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error during authentication for '{login_id_attempt}': {e}",
                exc_info=True,
            )
            return False, "An error occurred during login. Please try again.", None
        except Exception as e:  # Catch any other unexpected error
            session.rollback()
            self.logger.error(
                f"Unexpected error during authentication for '{login_id_attempt}': {e}",
                exc_info=True,
            )
            return False, "An unexpected server error occurred. Please try again.", None
        finally:
            session.close()

    def get_all_users(self, include_inactive: bool = True) -> List[User]:
        session = db_manager.get_session()
        try:
            query = session.query(User).options(joinedload(User.roles))
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
            # Use collate for consistency if user_id might be searched with varied case
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id.collate("NOCASE") == login_id_str)
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
        from views.admin.dialogs.add_edit_user_dialog import (
            AddEditUserDialog,
        )  # Local import

        errors = []
        # Assuming user_id is passed as 'user_id' in user_data or derived
        login_id = user_data.get("user_id", "").strip()
        display_name = user_data.get("user_name", "").strip()
        password = user_data.get("password", "")
        email_value = user_data.get("email")
        email = email_value.strip() if isinstance(email_value, str) else None

        if not login_id:
            errors.append("Login ID (Username) is required.")
        # User model v1.1.2 (based on user's v1.1.1) has user_id = Column(String(20))
        elif len(login_id) > 20:
            errors.append("Login ID (Username) cannot exceed 20 characters.")
        elif " " in login_id:
            errors.append("Login ID (Username) cannot contain spaces.")
        else:
            session = db_manager.get_session()
            try:
                # For uniqueness checks, typically case-insensitive for username if login is case-insensitive
                query = session.query(User).filter(
                    User.user_id.collate("NOCASE") == login_id
                )
                if not is_new and original_login_id_to_ignore is not None:
                    query = query.filter(
                        User.user_id.collate("NOCASE") != original_login_id_to_ignore
                    )

                if query.first():
                    errors.append(f"Login ID (Username) '{login_id}' already exists.")

                if email:  # Check email uniqueness if provided
                    email_query = session.query(User).filter(User.email == email)
                    user_to_exclude_from_email_check = None
                    if not is_new and original_login_id_to_ignore:
                        user_to_exclude_from_email_check = (
                            session.query(User.user_id)
                            .filter(
                                User.user_id.collate("NOCASE")
                                == original_login_id_to_ignore
                            )
                            .first()
                        )

                    if user_to_exclude_from_email_check:
                        email_query = email_query.filter(
                            User.user_id != user_to_exclude_from_email_check.user_id
                        )

                    if email_query.first():
                        errors.append(f"Email '{email}' is already in use.")
            except sqlalchemy_exc.SQLAlchemyError as e_db:
                self.logger.error(
                    f"DB error validating login_id/email uniqueness: {e_db}",
                    exc_info=True,
                )
                errors.append("Error validating login_id/email uniqueness.")
            finally:
                session.close()

        if not display_name:
            errors.append("Full Name (User Name) is required.")
        elif len(display_name) > 100:  # User model user_name = Column(String(100))
            errors.append("Full Name (User Name) cannot exceed 100 characters.")

        if is_new:
            if not password:
                errors.append("Password is required for new users.")
            elif len(password) < 6:  # Arbitrary minimum length, adjust as needed
                errors.append("Password must be at least 6 characters long.")
        elif password and len(password) < 6:  # If password provided for update
            errors.append("New password must be at least 6 characters long.")

        if email and (
            len(email) > 100 or ("@" not in email or "." not in email.split("@")[-1])
        ):  # User model email = Column(String(100))
            errors.append(
                "Invalid email format or email too long (max 100 characters)."
            )

        role_str = user_data.get("role")  # Assuming role is passed as string name
        if not role_str and is_new:
            errors.append("Role is required for new users.")
        elif (
            role_str
            and hasattr(AddEditUserDialog, "USER_ROLES")
            and role_str not in AddEditUserDialog.USER_ROLES
        ):
            errors.append(
                f"Selected role '{role_str}' is not a recognized role option."
            )
        # Further validation: check if role_str exists in DB
        elif role_str:
            session = db_manager.get_session()
            try:
                if (
                    not session.query(Role).filter(Role.name == role_str).first()
                ):  # Role.name
                    errors.append(f"Role '{role_str}' does not exist in the database.")
            finally:
                session.close()
        return not errors, errors

    def create_user(
        self, user_data: Dict[str, Any], current_admin_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        # Use user_id from user_data, ensure it's processed (e.g. upper for storage if desired)
        # The user's v1.2.3 used user_data.get("username", "").strip().upper() for user_id
        # For consistency with case-insensitive login, store 'ADMIN' as 'ADMIN'
        # but allow flexible input for other users if needed.
        # Let's assume user_id is provided directly and should be stored as-is,
        # unless there's a specific rule to uppercase it for all users.
        # Given 'ADMIN' is special, we ensure it's stored as 'ADMIN'.

        login_id_to_store = user_data.get("user_id", "").strip()
        if (
            login_id_to_store.upper() == "ADMIN"
        ):  # Normalize ADMIN user_id to uppercase for storage
            login_id_to_store = "ADMIN"

        # Prepare data for User model, aligning with its fields
        data_for_model = {
            "user_id": login_id_to_store,
            "user_name": user_data.get("user_name", "").strip(),
            "email": user_data.get("email"),  # Will be processed for None/empty string
            "is_active": user_data.get("is_active", True),
            "created_by": current_admin_id,
            "modified_by": current_admin_id,
            # Include other User fields from your user_models.py v1.1.1/v1.1.2 if they can be set at creation
            "printer_id": user_data.get("printer_id"),
            "default_screen_colors": user_data.get("default_screen_colors"),
        }

        # Password will be set via set_password method
        password_to_set = user_data.get("password", "")
        role_name_to_assign = user_data.get("role")

        # Validate pre-processed data (user_id as is, role as name)
        validation_payload = {
            **data_for_model,
            "password": password_to_set,
            "role": role_name_to_assign,
        }
        is_valid, errors = self.validate_user_data(validation_payload, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            processed_email = data_for_model["email"]
            if isinstance(processed_email, str):
                processed_email = processed_email.strip()
                if not processed_email:  # Empty string to None
                    processed_email = None
            data_for_model["email"] = processed_email

            # Remove password from data_for_model as it's set via method
            new_user = User(**data_for_model)
            new_user.set_password(password_to_set)  # MODIFIED: Use set_password

            if role_name_to_assign:
                role_obj = (
                    session.query(Role).filter(Role.name == role_name_to_assign).first()
                )  # Role.name
                if role_obj:
                    new_user.roles.append(role_obj)
                else:  # Should be caught by validation
                    self.logger.error(
                        f"Role '{role_name_to_assign}' not found for new user '{new_user.user_id}'."
                    )
                    # Decide if this is a rollback scenario

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
                f"Error creating user '{data_for_model.get('user_id')}': {e.orig}",
                exc_info=True,
            )
            # ... (error parsing logic from user's v1.2.3 can be kept)
            error_str = str(e.orig).lower()
            if "unique constraint failed: users.user_id" in error_str:
                return (
                    False,
                    f"Login ID (Username) '{data_for_model['user_id']}' already exists.",
                    None,
                )
            elif (
                "unique constraint failed: users.email" in error_str
                and data_for_model["email"]
            ):
                return (
                    False,
                    f"Email '{data_for_model['email']}' is already in use.",
                    None,
                )
            return False, f"Database integrity error: {e.orig}", None
        except Exception as e:  # Broader exception
            session.rollback()
            self.logger.error(
                f"Error creating user '{data_for_model.get('user_id')}': {e}",
                exc_info=True,
            )
            return False, f"Failed to create user: {e}", None
        finally:
            session.close()

    def update_user(
        self,
        user_id_to_update: str,  # Changed from login_id_str_pk for clarity
        user_data: Dict[str, Any],
        current_admin_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            # Fetch user case-insensitively for update target
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id.collate("NOCASE") == user_id_to_update)
                .first()
            )
            if not user:
                return False, f"User with Login ID '{user_id_to_update}' not found."

            # Prepare data for validation, using existing user values as fallback
            validation_data = {
                "user_id": user.user_id,  # Use actual stored user_id for validation context
                "user_name": user_data.get("user_name", user.user_name),
                "email": user_data.get("email", user.email),
                "role": user_data.get("role"),  # Role name string
            }
            if (
                "password" in user_data and user_data["password"]
            ):  # only if new password provided
                validation_data["password"] = user_data["password"]

            is_valid, errors = self.validate_user_data(
                validation_data, is_new=False, original_login_id_to_ignore=user.user_id
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            # Apply updates
            if "user_name" in user_data:
                user.user_name = user_data["user_name"].strip()

            if "email" in user_data:
                email_val = user_data["email"]
                user.email = email_val.strip() if isinstance(email_val, str) else None
                if user.email == "":
                    user.email = None

            if "password" in user_data and user_data["password"]:
                user.set_password(user_data["password"])  # MODIFIED: Use set_password

            if "is_active" in user_data:
                if user.user_id.upper() == "ADMIN" and not user_data["is_active"]:
                    # Prevent deactivating the sole admin logic (from user's v1.2.3)
                    active_admin_query = session.query(User).filter(
                        User.is_active == True,
                        User.user_id.collate("NOCASE") == "ADMIN",
                    )
                    if user.is_active:  # if current user is the one being deactivated
                        if active_admin_query.count() <= 1:
                            self.logger.warning(
                                f"Attempt to deactivate the last active ADMIN user ('{user.user_id}') was prevented."
                            )
                            return (
                                False,
                                "Cannot deactivate the last active ADMIN user.",
                            )
                    user.is_active = user_data["is_active"]
                else:
                    user.is_active = user_data["is_active"]

            new_role_name = user_data.get("role")
            if (
                new_role_name is not None
            ):  # Allow empty string or None to signify role removal if desired, or handle explicit 'no change'
                user.roles.clear()  # Simple approach: clear and re-add. More complex logic for partial updates if needed.
                if (
                    new_role_name
                ):  # If a new role is actually specified (not empty string)
                    role_obj = (
                        session.query(Role).filter(Role.name == new_role_name).first()
                    )  # Role.name
                    if role_obj:
                        user.roles.append(role_obj)
                    else:  # Should be caught by validation
                        self.logger.error(
                            f"Role object for '{new_role_name}' not found. Role not updated for user '{user.user_id}'."
                        )
                        # Potentially rollback or return error if role assignment is critical
                        # session.rollback(); return False, f"Role '{new_role_name}' not found."

            # Update other fields from user_models.py v1.1.1/v1.1.2 if they are updatable
            if "printer_id" in user_data:
                user.printer_id = user_data["printer_id"]
            if "default_screen_colors" in user_data:
                user.default_screen_colors = user_data["default_screen_colors"]

            user.modified_by = current_admin_id
            session.commit()
            self.logger.info(
                f"User '{user.user_id}' updated successfully by {current_admin_id}."
            )
            return True, "User updated successfully."
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            # ... (error parsing from user's v1.2.3 for email can be kept)
            self.logger.error(
                f"Error updating user '{user_id_to_update}': {e.orig}", exc_info=True
            )
            if "unique constraint failed: users.email" in str(
                e.orig
            ).lower() and validation_data.get("email"):
                return (
                    False,
                    f"Email '{validation_data['email']}' is already in use by another user.",
                )
            return False, f"Database integrity error: {e.orig}"
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error updating user '{user_id_to_update}': {e}", exc_info=True
            )
            return False, f"Failed to update user: {str(e)}"
        finally:
            session.close()

    def change_password(
        self,
        login_id_str: str,
        new_password: str,
        current_admin_id: Optional[str] = None,  # User performing the change
    ) -> Tuple[bool, str]:
        if not new_password or len(new_password) < 6:  # Keep password policy
            return False, "New password must be at least 6 characters long."

        session = db_manager.get_session()
        try:
            # Fetch user case-insensitively
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == login_id_str)
                .first()
            )
            if not user:
                return False, f"User '{login_id_str}' not found."

            user.set_password(new_password)  # MODIFIED: Use set_password
            user.modified_by = current_admin_id
            # user.modified_at is handled by BaseModel

            session.commit()
            self.logger.info(
                f"Password changed successfully for user '{user.user_id}' by {current_admin_id}."
            )
            return True, "Password changed successfully."
        except Exception as e:  # Catch all, including SQLAlchemyError
            session.rollback()
            self.logger.error(
                f"Error changing password for user '{login_id_str}': {e}", exc_info=True
            )
            return False, f"Failed to change password: {str(e)}"
        finally:
            session.close()

    def get_user_roles(self, login_id_str: str) -> List[str]:
        session = db_manager.get_session()
        try:
            # Fetch user case-insensitively
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id.collate("NOCASE") == login_id_str)
                .first()
            )
            if user and user.roles:
                return [role.name for role in user.roles]  # Role.name
            return []
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching roles for user '{login_id_str}': {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def delete_user_permanently(  # Renamed from user's v1.2.3 for clarity, was delete_user
        self, user_id_to_delete: str, current_admin_id: str
    ) -> Tuple[bool, str]:
        session = db_manager.get_session()
        try:
            # Fetch user case-sensitively for delete, or case-insensitively if desired.
            # For safety, usually PK lookups for delete are case-sensitive.
            # However, if user_id can be entered with different casing, use collate.
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == user_id_to_delete)
                .first()
            )
            if not user:
                return False, f"User '{user_id_to_delete}' not found."

            # Prevent deleting the main 'ADMIN' user if it's the last active one (from user's v1.2.3 logic)
            if user.user_id.upper() == "ADMIN":
                active_admin_count = (
                    session.query(User)
                    .filter(
                        User.is_active == True,
                        User.user_id.collate("NOCASE") == "ADMIN",
                    )
                    .count()
                )
                if (
                    active_admin_count <= 1 and user.is_active
                ):  # Only protect if this user is one of the last active admins
                    self.logger.warning(
                        f"Attempt to delete the last active ADMIN user ('{user.user_id}') by '{current_admin_id}' was prevented."
                    )
                    return (
                        False,
                        "Cannot delete the primary ADMIN account if it's the last active one.",
                    )

            session.delete(
                user
            )  # SQLAlchemy handles related UserRole entries via cascade on User.roles if set up
            session.commit()
            self.logger.info(
                f"User '{user.user_id}' permanently deleted by admin '{current_admin_id}'."
            )
            return True, f"User '{user.user_id}' deleted successfully."
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            self.logger.error(
                f"Database integrity error deleting user '{user_id_to_delete}': {e.orig}",
                exc_info=True,
            )
            return (
                False,
                f"Cannot delete user. They may be referenced by other records. ({e.orig})",
            )
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error deleting user '{user_id_to_delete}': {e}", exc_info=True
            )
            return False, f"Failed to delete user: {str(e)}"
        finally:
            session.close()

    def get_all_roles(
        self,
    ) -> List[Role]:  # Added from my v1.1.3 proposal, useful for UI
        session = db_manager.get_session()
        try:
            roles = session.query(Role).order_by(Role.name).all()
            self.logger.info(f"Retrieved {len(roles)} roles.")
            return roles
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving roles: {e}", exc_info=True)
            session.rollback()
            return []
        finally:
            session.close()
