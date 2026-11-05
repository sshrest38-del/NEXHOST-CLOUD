"""
NEXHOST CLOUD - Password Reset and Security Credentials Management
Author: @Harsh_54x
"""

from typing import Tuple
from database.users import UserRepository
from database.audit_logs import AuditLogRepository
from utils.security import hash_password, verify_password

def change_password(user_id: int, current_pass: str, new_pass: str) -> Tuple[bool, str]:
    """Change account password with current password verification."""
    user = UserRepository.get_by_id(user_id)
    if not user:
        return False, "User not found."

    if not verify_password(user.password_hash, current_pass):
        return False, "Current password is incorrect."

    if len(new_pass) < 6:
        return False, "New password must be at least 6 characters long."

    new_hash = hash_password(new_pass)
    UserRepository.update_password(user_id, new_hash)
    AuditLogRepository.record(user_id, "PASSWORD_CHANGED", "AUTH", "User successfully changed password")
    return True, "Password updated successfully!"

def reset_password_admin(admin_user_id: int, target_user_id: int, new_pass: str) -> Tuple[bool, str]:
    """Admin overrides user password."""
    target_user = UserRepository.get_by_id(target_user_id)
    if not target_user:
        return False, "User not found."

    if len(new_pass) < 6:
        return False, "New password must be at least 6 characters long."

    new_hash = hash_password(new_pass)
    UserRepository.update_password(target_user_id, new_hash)
    AuditLogRepository.record(admin_user_id, "ADMIN_PASSWORD_RESET", "AUTH", f"Admin reset password for {target_user.username}")
    return True, f"Password for {target_user.username} reset successfully."
