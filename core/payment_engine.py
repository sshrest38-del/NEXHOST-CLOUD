"""
NEXHOST CLOUD - Manual UPI Payment Engine and Approval Workflow
Author: @Harsh_54x
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from database.users import UserRepository
from database.plans import PlanRepository
from database.memberships import MembershipRepository
from database.payments import Payment, PaymentRepository
from database.audit_logs import AuditLogRepository, NotificationRepository
from services.storage_service import StorageService
from utils.validators import validate_upi_reference
from utils.logger import logger

class PaymentEngine:
    @classmethod
    def submit_payment_request(cls, user_id: int, plan_id: int, upi_ref_id: str,
                               screenshot_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[Payment]]:
        """
        Handle user submission of a manual UPI payment with proof screenshot.
        Strictly prevents duplicate transaction reference numbers.
        """
        clean_ref = (upi_ref_id or "").strip().upper()
        if not validate_upi_reference(clean_ref):
            return False, "Invalid UPI Reference ID / UTR. Must be 8-35 alphanumeric characters.", None

        if PaymentRepository.is_upi_ref_used(clean_ref):
            return False, f"Transaction reference '{clean_ref}' has already been registered in the system. Duplicate submissions are rejected.", None

        plan = PlanRepository.get_by_id(plan_id)
        if not plan:
            return False, "Selected membership plan does not exist.", None

        if not screenshot_bytes or len(screenshot_bytes) < 100:
            return False, "Please upload a valid payment proof screenshot.", None

        # Save screenshot safely
        proofs_dir = StorageService.get_payments_dir()
        ext = Path(filename).suffix.lower() if filename else ".png"
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            ext = ".png"
        safe_filename = f"proof_u{user_id}_{clean_ref}{ext}"
        screenshot_path = proofs_dir / safe_filename

        try:
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_bytes)
        except Exception as e:
            logger.error(f"Failed to save payment screenshot: {e}")
            return False, f"Error saving payment screenshot: {str(e)}", None

        # Record payment in DB
        success, msg, payment = PaymentRepository.create(
            user_id=user_id,
            plan_id=plan.id,
            amount_inr=plan.price_inr,
            upi_ref_id=clean_ref,
            screenshot_path=str(screenshot_path)
        )

        if success:
            NotificationRepository.send(
                user_id=user_id,
                title="Payment Submitted",
                message=f"Your UPI payment of ₹{plan.price_inr:,.0f} (Ref: {clean_ref}) for {plan.display_name} has been received and is pending admin verification.",
                level="INFO"
            )
            AuditLogRepository.record(user_id, "PAYMENT_SUBMITTED", "PAYMENT", f"UPI Ref {clean_ref} submitted for Plan {plan.name}")

        return success, msg, payment

    @classmethod
    def approve_payment(cls, payment_id: int, reviewer_id: int, notes: str = "") -> Tuple[bool, str]:
        """
        Admin approves payment:
        1. Verifies payment state.
        2. Assigns/upgrades the user's membership.
        3. Updates user role to premium_user (preserving admin status).
        4. Notifies user and writes audit logs.
        """
        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            return False, "Payment record not found."

        if payment.status == "APPROVED":
            return False, "This payment has already been approved."

        # Approve in database
        ok, msg = PaymentRepository.approve(payment_id, reviewer_id, notes)
        if not ok:
            return False, msg

        # Activate plan membership
        plan = PlanRepository.get_by_id(payment.plan_id)
        if plan:
            MembershipRepository.assign_plan(payment.user_id, plan)

        # Update role to premium_user if currently free_user
        user = UserRepository.get_by_id(payment.user_id)
        if user and user.role == "free_user":
            UserRepository.update_role(user.id, "premium_user")

        # Notify user
        NotificationRepository.send(
            user_id=payment.user_id,
            title="Payment Approved! Membership Active",
            message=f"Your payment of ₹{payment.amount_inr:,.0f} (Ref: {payment.upi_ref_id}) has been verified! Your {plan.display_name if plan else 'Premium'} membership is now active.",
            level="SUCCESS"
        )

        AuditLogRepository.record(
            reviewer_id,
            "PAYMENT_APPROVED",
            "PAYMENT",
            f"Admin {reviewer_id} approved payment #{payment_id} for user #{payment.user_id} (Ref: {payment.upi_ref_id})"
        )

        return True, f"Payment #{payment_id} approved and membership plan activated successfully!"

    @classmethod
    def reject_payment(cls, payment_id: int, reviewer_id: int, reason: str, notes: str = "") -> Tuple[bool, str]:
        """Admin rejects payment with reason."""
        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            return False, "Payment record not found."

        if payment.status == "APPROVED":
            return False, "Cannot reject an already approved payment."

        ok, msg = PaymentRepository.reject(payment_id, reviewer_id, reason, notes)
        if not ok:
            return False, msg

        # Notify user
        NotificationRepository.send(
            user_id=payment.user_id,
            title="Payment Verification Failed",
            message=f"Your payment (Ref: {payment.upi_ref_id}) was rejected by administrator. Reason: {reason}",
            level="ERROR"
        )

        AuditLogRepository.record(
            reviewer_id,
            "PAYMENT_REJECTED",
            "PAYMENT",
            f"Admin rejected payment #{payment_id} (Ref: {payment.upi_ref_id}). Reason: {reason}"
        )

        return True, f"Payment #{payment_id} rejected."
