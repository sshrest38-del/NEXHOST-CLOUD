"""
NEXHOST CLOUD - Telegram Bot & Owner Access Control Tests
Author: @Harsh_54x (https://t.me/Harsh_54x)
"""

import pytest
from database.users import UserRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.mongo import MongoLogger
import config

def test_telegram_user_auto_registration():
    """Verify that a new Telegram user gets registered and initialized with FREE tier."""
    tg_id = 998877665
    user = UserRepository.get_or_create_by_telegram(
        telegram_id=tg_id,
        tg_username="test_tg_user",
        full_name="Test Telegram User"
    )
    assert user is not None
    assert user.telegram_id == tg_id
    assert user.username == "test_tg_user"
    # By default, new users must NOT be authorized until owner approves
    assert UserRepository.is_telegram_authorized(tg_id) is False

def test_telegram_access_request_and_owner_approval():
    """Verify the access request state machine: request -> pending -> approve -> revoke."""
    tg_id = 112233445
    user = UserRepository.get_or_create_by_telegram(
        telegram_id=tg_id,
        tg_username="developer_pro",
        full_name="Developer Pro"
    )

    # 1. User requests access
    ok_req = UserRepository.set_telegram_access_requested(tg_id, True)
    assert ok_req is True

    pending_list = UserRepository.list_pending_telegram_requests()
    assert any(u.telegram_id == tg_id for u in pending_list)

    # 2. Owner approves request with PRO tier
    ok_auth = UserRepository.authorize_telegram_user(tg_id, role="premium_user")
    assert ok_auth is True

    # User is now authorized
    assert UserRepository.is_telegram_authorized(tg_id) is True

    # Verify no longer in pending list
    updated_pending = UserRepository.list_pending_telegram_requests()
    assert not any(u.telegram_id == tg_id for u in updated_pending)

    # 3. Owner revokes access
    UserRepository.deauthorize_telegram_user(tg_id)
    assert UserRepository.is_telegram_authorized(tg_id) is False

def test_owner_id_always_authorized(monkeypatch):
    """Verify configured master TELEGRAM_OWNER_ID bypasses authorization check."""
    owner_id = 777888999
    monkeypatch.setattr(config, "TELEGRAM_OWNER_ID", owner_id)

    # Even without DB entry, owner is authorized
    assert UserRepository.is_telegram_authorized(owner_id) is True

def test_mongo_graceful_fallback():
    """Verify MongoLogger handles unconfigured or unreachable MongoDB gracefully."""
    # Should not raise exception
    available = MongoLogger.is_available()
    assert isinstance(available, bool)
    
    # Event logging should return false gracefully if not available without crashing
    result = MongoLogger.log_telegram_action(123456, "tester", "test_action")
    assert isinstance(result, bool)
