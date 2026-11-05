"""
NEXHOST CLOUD - Membership Plan Model and Repository
Author: @Harsh_54x
"""

from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from database.connection import Base, get_db

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False) # FREE, STARTER, PRO, BUSINESS, LIFETIME
    display_name = Column(String(100), nullable=False)
    price_inr = Column(Float, default=0.0, nullable=False)
    max_bots = Column(Integer, default=1, nullable=False)
    max_ram_mb = Column(Integer, default=256, nullable=False)
    max_cpu_cores = Column(Float, default=0.5, nullable=False)
    max_storage_mb = Column(Integer, default=500, nullable=False)
    backup_enabled = Column(Boolean, default=False, nullable=False)
    support_tier = Column(String(50), default="Community", nullable=False)
    duration_days = Column(Integer, default=30, nullable=False)  # 30, 365, 36500 (lifetime)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

class PlanRepository:
    @staticmethod
    def get_by_id(plan_id: int) -> Optional[Plan]:
        with get_db() as db:
            return db.query(Plan).filter(Plan.id == plan_id).first()

    @staticmethod
    def get_by_name(name: str) -> Optional[Plan]:
        with get_db() as db:
            return db.query(Plan).filter(Plan.name == name.upper().strip()).first()

    @staticmethod
    def list_all(active_only: bool = False) -> List[Plan]:
        with get_db() as db:
            query = db.query(Plan)
            if active_only:
                query = query.filter(Plan.is_active == True)
            return query.order_by(Plan.price_inr.asc()).all()

    @staticmethod
    def create(name: str, display_name: str, price_inr: float, max_bots: int, max_ram_mb: int,
               max_cpu_cores: float, max_storage_mb: int, backup_enabled: bool,
               support_tier: str, duration_days: int, description: str) -> Plan:
        with get_db() as db:
            plan = Plan(
                name=name.upper().strip(),
                display_name=display_name.strip(),
                price_inr=price_inr,
                max_bots=max_bots,
                max_ram_mb=max_ram_mb,
                max_cpu_cores=max_cpu_cores,
                max_storage_mb=max_storage_mb,
                backup_enabled=backup_enabled,
                support_tier=support_tier,
                duration_days=duration_days,
                description=description,
                is_active=True
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return plan

    @staticmethod
    def update(plan_id: int, **kwargs) -> Optional[Plan]:
        with get_db() as db:
            plan = db.query(Plan).filter(Plan.id == plan_id).first()
            if not plan:
                return None
            for key, val in kwargs.items():
                if hasattr(plan, key) and val is not None:
                    setattr(plan, key, val)
            db.commit()
            db.refresh(plan)
            return plan
