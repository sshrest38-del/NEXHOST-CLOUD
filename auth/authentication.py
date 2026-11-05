"""
NEXHOST CLOUD - Authentication Logic and Login Service
Author: @Harsh_54x
"""

from typing import Tuple, Optional
from database.users import User, UserRepository
from database.audit_logs import AuditLogRepository
from utils.security import verify_password
from auth.sessions import set_login_session, clear_session

def login(email_or_username: str, password: str) -> Tuple[bool, str, Optional[User]]:
    """
    Authenticate user by email or username with secure password hashing.
    Returns: (success: bool, message: str, user: Optional[User])
    """
    ident = (email_or_username or "").strip()
    if not ident or not password:
        return False, "Please enter both username/email and password.", None

    # Try lookup by email first, then username
    user = UserRepository.get_by_email(ident) or UserRepository.get_by_username(ident)
    if not user:
        return False, "Invalid credentials. User does not exist.", None

    if not user.is_active:
        return False, "Account suspended. Please contact platform support @Harsh_54x.", None

    if not verify_password(user.password_hash, password):
        AuditLogRepository.record(user.id, "LOGIN_FAILED", "AUTH", "Invalid password attempt")
        return False, "Invalid password. Please check your credentials.", None

    # Success: set session
    set_login_session(user)
    AuditLogRepository.record(user.id, "LOGIN_SUCCESS", "AUTH", f"User {user.username} logged in successfully")
    return True, f"Welcome back, {user.full_name or user.username}!", user

def logout():
    """Terminate user session."""
    user = UserRepository.get_by_id(st.session_state.get("user_id") if "user_id" in st.session_state else 0)
    if user:
        AuditLogRepository.record(user.id, "LOGOUT", "AUTH", f"User {user.username} logged out")
    clear_session()
