"""
NEXHOST CLOUD - Project Management Engine
Author: @Harsh_54x
"""

from typing import Tuple, Optional, Dict, Any, List
from database.projects import Project, ProjectRepository
from database.audit_logs import AuditLogRepository
from services.storage_service import StorageService
from services.github_service import GitHubService
from core.membership_engine import MembershipEngine
from core.runtime_manager import RuntimeManager
from utils.validators import validate_startup_command
from utils.logger import logger

class ProjectManager:
    @classmethod
    def create_project_from_zip(cls, user_id: int, name: str, zip_file, startup_cmd: Optional[str] = None,
                                runtime_version: str = "python:3.11", description: str = "") -> Tuple[bool, str, Optional[Project]]:
        """
        Create a new bot project from an uploaded ZIP file.
        Strictly enforces user membership bot quota and safe extraction.
        """
        can_create, reason = MembershipEngine.can_create_bot(user_id)
        if not can_create:
            return False, reason, None

        if not name or len(name.strip()) < 2:
            return False, "Project name must be at least 2 characters long.", None

        # Create project in DB
        project = ProjectRepository.create(
            user_id=user_id,
            name=name.strip(),
            source_type="ZIP",
            startup_command=startup_cmd.strip() if startup_cmd else "python bot.py",
            runtime_version=runtime_version,
            description=description
        )

        # Unpack archive into isolated project storage
        ok, msg, extracted_files = StorageService.extract_project_zip(user_id, project.id, zip_file)
        if not ok:
            # Rollback project on failure
            ProjectRepository.delete(project.id)
            return False, f"ZIP extraction failed: {msg}", None

        # Auto-detect entrypoint if startup_cmd wasn't explicitly supplied
        analysis = RuntimeManager.analyze_project_files(user_id, project.id)
        if not startup_cmd and analysis["detected_entrypoint"]:
            ProjectRepository.update_settings(
                project_id=project.id,
                name=project.name,
                startup_command=analysis["suggested_command"],
                runtime_version=runtime_version,
                auto_restart=project.auto_restart
            )

        AuditLogRepository.record(user_id, "PROJECT_CREATED_ZIP", f"PROJECT_{project.id}", f"Project '{project.name}' created with {len(extracted_files)} files.")
        return True, f"Project '{project.name}' created successfully with {len(extracted_files)} files!", project

    @classmethod
    def create_project_from_github(cls, user_id: int, name: str, repo_url: str, branch: str = "main",
                                   token: Optional[str] = None, startup_cmd: Optional[str] = None,
                                   runtime_version: str = "python:3.11", description: str = "") -> Tuple[bool, str, Optional[Project]]:
        """
        Create a new bot project by importing from a public or private GitHub repository.
        """
        can_create, reason = MembershipEngine.can_create_bot(user_id)
        if not can_create:
            return False, reason, None

        if not name or len(name.strip()) < 2:
            return False, "Project name must be at least 2 characters long.", None

        project = ProjectRepository.create(
            user_id=user_id,
            name=name.strip(),
            source_type="GITHUB",
            github_repo_url=repo_url.strip(),
            github_branch=branch.strip() or "main",
            startup_command=startup_cmd.strip() if startup_cmd else "python bot.py",
            runtime_version=runtime_version,
            description=description
        )

        target_dir = StorageService.get_project_dir(user_id, project.id)
        ok, msg = GitHubService.clone_or_download_repo(repo_url, target_dir, branch, token)
        if not ok:
            ProjectRepository.delete(project.id)
            return False, f"GitHub import failed: {msg}", None

        # Auto-detect entrypoint if needed
        analysis = RuntimeManager.analyze_project_files(user_id, project.id)
        if not startup_cmd and analysis["detected_entrypoint"]:
            ProjectRepository.update_settings(
                project_id=project.id,
                name=project.name,
                startup_command=analysis["suggested_command"],
                runtime_version=runtime_version,
                auto_restart=project.auto_restart
            )

        AuditLogRepository.record(user_id, "PROJECT_CREATED_GITHUB", f"PROJECT_{project.id}", f"Project '{project.name}' cloned from {repo_url} ({branch}).")
        return True, f"Project '{project.name}' imported from GitHub successfully!", project

    @classmethod
    def delete_project(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """
        Safely delete a bot project:
        1. Ensures user ownership.
        2. Cleans up project filesystem.
        3. Removes database records.
        """
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return False, "Project not found or unauthorized."

        # Delete physical files
        StorageService.delete_entire_project(user_id, project_id)

        # Delete DB record
        ProjectRepository.delete(project_id)
        AuditLogRepository.record(user_id, "PROJECT_DELETED", f"PROJECT_{project_id}", f"Project '{proj.name}' was permanently deleted.")
        return True, f"Project '{proj.name}' was deleted successfully."
