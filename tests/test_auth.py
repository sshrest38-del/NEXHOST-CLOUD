"""
NEXHOST CLOUD - Authentication and User Registration Tests
Author: @Harsh_54x
"""

import sys
import os
from pathlib import Path
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from database.users import UserRepository
from auth.registration import register_user
from auth.authentication import login
from auth.password_reset import change_password

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_user_registration_success():
    email = "test_dev@example.com"
    username = "test_dev"
    pw = "SecretPassword123"

    ok, msg, user = register_user(email, username, pw, full_name="Test Dev")
    assert ok is True
    assert user is not None
    assert user.email == email
    assert user.username == username
    assert user.role == "free_user"

def test_duplicate_registration_rejected():
    email = "duplicate@example.com"
    username = "dup_user"
    pw = "SecretPass123"

    ok1, _, _ = register_user(email, username, pw)
    assert ok1 is True

    # Duplicate email
    ok2, msg2, _ = register_user(email, "other_user", pw)
    assert ok2 is False
    assert "email address already exists" in msg2

    # Duplicate username
    ok3, msg3, _ = register_user("other@example.com", username, pw)
    assert ok3 is False
    assert "username is already taken" in msg3

def test_login_flow():
    email = "login_test@example.com"
    username = "login_user"
    pw = "LoginPass2026"
    register_user(email, username, pw)

    # Success by email
    ok, msg, user = login(email, pw)
    assert ok is True
    assert user.username == username

    # Success by username
    ok, msg, user = login(username, pw)
    assert ok is True

    # Failure with invalid password
    ok_fail, msg_fail, _ = login(email, "WrongPassword")
    assert ok_fail is False
    assert "Invalid password" in msg_fail

    # Failure with non-existent user
    ok_non, _, _ = login("nonexistent@domain.com", pw)
    assert ok_non is False

def test_password_change():
    email = "pw_change@example.com"
    username = "pw_user"
    old_pw = "OldPassword123"
    new_pw = "NewPassword456"

    _, _, user = register_user(email, username, old_pw)

    # Change with correct old password
    ok, msg = change_password(user.id, old_pw, new_pw)
    assert ok is True

    # Verify old password fails and new password succeeds
    ok_old, _, _ = login(email, old_pw)
    assert ok_old is False

    ok_new, _, _ = login(email, new_pw)
    assert ok_new is True
