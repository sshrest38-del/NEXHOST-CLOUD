"""
NEXHOST CLOUD - Membership Limits and Expiry Tests
Author: @Harsh_54x
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.projects import ProjectRepository
from auth.registration import register_user
from core.membership_engine import MembershipEngine

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_free_plan_quota_enforcement():
    _, _, user = register_user("quota_user@test.com", "quota_user", "Pass123456")

    # Initial limits: 1 bot slot
    limits = MembershipEngine.get_user_limits(user.id)
    assert limits["plan_name"] == "FREE"
    assert limits["max_bots"] == 1
    assert limits["remaining_slots"] == 1

    can_create1, _ = MembershipEngine.can_create_bot(user.id)
    assert can_create1 is True

    # Create 1 bot
    proj1 = ProjectRepository.create(user.id, "Bot One")
    limits2 = MembershipEngine.get_user_limits(user.id)
    assert limits2["current_bots"] == 1
    assert limits2["remaining_slots"] == 0

    # Attempting to create 2nd bot must be blocked!
    can_create2, reason = MembershipEngine.can_create_bot(user.id)
    assert can_create2 is False
    assert "Bot slot limit reached" in reason

def test_membership_upgrade_expands_capacity():
    _, _, user = register_user("upgrade_user@test.com", "upgrade_user", "Pass123456")

    # Initially Free (1 bot)
    ProjectRepository.create(user.id, "Free Bot")
    assert MembershipEngine.can_create_bot(user.id)[0] is False

    # Upgrade to STARTER (3 bots)
    starter_plan = PlanRepository.get_by_name("STARTER")
    MembershipRepository.assign_plan(user.id, starter_plan)

    limits = MembershipEngine.get_user_limits(user.id)
    assert limits["plan_name"] == "STARTER"
    assert limits["max_bots"] == 3
    assert limits["remaining_slots"] == 2

    # Now allowed to create additional bots
    can_create, _ = MembershipEngine.can_create_bot(user.id)
    assert can_create is True
