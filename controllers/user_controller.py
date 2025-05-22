# controllers/user_controller.py
"""
EDSI Veterinary Management System - User Controller
Version: 1.2.3
Purpose: Handles user authentication, CRUD operations.
         Aligns with User model v1.1.1 (with email field).
Last Updated: May 21, 2025
Author: Gemini

Changelog:
- v1.2.3 (2025-05-21):
    - Modified `create_user` and `update_user` to correctly pass the `email`
      field to the User model, now that the User model has an email column.
    - Ensured role assignment logic in `create_user` and `update_user` is robust.
- v1.2.2 (2025-05-21):
    - Modified `validate_user_data` to correctly handle cases where 'email'
      in `user_data` might be None, preventing an AttributeError on `None.strip()`.
- v1.2.1 (2025-05-20):
    - Fixed circular import with `AddEditUserDialog`.
- v1.2.0 (2025-05-20):
    - Aligned with User model v1.1.0 (String user_id, user_name).
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

# Import for USER_ROLES is moved into methods that need it
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
        # This method remains unchanged from v1.2.2
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
        # This method remains unchanged from v1.2.2
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
        # This method remains unchanged from v1.2.2
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
        # This method's logic for email validation is already robust for None
        # from v1.2.2. We ensure it uses the correct dialog for USER_ROLES.
        from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

        errors = []
        login_id = user_data.get("username", user_data.get("user_id", "")).strip()
        display_name = user_data.get(
            "full_name", user_data.get("user_name", "")
        ).strip()
        password = user_data.get("password", "")

        email_value = user_data.get("email")
        email = email_value.strip() if isinstance(email_value, str) else None

        if not login_id:
            errors.append("Login ID (Username) is required.")
        elif len(login_id) > 20:
            errors.append("Login ID (Username) cannot exceed 20 characters.")
        elif " " in login_id:
            errors.append("Login ID (Username) cannot contain spaces.")
        else:  # Check uniqueness
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
                    errors.append(f"Login ID (Username) '{login_id}' already exists.")

                # Check email uniqueness if email is provided
                if email:
                    email_query = session.query(User).filter(User.email == email)
                    if not is_new and original_login_id_to_ignore is not None:
                        # Exclude current user if their email hasn't changed or if they are the one with this email
                        user_being_updated = (
                            session.query(User)
                            .filter(
                                func.upper(User.user_id)
                                == original_login_id_to_ignore.upper()
                            )
                            .first()
                        )
                        if user_being_updated and user_being_updated.email == email:
                            pass  # It's the same user's existing email, allow
                        elif email_query.first():
                            errors.append(
                                f"Email '{email}' is already in use by another user."
                            )
                    elif email_query.first():  # For new user
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
        elif len(display_name) > 100:
            errors.append("Full Name (User Name) cannot exceed 100 characters.")

        if is_new:
            if not password:
                errors.append("Password is required for new users.")
            elif len(password) < 6:
                errors.append("Password must be at least 6 characters long.")
        elif password and len(password) < 6:  # If password is provided for update
            errors.append("New password must be at least 6 characters long.")

        # Email format check (if email is not None)
        if email and (
            len(email) > 100 or ("@" not in email or "." not in email.split("@")[-1])
        ):
            errors.append(
                "Invalid email format or email too long (max 100 characters)."
            )

        role_str = user_data.get("role")
        if not role_str and is_new:  # Role is mandatory for new users
            errors.append("Role is required for new users.")
        elif (
            role_str
            and hasattr(AddEditUserDialog, "USER_ROLES")
            and role_str not in AddEditUserDialog.USER_ROLES
        ):
            errors.append(
                f"Selected role '{role_str}' is not a recognized role option."
            )

        return not errors, errors

    def create_user(
        self, user_data: Dict[str, Any], current_admin_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

        data_for_processing = {
            "user_id": user_data.get("username", "").strip().upper(),
            "user_name": user_data.get("full_name", "").strip(),
            "password": user_data.get("password", ""),
            "email": user_data.get("email"),  # Passed as is (can be None or string)
            "role": user_data.get("role"),
            "is_active": user_data.get("is_active", True),
        }

        is_valid, errors = self.validate_user_data(data_for_processing, is_new=True)
        if not is_valid:
            return False, "Validation failed: " + "; ".join(errors), None

        session = db_manager.get_session()
        try:
            # Prepare email: None if empty after strip, else the stripped value
            processed_email = (
                data_for_processing["email"].strip()
                if isinstance(data_for_processing["email"], str)
                else None
            )
            if processed_email == "":
                processed_email = None

            new_user = User(
                user_id=data_for_processing["user_id"],
                user_name=data_for_processing["user_name"],
                password_hash=self._hash_password(data_for_processing["password"]),
                email=processed_email,  # Now User model has this field
                is_active=data_for_processing.get("is_active", True),
                created_by=current_admin_id,
                modified_by=current_admin_id,
            )

            role_to_assign_str = data_for_processing.get("role")
            if (
                role_to_assign_str
            ):  # Role should be validated as existing by validate_user_data
                role_obj = (
                    session.query(Role).filter(Role.name == role_to_assign_str).first()
                )
                if role_obj:
                    new_user.roles.append(role_obj)
                else:  # Should not happen if validation is correct
                    self.logger.error(
                        f"Role '{role_to_assign_str}' not found in DB despite validation. User '{new_user.user_id}' created without role."
                    )
            else:  # Should also be caught by validation if role is mandatory
                self.logger.warning(
                    f"No role provided for new user '{new_user.user_id}'. Created without role."
                )

            session.add(new_user)
            session.commit()
            session.refresh(
                new_user
            )  # To get potentially auto-generated fields like created_date
            self.logger.info(
                f"User '{new_user.user_id}' created successfully by {current_admin_id}."
            )
            return True, "User created successfully.", new_user
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
            self.logger.error(
                f"Error creating user '{data_for_processing.get('user_id')}': {e.orig}",
                exc_info=True,
            )
            # More specific error check
            error_str = str(e.orig).lower()
            if "unique constraint failed: users.user_id" in error_str:
                return (
                    False,
                    f"Login ID (Username) '{data_for_processing['user_id']}' already exists.",
                    None,
                )
            elif "unique constraint failed: users.email" in error_str:
                return (
                    False,
                    f"Email '{data_for_processing['email']}' is already in use.",
                    None,
                )
            return False, f"Database integrity error: {e.orig}", None
        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Error creating user '{data_for_processing.get('user_id')}': {e}",
                exc_info=True,
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

            validation_data = {
                "user_id": login_id_str_pk,
                "user_name": user_data.get(
                    "full_name", user_data.get("user_name", user.user_name)
                ),
                "email": user_data.get(
                    "email", user.email
                ),  # Pass current email if not in user_data
                "role": user_data.get("role"),
            }
            if "password" in user_data and user_data["password"]:
                validation_data["password"] = user_data["password"]

            is_valid, errors = self.validate_user_data(
                validation_data,
                is_new=False,
                original_login_id_to_ignore=login_id_str_pk,
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)

            if "full_name" in user_data:
                user.user_name = user_data["full_name"].strip()
            elif "user_name" in user_data:
                user.user_name = user_data["user_name"].strip()

            if "email" in user_data:  # Check if email key is present
                email_val = user_data["email"]
                user.email = email_val.strip() if isinstance(email_val, str) else None

            new_role_str = user_data.get("role")
            if new_role_str:
                if (
                    hasattr(AddEditUserDialog, "USER_ROLES")
                    and new_role_str not in AddEditUserDialog.USER_ROLES
                ):
                    return (
                        False,
                        f"Invalid role: {new_role_str}",
                    )  # Should be caught by validation

                current_role_names = [r.name for r in user.roles]
                if (
                    new_role_str not in current_role_names
                    or len(user.roles) > 1
                    or not user.roles
                ):
                    user.roles.clear()
                    role_obj = (
                        session.query(Role).filter(Role.name == new_role_str).first()
                    )
                    if role_obj:
                        user.roles.append(role_obj)
                    else:  # Should not happen if validation and AddEditUserDialog.USER_ROLES are aligned
                        self.logger.error(
                            f"Role object for '{new_role_str}' not found. Role not updated for user '{user.user_id}'."
                        )

            if "password" in user_data and user_data["password"]:
                user.password_hash = self._hash_password(user_data["password"])

            if "is_active" in user_data:
                if user.user_id.upper() == "ADMIN" and not user_data["is_active"]:
                    active_admin_count = (
                        session.query(User)
                        .filter(
                            User.is_active == True,
                            func.upper(User.user_id) == "ADMIN",
                            User.user_id != user.user_id,
                        )
                        .count()
                    )
                    if active_admin_count == 0:
                        self.logger.warning(
                            f"Attempt to deactivate the last active ADMIN user ('{user.user_id}') was prevented."
                        )
                        return False, "Cannot deactivate the last active ADMIN user."
                user.is_active = user_data["is_active"]

            user.modified_by = current_admin_id

            session.commit()
            self.logger.info(
                f"User '{user.user_id}' updated successfully by {current_admin_id}."
            )
            return True, "User updated successfully."
        except (
            sqlalchemy_exc.IntegrityError
        ) as e:  # Catch potential unique constraint on email update
            session.rollback()
            self.logger.error(
                f"Error updating user '{login_id_str_pk}': {e.orig}", exc_info=True
            )
            if "unique constraint failed: users.email" in str(e.orig).lower():
                return (
                    False,
                    f"Email '{validation_data['email']}' is already in use by another user.",
                )
            return False, f"Database integrity error: {e.orig}"
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
        # This method remains unchanged from v1.2.2
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
            user.modified_by = current_admin_id
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
        # This method remains unchanged from v1.2.2
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(func.upper(User.user_id) == login_id_str.upper())
                .first()
            )
            if user and user.roles:
                return [role.name for role in user.roles]
            return []
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error fetching roles for user '{login_id_str}': {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def delete_user_permanently(
        self, user_id_to_delete: str, current_admin_id: str
    ) -> Tuple[bool, str]:
        # This method remains unchanged from v1.2.2
        session = db_manager.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id_to_delete).first()
            if not user:
                return False, f"User '{user_id_to_delete}' not found."

            if user.user_id.upper() == "ADMIN":
                active_admin_count = (
                    session.query(User)
                    .filter(User.is_active == True, func.upper(User.user_id) == "ADMIN")
                    .count()
                )
                if active_admin_count <= 1:
                    self.logger.warning(
                        f"Attempt to delete the last (or only) ADMIN user ('{user_id_to_delete}') by '{current_admin_id}' was prevented."
                    )
                    return (
                        False,
                        "Cannot delete the primary ADMIN account if it's the last one.",
                    )

            session.delete(user)
            session.commit()
            self.logger.info(
                f"User '{user_id_to_delete}' permanently deleted by admin '{current_admin_id}'."
            )
            return True, f"User '{user_id_to_delete}' deleted successfully."
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
