"""
NEXHOST CLOUD - Worker API Client and Controller Bridge
Author: @Harsh_54x
"""

from typing import Dict, Any, Optional, Tuple
import requests
from config import WORKER_URL, WORKER_API_KEY, WORKER_TYPE
from services.storage_service import StorageService
from workers.sandbox import SandboxProcessManager
from workers.docker_manager import DockerContainerManager
from utils.logger import logger

class WorkerClient:
    """
    Connects NEXHOST CLOUD control plane with the isolated worker nodes.
    Supports remote HTTP API dispatch as well as automatic embedded local worker fallback.
    """
    def __init__(self, base_url: str = WORKER_URL, api_key: str = WORKER_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Worker-Key": self.api_key}
        self.docker_mgr = DockerContainerManager()

    def _is_remote_worker_active(self) -> bool:
        """Check if remote worker daemon responds."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/health", headers=self.headers, timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def start_bot(self, project_id: int, user_id: int, startup_command: str,
                  env_vars: Dict[str, str], memory_mb: int = 512, cpu_limit: float = 1.0,
                  runtime_version: str = "python:3.11") -> Tuple[bool, str, Optional[str]]:
        """Dispatch bot startup to worker."""
        if self._is_remote_worker_active():
            try:
                payload = {
                    "user_id": user_id,
                    "startup_command": startup_command,
                    "runtime_version": runtime_version,
                    "env_vars": env_vars,
                    "memory_mb": memory_mb,
                    "cpu_limit": cpu_limit
                }
                resp = requests.post(
                    f"{self.base_url}/api/v1/projects/{project_id}/start",
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                data = resp.json()
                return data.get("success", False), data.get("message", ""), data.get("container_id")
            except Exception as e:
                logger.warning(f"Remote worker call failed, falling back to embedded worker: {e}")

        # Embedded Worker Fallback
        proj_dir = StorageService.get_project_dir(user_id, project_id)
        if WORKER_TYPE == "docker" and self.docker_mgr.is_docker_ready():
            return self.docker_mgr.start_container(
                project_id=project_id,
                user_id=user_id,
                project_dir=proj_dir,
                startup_cmd=startup_command,
                env_vars=env_vars,
                memory_mb=memory_mb,
                cpu_limit=cpu_limit
            )
        else:
            sandbox = SandboxProcessManager.get_or_create(
                project_id=project_id,
                user_id=user_id,
                project_dir=proj_dir,
                startup_command=startup_command,
                env_vars=env_vars,
                memory_limit_mb=memory_mb,
                cpu_limit=cpu_limit
            )
            ok, msg = sandbox.start()
            pid_str = str(sandbox.process.pid) if sandbox.process else None
            return ok, msg, pid_str

    def stop_bot(self, project_id: int, user_id: int = 1) -> Tuple[bool, str]:
        """Dispatch stop command to worker."""
        if self._is_remote_worker_active():
            try:
                resp = requests.post(
                    f"{self.base_url}/api/v1/projects/{project_id}/stop",
                    params={"user_id": user_id},
                    headers=self.headers,
                    timeout=8
                )
                data = resp.json()
                return data.get("success", False), data.get("message", "")
            except Exception as e:
                logger.warning(f"Remote worker stop failed: {e}")

        # Embedded Worker Fallback
        if WORKER_TYPE == "docker" and self.docker_mgr.is_docker_ready():
            return self.docker_mgr.stop_container(project_id)
        else:
            sandbox = SandboxProcessManager.get(project_id)
            if sandbox:
                return sandbox.stop()
            return True, "Bot process was already stopped."

    def restart_bot(self, project_id: int, user_id: int, startup_command: str,
                    env_vars: Dict[str, str], memory_mb: int = 512, cpu_limit: float = 1.0,
                    runtime_version: str = "python:3.11") -> Tuple[bool, str, Optional[str]]:
        self.stop_bot(project_id, user_id)
        return self.start_bot(project_id, user_id, startup_command, env_vars, memory_mb, cpu_limit, runtime_version)

    def get_status(self, project_id: int) -> Dict[str, Any]:
        """Get live metrics and running status from worker."""
        if self._is_remote_worker_active():
            try:
                resp = requests.get(
                    f"{self.base_url}/api/v1/projects/{project_id}/status",
                    headers=self.headers,
                    timeout=3
                )
                return resp.json()
            except Exception:
                pass

        # Embedded Worker Fallback
        if WORKER_TYPE == "docker" and self.docker_mgr.is_docker_ready():
            return self.docker_mgr.get_container_metrics(project_id)
        else:
            sandbox = SandboxProcessManager.get(project_id)
            if sandbox:
                return sandbox.get_metrics()
            return {"status": "STOPPED", "is_running": False, "cpu_percent": 0.0, "memory_mb": 0.0}

    def get_logs(self, project_id: int, limit: int = 200) -> str:
        """Fetch live logs stream from worker."""
        if self._is_remote_worker_active():
            try:
                resp = requests.get(
                    f"{self.base_url}/api/v1/projects/{project_id}/logs",
                    params={"limit": limit},
                    headers=self.headers,
                    timeout=5
                )
                return resp.json().get("logs", "")
            except Exception:
                pass

        # Embedded Worker Fallback
        if WORKER_TYPE == "docker" and self.docker_mgr.is_docker_ready():
            return self.docker_mgr.get_container_logs(project_id, tail=limit)
        else:
            sandbox = SandboxProcessManager.get(project_id)
            return sandbox.get_logs(limit) if sandbox else "Bot is currently offline. No active logs."

    def install_requirements(self, project_id: int, user_id: int, startup_command: str = "python bot.py") -> Tuple[bool, str]:
        """Trigger dependency installation inside project directory."""
        if self._is_remote_worker_active():
            try:
                payload = {
                    "user_id": user_id,
                    "startup_command": startup_command,
                    "runtime_version": "python:3.11",
                    "env_vars": {}
                }
                resp = requests.post(
                    f"{self.base_url}/api/v1/projects/{project_id}/install",
                    json=payload,
                    headers=self.headers,
                    timeout=180
                )
                data = resp.json()
                return data.get("success", False), data.get("message", "")
            except Exception as e:
                logger.warning(f"Remote install call failed: {e}")

        # Embedded Worker Fallback
        proj_dir = StorageService.get_project_dir(user_id, project_id)
        sandbox = SandboxProcessManager.get_or_create(
            project_id=project_id,
            user_id=user_id,
            project_dir=proj_dir,
            startup_command=startup_command,
            env_vars={}
        )
        return sandbox.install_requirements()

worker_client = WorkerClient()
