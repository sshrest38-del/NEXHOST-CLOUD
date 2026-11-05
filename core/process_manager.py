"""
NEXHOST CLOUD - Bot Process Lifecycle and Worker Orchestrator
Author: @Harsh_54x
"""

from typing import Tuple, Dict, Any, Optional
from database.projects import ProjectRepository
from database.deployments import DeploymentRepository
from database.audit_logs import AuditLogRepository
from core.membership_engine import MembershipEngine
from workers.worker_client import worker_client
from workers.sandbox import SandboxProcessManager
from utils.logger import logger

class ProcessManager:
    @classmethod
    def start_bot(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """Verify quotas and launch bot on worker node."""
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return False, "Project not found or unauthorized access."

        can_start, reason = MembershipEngine.can_start_bot(user_id, project_id)
        if not can_start:
            return False, reason

        limits = MembershipEngine.get_user_limits(user_id)
        env_vars = ProjectRepository.get_env_vars(project_id)

        # Mark as deploying in DB
        ProjectRepository.update_status(project_id, "DEPLOYING")

        ok, msg, container_or_pid = worker_client.start_bot(
            project_id=project_id,
            user_id=user_id,
            startup_command=proj.startup_command,
            env_vars=env_vars,
            memory_mb=limits["max_ram_mb"],
            cpu_limit=limits["max_cpu_cores"],
            runtime_version=proj.runtime_version
        )

        if ok:
            ProjectRepository.update_status(project_id, "RUNNING", container_id=container_or_pid)
            # Create or update deployment entry
            dep = DeploymentRepository.create(project_id, commit_or_version="latest", initial_logs=msg)
            DeploymentRepository.update_status(dep.id, "RUNNING")
            AuditLogRepository.record(user_id, "BOT_STARTED", f"PROJECT_{project_id}", f"Bot '{proj.name}' started successfully.")
            return True, f"Bot '{proj.name}' is now running! ({msg})"
        else:
            ProjectRepository.update_status(project_id, "FAILED")
            return False, f"Failed to start bot: {msg}"

    @classmethod
    def stop_bot(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """Stop running bot process or container."""
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return False, "Project not found or unauthorized access."

        ok, msg = worker_client.stop_bot(project_id, user_id)
        ProjectRepository.update_status(project_id, "STOPPED")

        latest_dep = DeploymentRepository.get_latest(project_id)
        if latest_dep and latest_dep.status == "RUNNING":
            DeploymentRepository.update_status(latest_dep.id, "STOPPED", exit_code=0)

        AuditLogRepository.record(user_id, "BOT_STOPPED", f"PROJECT_{project_id}", f"Bot '{proj.name}' was stopped.")
        return True, f"Bot '{proj.name}' stopped."

    @classmethod
    def restart_bot(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """Restart bot and record restart count."""
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return False, "Project not found or unauthorized access."

        ProjectRepository.increment_restart_count(project_id)
        cls.stop_bot(user_id, project_id)
        return cls.start_bot(user_id, project_id)

    @classmethod
    def force_stop_bot(cls, user_id: int, project_id: int) -> Tuple[bool, str]:
        """Force termination of bot process."""
        return cls.stop_bot(user_id, project_id)

    @classmethod
    def get_live_status(cls, user_id: int, project_id: int) -> Dict[str, Any]:
        """Get telemetry and status."""
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return {"status": "STOPPED", "is_running": False}

        status = worker_client.get_status(project_id)
        
        # If DB thinks running but worker says stopped, sync status
        if proj.status == "RUNNING" and not status.get("is_running", False):
            ProjectRepository.update_status(project_id, "STOPPED")

        return status

    @classmethod
    def get_live_logs(cls, user_id: int, project_id: int, limit: int = 200) -> str:
        """Fetch logs stream."""
        return worker_client.get_logs(project_id, limit=limit)

    @classmethod
    def clear_logs(cls, user_id: int, project_id: int):
        """Clear local logs."""
        sandbox = SandboxProcessManager.get(project_id)
        if sandbox:
            sandbox.clear_logs()
