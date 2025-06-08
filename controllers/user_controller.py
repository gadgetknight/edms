# controllers/user_controller.py
"""
EDSI Veterinary Management System - User Controller
Version: 1.3.0
Purpose: Handles user authentication, CRUD operations.
         - Standardized get_all_users filter to use a string-based status_filter.
Last Updated: June 5, 2025
Author: Gemini

Changelog:
- v1.3.0 (2025-06-05):
    - Modified `get_all_users` to accept a string `status_filter` ('active',
      'inactive', 'all') for consistency with other controllers.
- v1.2.8 (2025-06-05):
    - In `toggle_user_active_status`, added a check to prevent a user from
      deactivating their own account, moving this business rule from the
      view into the controller for better enforcement.
- v1.2.7 (2025-06-05):
    - Added `toggle_user_active_status` method to handle activating and
      deactivating users, including a safeguard to prevent deactivating the
      last active ADMIN account.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, exc as sqlalchemy_exc
from datetime import datetime

from config.database_config import db_manager
from models.user_models import User, Role, UserRole


class UserController:
    """Controller for user management operations."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def authenticate_user(
        self, login_id_attempt: str, password_attempt: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        # ... (implementation unchanged) ...
        try:
            self.logger.info(
                f"UserController.authenticate_user received login_id: '{login_id_attempt}', "
                f"password_attempt (first 3 chars): '{password_attempt[:3] if password_attempt else ''}...'"
            )
            session = db_manager.get_session()
            try:
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
                            "user_id": user.user_id,
                            "user_name": user.user_name,
                            "is_active": user.is_active,
                        },
                    )
                if hasattr(user, "last_login"):
                    user.last_login = datetime.utcnow()
                session.commit()
                self.logger.info(f"User '{user.user_id}' authenticated successfully.")
                return (
                    True,
                    "Login successful.",
                    {
                        "user_id": user.user_id,
                        "user_name": user.user_name,
                        "is_active": user.is_active,
                    },
                )
            except sqlalchemy_exc.SQLAlchemyError as e_db:
                session.rollback()
                self.logger.error(
                    f"Database error during authentication for '{login_id_attempt}': {e_db}",
                    exc_info=True,
                )
                return False, "An error occurred during login. Please try again.", None
            finally:
                session.close()
        except Exception as e_outer:
            self.logger.error(
                f"Outer unexpected error during authentication for '{login_id_attempt}': {e_outer}",
                exc_info=True,
            )
            return False, "An unexpected server error occurred. Please try again.", None

    def get_all_users(self, status_filter: str = "all") -> List[User]:
        session = db_manager.get_session()
        try:
            query = session.query(User).options(joinedload(User.roles))
            if status_filter == "active":
                query = query.filter(User.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(User.is_active == False)

            users = query.order_by(User.user_id).all()
            return users
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error fetching all users: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_user_by_login_id(self, login_id_str: str) -> Optional[User]:
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
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
        # ... (implementation unchanged) ...
        try:
            from views.admin.dialogs.add_edit_user_dialog import AddEditUserDialog

            available_roles_in_dialog = AddEditUserDialog.USER_ROLES
        except ImportError:
            self.logger.warning(
                "Could not import AddEditUserDialog for role validation. Role list might be incomplete."
            )
            available_roles_in_dialog = []
        errors = []
        login_id = user_data.get("user_id", "").strip()
        display_name = user_data.get("user_name", "").strip()
        password = user_data.get("password", "")
        email_value = user_data.get("email")
        email = email_value.strip() if isinstance(email_value, str) else None
        if not login_id:
            errors.append("Login ID (Username) is required.")
        elif len(login_id) > 20:
            errors.append("Login ID (Username) cannot exceed 20 characters.")
        elif " " in login_id:
            errors.append("Login ID (Username) cannot contain spaces.")
        else:
            session = db_manager.get_session()
            try:
                query = session.query(User).filter(
                    User.user_id.collate("NOCASE") == login_id
                )
                if not is_new and original_login_id_to_ignore is not None:
                    query = query.filter(
                        User.user_id.collate("NOCASE") != original_login_id_to_ignore
                    )
                if query.first():
                    errors.append(f"Login ID (Username) '{login_id}' already exists.")
                if email:
                    email_query = session.query(User).filter(User.email == email)
                    user_to_exclude_from_email_check = None
                    if not is_new and original_login_id_to_ignore:
                        original_user = (
                            session.query(User)
                            .filter(
                                User.user_id.collate("NOCASE")
                                == original_login_id_to_ignore
                            )
                            .first()
                        )
                        if original_user:
                            user_to_exclude_from_email_check = original_user.user_id
                    if user_to_exclude_from_email_check:
                        email_query = email_query.filter(
                            User.user_id != user_to_exclude_from_email_check
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
        elif len(display_name) > 100:
            errors.append("Full Name (User Name) cannot exceed 100 characters.")
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
        if not role_str and is_new:
            errors.append("Role is required for new users.")
        if role_str:
            session = db_manager.get_session()
            try:
                if not session.query(Role).filter(Role.name == role_str).first():
                    errors.append(f"Role '{role_str}' does not exist in the database.")
            finally:
                session.close()
        return not errors, errors

    def create_user(
        self, user_data: Dict[str, Any], current_admin_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        # ... (implementation unchanged) ...
        login_id_to_store = user_data.get("user_id", "").strip()
        if not login_id_to_store:
            return False, "Login ID (Username) cannot be empty.", None
        if login_id_to_store.upper() == "ADMIN":
            login_id_to_store = "ADMIN"
        data_for_model = {
            "user_id": login_id_to_store,
            "user_name": user_data.get("user_name", "").strip(),
            "email": user_data.get("email"),
            "is_active": user_data.get("is_active", True),
            "created_by": current_admin_id,
            "modified_by": current_admin_id,
            "printer_id": user_data.get("printer_id"),
            "default_screen_colors": user_data.get("default_screen_colors"),
        }
        password_to_set = user_data.get("password", "")
        role_name_to_assign = user_data.get("role")
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
                if not processed_email:
                    processed_email = None
            data_for_model["email"] = processed_email
            new_user = User(**data_for_model)
            new_user.set_password(password_to_set)
            if role_name_to_assign:
                role_obj = (
                    session.query(Role).filter(Role.name == role_name_to_assign).first()
                )
                if role_obj:
                    new_user.roles.append(role_obj)
                else:
                    self.logger.error(
                        f"Role '{role_name_to_assign}' for new user '{new_user.user_id}' not found in DB during create. Validation might have missed this."
                    )
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
        except AttributeError as ae:
            session.rollback()
            self.logger.error(
                f"AttributeError during user creation for '{data_for_model.get('user_id')}': {ae}",
                exc_info=True,
            )
            return False, f"Failed to set user attribute during creation: {ae}", None
        except Exception as e:
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
        user_id_to_update: str,
        user_data: Dict[str, Any],
        current_admin_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id.collate("NOCASE") == user_id_to_update)
                .first()
            )
            if not user:
                return False, f"User with Login ID '{user_id_to_update}' not found."
            validation_data = {
                "user_id": user.user_id,
                "user_name": user_data.get("user_name", user.user_name),
                "email": user_data.get("email", user.email),
                "role": user_data.get("role"),
            }
            if "password" in user_data and user_data["password"]:
                validation_data["password"] = user_data["password"]
            is_valid, errors = self.validate_user_data(
                validation_data, is_new=False, original_login_id_to_ignore=user.user_id
            )
            if not is_valid:
                return False, "Validation failed: " + "; ".join(errors)
            roles_modified = False
            if "user_name" in user_data:
                user.user_name = user_data["user_name"].strip()
            if "email" in user_data:
                email_val = user_data["email"]
                user.email = email_val.strip() if isinstance(email_val, str) else None
                if user.email == "":
                    user.email = None
            if "password" in user_data and user_data["password"]:
                user.set_password(user_data["password"])
            if "is_active" in user_data:
                if user.user_id.upper() == "ADMIN" and not user_data["is_active"]:
                    active_admin_query = session.query(User).filter(
                        User.is_active == True,
                        User.user_id.collate("NOCASE") == "ADMIN",
                    )
                    if user.is_active:
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
            new_role_name_from_data = user_data.get("role")
            if new_role_name_from_data is not None:
                current_role_names = {r.name for r in user.roles}
                if not (
                    len(current_role_names) == 1
                    and new_role_name_from_data in current_role_names
                ):
                    roles_modified = True
                    user.roles.clear()
                    if new_role_name_from_data:
                        role_obj = (
                            session.query(Role)
                            .filter(Role.name == new_role_name_from_data)
                            .first()
                        )
                        if role_obj:
                            user.roles.append(role_obj)
                        else:
                            self.logger.error(
                                f"Role object for '{new_role_name_from_data}' not found during update. User '{user.user_id}' will have no roles."
                            )
            if "printer_id" in user_data:
                user.printer_id = user_data["printer_id"]
            if "default_screen_colors" in user_data:
                user.default_screen_colors = user_data["default_screen_colors"]
            user.modified_by = current_admin_id
            if roles_modified:
                session.add(user)
            session.commit()
            self.logger.info(
                f"User '{user.user_id}' updated successfully by {current_admin_id}."
            )
            return True, "User updated successfully."
        except sqlalchemy_exc.IntegrityError as e:
            session.rollback()
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
        current_admin_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        # ... (implementation unchanged) ...
        if not new_password or len(new_password) < 6:
            return False, "New password must be at least 6 characters long."
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == login_id_str)
                .first()
            )
            if not user:
                return False, f"User '{login_id_str}' not found."
            user.set_password(new_password)
            user.modified_by = current_admin_id
            session.commit()
            self.logger.info(
                f"Password changed successfully for user '{user.user_id}' by {current_admin_id}."
            )
            return True, "Password changed successfully."
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error changing password for user '{login_id_str}': {e}", exc_info=True
            )
            return False, f"Failed to change password: {str(e)}"
        finally:
            session.close()

    def get_user_roles(self, login_id_str: str) -> List[str]:
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .options(joinedload(User.roles))
                .filter(User.user_id.collate("NOCASE") == login_id_str)
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
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == user_id_to_delete)
                .first()
            )
            if not user:
                return False, f"User '{user_id_to_delete}' not found."
            if user.user_id.upper() == "ADMIN":
                active_admin_count = (
                    session.query(User)
                    .filter(
                        User.is_active == True,
                        User.user_id.collate("NOCASE") == "ADMIN",
                    )
                    .count()
                )
                if active_admin_count <= 1 and user.is_active:
                    self.logger.warning(
                        f"Attempt to delete the last active ADMIN user ('{user.user_id}') by '{current_admin_id}' was prevented."
                    )
                    return (
                        False,
                        "Cannot delete the primary ADMIN account if it's the last active one.",
                    )
            session.delete(user)
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

    def toggle_user_active_status(
        self, user_login_id: str, current_admin_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
            user = (
                session.query(User)
                .filter(User.user_id.collate("NOCASE") == user_login_id)
                .first()
            )
            if not user:
                return False, f"User '{user_login_id}' not found."

            is_deactivating = user.is_active
            if is_deactivating:
                # Rule 1: Cannot deactivate yourself
                if user.user_id == current_admin_id:
                    self.logger.warning(
                        f"User '{current_admin_id}' attempted to deactivate their own account. Operation prevented."
                    )
                    return False, "You cannot deactivate your own account."

                # Rule 2: Cannot deactivate the last active admin
                if user.has_role("ADMIN"):
                    active_admin_count = (
                        session.query(User)
                        .join(User.roles)
                        .filter(Role.name == "ADMIN", User.is_active == True)
                        .count()
                    )
                    if active_admin_count <= 1:
                        self.logger.warning(
                            f"Attempt to deactivate the last active ADMIN user ('{user.user_id}') by '{current_admin_id}' was prevented."
                        )
                        return False, "Cannot deactivate the last active ADMIN user."

            # Toggle the status
            new_status = not user.is_active
            user.is_active = new_status
            user.modified_by = current_admin_id

            session.commit()

            status_str = "activated" if new_status else "deactivated"
            self.logger.info(
                f"User '{user.user_id}' has been {status_str} by {current_admin_id}."
            )
            return True, f"User '{user.user_id}' has been successfully {status_str}."

        except sqlalchemy_exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(
                f"Database error toggling status for user '{user_login_id}': {e}",
                exc_info=True,
            )
            return False, "A database error occurred."
        finally:
            session.close()

    def get_all_roles(self) -> List[Role]:
        # ... (implementation unchanged) ...
        session = db_manager.get_session()
        try:
            roles = session.query(Role).order_by(Role.name).all()
            self.logger.info(f"Retrieved {len(roles)} roles.")
            return roles
        except sqlalchemy_exc.SQLAlchemyError as e:
            self.logger.error(f"Error retrieving roles: {e}", exc_info=True)
            session.rollback()
            return []
        finally:
            session.close()
