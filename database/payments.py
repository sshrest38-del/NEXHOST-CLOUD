"""
NEXHOST CLOUD - Manual UPI Payment Model and Repository
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from database.connection import Base, get_db

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    amount_inr = Column(Float, nullable=False)
    upi_ref_id = Column(String(100), unique=True, index=True, nullable=False)  # Enforce uniqueness!
    screenshot_path = Column(String(255), nullable=False)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, UNDER_REVIEW, APPROVED, REJECTED, REFUNDED
    rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    plan = relationship("Plan", lazy="joined")

class PaymentRepository:
    @staticmethod
    def is_upi_ref_used(upi_ref_id: str) -> bool:
        """Check if UPI reference is already submitted."""
        with get_db() as db:
            clean = upi_ref_id.strip().upper()
            return db.query(Payment).filter(Payment.upi_ref_id == clean).count() > 0

    @staticmethod
    def create(user_id: int, plan_id: int, amount_inr: float, upi_ref_id: str, screenshot_path: str) -> Tuple[bool, str, Optional[Payment]]:
        """
        Record manual UPI payment. Validates uniqueness of transaction reference.
        """
        clean_ref = upi_ref_id.strip().upper()
        if PaymentRepository.is_upi_ref_used(clean_ref):
            return False, f"Duplicate reference ID '{clean_ref}' has already been submitted.", None

        with get_db() as db:
            payment = Payment(
                user_id=user_id,
                plan_id=plan_id,
                amount_inr=amount_inr,
                upi_ref_id=clean_ref,
                screenshot_path=screenshot_path,
                status="PENDING",
                created_at=datetime.now(timezone.utc)
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return True, "Payment request submitted successfully for admin review.", payment

    @staticmethod
    def get_by_id(payment_id: int) -> Optional[Payment]:
        with get_db() as db:
            return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def list_by_user(user_id: int) -> List[Payment]:
        with get_db() as db:
            return db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.id.desc()).all()

    @staticmethod
    def list_pending() -> List[Payment]:
        with get_db() as db:
            return db.query(Payment).filter(
                Payment.status.in_(["PENDING", "UNDER_REVIEW"])
            ).order_by(Payment.id.desc()).all()

    @staticmethod
    def list_all() -> List[Payment]:
        with get_db() as db:
            return db.query(Payment).order_by(Payment.id.desc()).all()

    @staticmethod
    def approve(payment_id: int, reviewer_id: int, notes: str = "") -> Tuple[bool, str]:
        """Approve payment, marking it approved and returning success."""
        with get_db() as db:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                return False, "Payment record not found."
            if payment.status == "APPROVED":
                return False, "Payment is already approved."

            payment.status = "APPROVED"
            payment.reviewed_by = reviewer_id
            payment.admin_notes = notes
            payment.reviewed_at = datetime.now(timezone.utc)
            db.commit()
            return True, "Payment verified and approved successfully."

    @staticmethod
    def reject(payment_id: int, reviewer_id: int, reason: str, notes: str = "") -> Tuple[bool, str]:
        """Reject payment with reason."""
        with get_db() as db:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                return False, "Payment record not found."
            if payment.status == "APPROVED":
                return False, "Cannot reject already approved payment."

            payment.status = "REJECTED"
            payment.reviewed_by = reviewer_id
            payment.rejection_reason = reason
            payment.admin_notes = notes
            payment.reviewed_at = datetime.now(timezone.utc)
            db.commit()
            return True, "Payment rejected."
