"""
NEXHOST CLOUD - Role-Based Access Control and Resource Permissions
Author: @Harsh_54x
"""

from typing import Optional
from database.users import User, UserRepository
from database.projects import Project, ProjectRepository
from auth.sessions import get_current_user

def is_super_admin(user: Optional[User] = None) -> bool:
    """Check if user has super admin owner privileges."""
    u = user or get_current_user()
    return bool(u and u.is_active and u.role == "super_admin")

def is_admin(user: Optional[User] = None) -> bool:
    """Check if user is admin or super admin."""
    u = user or get_current_user()
    return bool(u and u.is_active and u.role in ["admin", "super_admin"])

def is_premium(user: Optional[User] = None) -> bool:
    """Check if user has premium status."""
    u = user or get_current_user()
    return bool(u and u.is_active and u.role in ["premium_user", "admin", "super_admin"])

def can_access_project(user_id: int, project_id: int) -> bool:
    """
    STRICT RESOURCE ISOLATION:
    Enforces that a regular user can ONLY access their own projects.
    Admins can inspect projects for support purposes.
    """
    user = UserRepository.get_by_id(user_id)
    if not user or not user.is_active:
        return False
    if user.role in ["super_admin", "admin"]:
        return True

    proj = ProjectRepository.get_user_project(user_id, project_id)
    return proj is not None
