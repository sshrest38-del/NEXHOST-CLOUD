"""
NEXHOST CLOUD - Deployment Orchestrator and Build Pipeline
Author: @Harsh_54x
"""

from typing import Tuple, Optional
from database.projects import ProjectRepository
from database.deployments import Deployment, DeploymentRepository
from core.process_manager import ProcessManager
from workers.worker_client import worker_client
from utils.logger import logger

class DeploymentEngine:
    @classmethod
    def deploy_project(cls, user_id: int, project_id: int, install_deps: bool = True) -> Tuple[bool, str, Optional[Deployment]]:
        """
        Execute full deployment pipeline:
        1. Create deployment build record.
        2. Optionally install requirements on worker.
        3. Launch bot on worker node.
        4. Capture logs and update status.
        """
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return False, "Project not found or unauthorized.", None

        # Create deployment record
        dep = DeploymentRepository.create(project_id, commit_or_version="latest", initial_logs="[NEXHOST] Starting deployment pipeline...")

        if install_deps:
            DeploymentRepository.append_log(dep.id, "[NEXHOST] Phase 1: Checking and installing project dependencies...")
            ok, msg = worker_client.install_requirements(project_id, user_id, proj.startup_command)
            DeploymentRepository.append_log(dep.id, f"[NEXHOST] Pip Output: {msg}")

        DeploymentRepository.append_log(dep.id, "[NEXHOST] Phase 2: Launching isolated runtime container/process...")
        ok, start_msg = ProcessManager.start_bot(user_id, project_id)
        DeploymentRepository.append_log(dep.id, f"[NEXHOST] {start_msg}")

        if ok:
            DeploymentRepository.update_status(dep.id, "RUNNING")
            return True, f"Deployment #{dep.deployment_number} succeeded!", dep
        else:
            DeploymentRepository.update_status(dep.id, "FAILED", exit_code=1)
            return False, f"Deployment failed: {start_msg}", dep
