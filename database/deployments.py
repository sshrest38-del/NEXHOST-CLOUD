"""
NEXHOST CLOUD - Deployment Records and History
Author: @Harsh_54x
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from database.connection import Base, get_db

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=False)
    deployment_number = Column(Integer, default=1, nullable=False)
    status = Column(String(30), default="BUILDING", nullable=False)  # BUILDING, RUNNING, STOPPED, FAILED
    commit_or_version = Column(String(100), default="v1.0.0", nullable=True)
    logs = Column(Text, default="", nullable=True)
    exit_code = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    stopped_at = Column(DateTime, nullable=True)

class DeploymentRepository:
    @staticmethod
    def create(project_id: int, commit_or_version: str = "v1.0.0", initial_logs: str = "") -> Deployment:
        with get_db() as db:
            prev_count = db.query(Deployment).filter(Deployment.project_id == project_id).count()
            deployment = Deployment(
                project_id=project_id,
                deployment_number=prev_count + 1,
                status="BUILDING",
                commit_or_version=commit_or_version,
                logs=initial_logs,
                started_at=datetime.now(timezone.utc)
            )
            db.add(deployment)
            db.commit()
            db.refresh(deployment)
            return deployment

    @staticmethod
    def get_latest(project_id: int) -> Optional[Deployment]:
        with get_db() as db:
            return db.query(Deployment).filter(
                Deployment.project_id == project_id
            ).order_by(Deployment.id.desc()).first()

    @staticmethod
    def list_by_project(project_id: int, limit: int = 20) -> List[Deployment]:
        with get_db() as db:
            return db.query(Deployment).filter(
                Deployment.project_id == project_id
            ).order_by(Deployment.id.desc()).limit(limit).all()

    @staticmethod
    def update_status(deployment_id: int, status: str, exit_code: Optional[int] = None, logs: Optional[str] = None):
        with get_db() as db:
            dep = db.query(Deployment).filter(Deployment.id == deployment_id).first()
            if dep:
                dep.status = status.upper()
                if exit_code is not None:
                    dep.exit_code = exit_code
                if logs is not None:
                    dep.logs = logs
                if status.upper() in ["STOPPED", "FAILED"]:
                    dep.stopped_at = datetime.now(timezone.utc)
                db.commit()

    @staticmethod
    def append_log(deployment_id: int, log_line: str):
        with get_db() as db:
            dep = db.query(Deployment).filter(Deployment.id == deployment_id).first()
            if dep:
                current = dep.logs or ""
                dep.logs = (current + "\n" + log_line).strip()[-100000:]  # Keep last 100KB logs
                db.commit()
