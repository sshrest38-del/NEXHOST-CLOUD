"""
NEXHOST CLOUD - Project Entity Model and Repository
Author: @Harsh_54x
"""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy import Column, Integer, ForeignKey, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base, get_db

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), index=True, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(30), default="ZIP", nullable=False)  # ZIP, GITHUB
    github_repo_url = Column(String(255), nullable=True)
    github_branch = Column(String(60), default="main", nullable=True)
    runtime_version = Column(String(30), default="python:3.11", nullable=False)
    startup_command = Column(String(255), default="python bot.py", nullable=False)
    status = Column(String(30), default="STOPPED", nullable=False)  # STOPPED, RUNNING, FAILED, DEPLOYING
    env_vars_json = Column(Text, default="{}", nullable=False)
    auto_restart = Column(Boolean, default=True, nullable=False)
    restart_count = Column(Integer, default=0, nullable=False)
    container_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", lazy="joined")

class ProjectRepository:
    @staticmethod
    def get_by_id(project_id: int) -> Optional[Project]:
        with get_db() as db:
            return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_user_project(user_id: int, project_id: int) -> Optional[Project]:
        """Fetch project ensuring user-level isolation."""
        with get_db() as db:
            return db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id
            ).first()

    @staticmethod
    def list_by_user(user_id: int, search: str = "", status: str = "") -> List[Project]:
        with get_db() as db:
            query = db.query(Project).filter(Project.user_id == user_id)
            if search:
                s = f"%{search.lower()}%"
                query = query.filter(Project.name.ilike(s) | Project.slug.ilike(s))
            if status and status.upper() != "ALL":
                query = query.filter(Project.status == status.upper())
            return query.order_by(Project.id.desc()).all()

    @staticmethod
    def count_by_user(user_id: int) -> int:
        with get_db() as db:
            return db.query(Project).filter(Project.user_id == user_id).count()

    @staticmethod
    def count_running_by_user(user_id: int) -> int:
        with get_db() as db:
            return db.query(Project).filter(
                Project.user_id == user_id,
                Project.status == "RUNNING"
            ).count()

    @staticmethod
    def list_all() -> List[Project]:
        with get_db() as db:
            return db.query(Project).order_by(Project.id.desc()).all()

    @staticmethod
    def create(user_id: int, name: str, source_type: str = "ZIP", startup_command: str = "python bot.py",
               runtime_version: str = "python:3.11", description: str = "", github_repo_url: str = None,
               github_branch: str = "main", env_vars: Optional[Dict[str, str]] = None) -> Project:
        with get_db() as db:
            slug = name.lower().replace(" ", "-").replace("_", "-")
            env_str = json.dumps(env_vars or {})
            project = Project(
                user_id=user_id,
                name=name.strip(),
                slug=f"{slug}-{int(datetime.now(timezone.utc).timestamp())}",
                description=description.strip(),
                source_type=source_type,
                github_repo_url=github_repo_url,
                github_branch=github_branch,
                runtime_version=runtime_version,
                startup_command=startup_command,
                status="STOPPED",
                env_vars_json=env_str,
                created_at=datetime.now(timezone.utc)
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            return project

    @staticmethod
    def update_status(project_id: int, status: str, container_id: Optional[str] = None) -> bool:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.status = status.upper()
                if container_id is not None:
                    proj.container_id = container_id
                proj.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def increment_restart_count(project_id: int) -> int:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.restart_count += 1
                db.commit()
                return proj.restart_count
            return 0

    @staticmethod
    def update_env_vars(project_id: int, env_vars: Dict[str, str]) -> bool:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.env_vars_json = json.dumps(env_vars)
                proj.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def get_env_vars(project_id: int) -> Dict[str, str]:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj and proj.env_vars_json:
                try:
                    return json.loads(proj.env_vars_json)
                except Exception:
                    return {}
            return {}

    @staticmethod
    def update_settings(project_id: int, name: str, startup_command: str, runtime_version: str, auto_restart: bool) -> bool:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.name = name.strip()
                proj.startup_command = startup_command.strip()
                proj.runtime_version = runtime_version.strip()
                proj.auto_restart = auto_restart
                proj.updated_at = datetime.now(timezone.utc)
                db.commit()
                return True
            return False

    @staticmethod
    def delete(project_id: int) -> bool:
        with get_db() as db:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                db.delete(proj)
                db.commit()
                return True
            return False
