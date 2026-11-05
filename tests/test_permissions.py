"""
NEXHOST CLOUD - Role Permissions and Resource Isolation Tests
Author: @Harsh_54x
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from database.users import UserRepository
from database.projects import ProjectRepository
from auth.registration import register_user
from auth.permissions import is_admin, is_super_admin, is_premium, can_access_project

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_roles_and_permissions():
    _, _, free_u = register_user("role_free@test.com", "role_free", "Pass123456")
    assert not is_admin(free_u)
    assert not is_super_admin(free_u)
    assert not is_premium(free_u)

    # Upgrade to premium
    UserRepository.update_role(free_u.id, "premium_user")
    free_u_updated = UserRepository.get_by_id(free_u.id)
    assert is_premium(free_u_updated)
    assert not is_admin(free_u_updated)

    # Upgrade to admin
    UserRepository.update_role(free_u.id, "admin")
    admin_u = UserRepository.get_by_id(free_u.id)
    assert is_admin(admin_u)
    assert is_premium(admin_u)

def test_strict_user_data_isolation():
    """
    CRITICAL: User A must never have access to User B's project resources.
    """
    _, _, user_a = register_user("user_a@test.com", "user_a", "Pass123456")
    _, _, user_b = register_user("user_b@test.com", "user_b", "Pass123456")

    # User A creates a project
    proj_a = ProjectRepository.create(user_id=user_a.id, name="User A Secret Bot")

    # User A CAN access their project
    assert can_access_project(user_a.id, proj_a.id) is True

    # User B CANNOT access User A's project
    assert can_access_project(user_b.id, proj_a.id) is False

    # Direct repository check for user isolation
    isolated_query = ProjectRepository.get_user_project(user_b.id, proj_a.id)
    assert isolated_query is None
