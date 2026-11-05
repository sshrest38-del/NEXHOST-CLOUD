"""
NEXHOST CLOUD - Manual UPI Payment Flow and Verification Tests
Author: @Harsh_54x
"""

import sys
import secrets
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from database.users import UserRepository
from database.plans import PlanRepository
from database.payments import PaymentRepository
from auth.registration import register_user
from core.payment_engine import PaymentEngine
from core.membership_engine import MembershipEngine

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_manual_upi_payment_flow():
    _, _, user = register_user("payer@test.com", "payer", "Pass123456")
    admin = UserRepository.get_by_email("owner@nexhost.cloud")
    starter_plan = PlanRepository.get_by_name("STARTER")

    utr = f"UPI{secrets.token_hex(6).upper()}"
    dummy_screenshot = b"FAKE_PNG_BINARY_DATA_FOR_SCREENSHOT_VERIFICATION_TESTING" * 5

    # Step 1: User submits payment request
    ok, msg, payment = PaymentEngine.submit_payment_request(
        user_id=user.id,
        plan_id=starter_plan.id,
        upi_ref_id=utr,
        screenshot_bytes=dummy_screenshot,
        filename="proof.png"
    )
    assert ok is True
    assert payment is not None
    assert payment.status == "PENDING"
    assert payment.upi_ref_id == utr

    # User membership must STILL be FREE (uploading screenshot does NOT auto-activate!)
    limits_before = MembershipEngine.get_user_limits(user.id)
    assert limits_before["plan_name"] == "FREE"

    # Step 2: Test duplicate UTR rejection
    ok_dup, msg_dup, _ = PaymentEngine.submit_payment_request(
        user_id=user.id,
        plan_id=starter_plan.id,
        upi_ref_id=utr,
        screenshot_bytes=dummy_screenshot,
        filename="proof.png"
    )
    assert ok_dup is False
    assert "Duplicate" in msg_dup or "already been registered" in msg_dup

    # Step 3: Admin approves payment
    ok_app, msg_app = PaymentEngine.approve_payment(payment.id, reviewer_id=admin.id, notes="Verified in bank")
    assert ok_app is True

    # User membership is now STARTER!
    limits_after = MembershipEngine.get_user_limits(user.id)
    assert limits_after["plan_name"] == "STARTER"

    # User role upgraded to premium_user
    updated_user = UserRepository.get_by_id(user.id)
    assert updated_user.role == "premium_user"

def test_payment_rejection_flow():
    _, _, user = register_user("rejected_payer@test.com", "rej_payer", "Pass123456")
    admin = UserRepository.get_by_email("owner@nexhost.cloud")
    pro_plan = PlanRepository.get_by_name("PRO")

    utr = f"REJ{secrets.token_hex(6).upper()}"
    dummy_screenshot = b"FAKE_IMAGE_DATA_FOR_REJECTION" * 5

    ok, _, payment = PaymentEngine.submit_payment_request(
        user_id=user.id,
        plan_id=pro_plan.id,
        upi_ref_id=utr,
        screenshot_bytes=dummy_screenshot,
        filename="proof.jpg"
    )
    assert ok is True

    # Admin rejects payment
    reason = "Transaction reference was not found in bank statement."
    ok_rej, msg_rej = PaymentEngine.reject_payment(payment.id, reviewer_id=admin.id, reason=reason)
    assert ok_rej is True

    updated_payment = PaymentRepository.get_by_id(payment.id)
    assert updated_payment.status == "REJECTED"
    assert updated_payment.rejection_reason == reason
