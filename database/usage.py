"""
NEXHOST CLOUD - Resource Telemetry and Metric Records
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime
from database.connection import Base, get_db

class ResourceUsage(Base):
    __tablename__ = "resource_usage"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=False)
    cpu_percent = Column(Float, default=0.0, nullable=False)
    memory_mb = Column(Float, default=0.0, nullable=False)
    storage_mb = Column(Float, default=0.0, nullable=False)
    network_rx_mb = Column(Float, default=0.0, nullable=False)
    network_tx_mb = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class UsageRepository:
    @staticmethod
    def record(project_id: int, cpu_percent: float, memory_mb: float, storage_mb: float,
               rx_mb: float = 0.0, tx_mb: float = 0.0) -> ResourceUsage:
        with get_db() as db:
            usage = ResourceUsage(
                project_id=project_id,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                storage_mb=storage_mb,
                network_rx_mb=rx_mb,
                network_tx_mb=tx_mb,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)
            return usage

    @staticmethod
    def get_latest(project_id: int) -> Optional[ResourceUsage]:
        with get_db() as db:
            return db.query(ResourceUsage).filter(
                ResourceUsage.project_id == project_id
            ).order_by(ResourceUsage.id.desc()).first()

    @staticmethod
    def get_history(project_id: int, limit: int = 30) -> List[ResourceUsage]:
        with get_db() as db:
            return db.query(ResourceUsage).filter(
                ResourceUsage.project_id == project_id
            ).order_by(ResourceUsage.id.asc()).limit(limit).all()
