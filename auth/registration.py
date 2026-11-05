"""
NEXHOST CLOUD - User Registration Service
Author: @Harsh_54x
"""

from typing import Tuple, Optional
from database.users import User, UserRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.audit_logs import AuditLogRepository, NotificationRepository
from utils.security import hash_password
from utils.validators import validate_email, validate_username

def register_user(email: str, username: str, password: str, full_name: str = "") -> Tuple[bool, str, Optional[User]]:
    """
    Register new user account, hash password, and assign default Free plan.
    """
    email_clean = (email or "").strip().lower()
    username_clean = (username or "").strip().lower()
    full_name_clean = (full_name or "").strip()

    if not validate_email(email_clean):
        return False, "Please provide a valid email address.", None

    if not validate_username(username_clean):
        return False, "Username must be 3-30 alphanumeric characters or underscores.", None

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    # Check for existing email
    if UserRepository.get_by_email(email_clean):
        return False, "An account with this email address already exists.", None

    # Check for existing username
    if UserRepository.get_by_username(username_clean):
        return False, "This username is already taken. Please choose another.", None

    # Create user
    pw_hash = hash_password(password)
    user = UserRepository.create(
        email=email_clean,
        username=username_clean,
        password_hash=pw_hash,
        full_name=full_name_clean or username_clean,
        role="free_user"
    )

    # Assign default FREE Plan
    free_plan = PlanRepository.get_by_name("FREE")
    if free_plan:
        MembershipRepository.assign_plan(user.id, free_plan)

    # Send Welcome Notification
    NotificationRepository.send(
        user_id=user.id,
        title="Welcome to NEXHOST CLOUD!",
        message=f"Welcome aboard, {user.username}! Your Free Plan has been activated. Start hosting your Telegram bots in seconds.",
        level="SUCCESS"
    )

    AuditLogRepository.record(user.id, "USER_REGISTERED", "AUTH", f"New user {user.username} registered")
    return True, "Account registered successfully! You can now log in.", user
