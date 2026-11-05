"""
NEXHOST CLOUD - User Membership Record Model and Repository
Author: @Harsh_54x
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base, get_db
from database.plans import Plan

class UserMembership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRED, CANCELLED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_lifetime = Column(Boolean, default=False, nullable=False)

    plan = relationship("Plan", lazy="joined")

class MembershipRepository:
    @staticmethod
    def get_active_membership(user_id: int) -> Optional[UserMembership]:
        """Fetch current valid active membership. Automatically handles expiration check."""
        with get_db() as db:
            now = datetime.now(timezone.utc)
            # Check for lifetime membership first
            lifetime = db.query(UserMembership).filter(
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE",
                UserMembership.is_lifetime == True
            ).first()
            if lifetime:
                return lifetime

            # Check standard membership
            membership = db.query(UserMembership).filter(
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE"
            ).order_by(UserMembership.id.desc()).first()

            if membership:
                # Compare naive or aware datetime safely
                exp = membership.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now and not membership.is_lifetime:
                    # Expired: update status
                    membership.status = "EXPIRED"
                    db.commit()
                    return None
            return membership

    @staticmethod
    def assign_plan(user_id: int, plan: Plan, duration_days: Optional[int] = None) -> UserMembership:
        """Assign or upgrade plan for a user."""
        with get_db() as db:
            now = datetime.now(timezone.utc)
            days = duration_days if duration_days is not None else plan.duration_days
            is_lifetime = (plan.name == "LIFETIME" or days >= 30000)

            # Deactivate previous active memberships
            prev_active = db.query(UserMembership).filter(
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE"
            ).all()
            for m in prev_active:
                m.status = "CANCELLED"

            new_membership = UserMembership(
                user_id=user_id,
                plan_id=plan.id,
                status="ACTIVE",
                started_at=now,
                expires_at=now + timedelta(days=days),
                is_lifetime=is_lifetime
            )
            db.add(new_membership)
            db.commit()
            db.refresh(new_membership)
            return new_membership

    @staticmethod
    def extend_membership(membership_id: int, additional_days: int) -> Optional[UserMembership]:
        """Extend active membership expiry."""
        with get_db() as db:
            m = db.query(UserMembership).filter(UserMembership.id == membership_id).first()
            if m:
                m.expires_at = m.expires_at + timedelta(days=additional_days)
                m.status = "ACTIVE"
                db.commit()
                db.refresh(m)
                return m
            return None

    @staticmethod
    def list_history(user_id: int) -> List[UserMembership]:
        """Fetch all membership records for user."""
        with get_db() as db:
            return db.query(UserMembership).filter(
                UserMembership.user_id == user_id
            ).order_by(UserMembership.id.desc()).all()
