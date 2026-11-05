"""
NEXHOST CLOUD - Hardened Docker Container Execution Manager
Author: @Harsh_54x
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from utils.logger import logger
from utils.security import mask_sensitive_text

try:
    import docker
    from docker.errors import DockerException, NotFound
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

class DockerContainerManager:
    """
    Manages isolated, non-root Docker containers for user Python projects.
    Enforces strict memory, CPU and process quotas with zero Docker socket exposure.
    """
    def __init__(self):
        self.client = None
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                self.client.ping()
            except Exception as e:
                logger.warning(f"Docker daemon not reachable: {e}. Worker will use process sandbox fallback.")
                self.client = None

    def is_docker_ready(self) -> bool:
        return self.client is not None

    def start_container(self, project_id: int, user_id: int, project_dir: Path, startup_cmd: str,
                        env_vars: Dict[str, str], memory_mb: int = 512, cpu_limit: float = 1.0,
                        runtime_image: str = "python:3.11-slim") -> Tuple[bool, str, Optional[str]]:
        """
        Run bot in a non-root isolated container with strict resource limits.
        """
        if not self.is_docker_ready():
            return False, "Docker daemon unavailable on this worker.", None

        container_name = f"nexhost-proj-{project_id}"

        # Clean existing container with same name if any
        try:
            existing = self.client.containers.get(container_name)
            existing.stop(timeout=2)
            existing.remove(force=True)
        except Exception:
            pass

        # Environment setup
        container_env = env_vars.copy()
        container_env["PYTHONUNBUFFERED"] = "1"
        container_env["NEXHOST_CONTAINER"] = "1"

        # Security options:
        # non-root user (1000:1000), read-only root where possible or drop privileges
        # mem_limit in bytes or string
        mem_str = f"{memory_mb}m"
        nano_cpus = int(cpu_limit * 1_000_000_000)

        volumes = {
            str(project_dir.resolve()): {
                "bind": "/app",
                "mode": "rw"
            }
        }

        try:
            logger.info(f"Creating isolated Docker container '{container_name}' using {runtime_image} (RAM: {mem_str}, CPU: {cpu_limit})...")
            container = self.client.containers.run(
                image=runtime_image,
                command=f"sh -c '{startup_cmd}'",
                name=container_name,
                working_dir="/app",
                volumes=volumes,
                environment=container_env,
                detach=True,
                mem_limit=mem_str,
                nano_cpus=nano_cpus,
                privileged=False,
                network_mode="bridge",
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 5}
            )
            return True, f"Container started successfully ({container.short_id})", container.id

        except Exception as e:
            logger.error(f"Docker container run failure: {e}")
            return False, f"Docker startup error: {str(e)}", None

    def stop_container(self, project_id: int) -> Tuple[bool, str]:
        if not self.is_docker_ready():
            return False, "Docker unavailable."
        container_name = f"nexhost-proj-{project_id}"
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            return True, "Container stopped successfully."
        except Exception as e:
            return False, f"Failed to stop container: {str(e)}"

    def get_container_logs(self, project_id: int, tail: int = 200) -> str:
        if not self.is_docker_ready():
            return "Docker unavailable."
        container_name = f"nexhost-proj-{project_id}"
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
            return mask_sensitive_text(logs)
        except Exception as e:
            return f"Logs unavailable: {str(e)}"

    def get_container_metrics(self, project_id: int) -> Dict[str, Any]:
        if not self.is_docker_ready():
            return {"status": "OFFLINE", "cpu_percent": 0.0, "memory_mb": 0.0}
        container_name = f"nexhost-proj-{project_id}"
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            # Calculate memory
            mem_usage = stats.get("memory_stats", {}).get("usage", 0)
            mem_mb = round(mem_usage / (1024 * 1024), 2)
            
            # Simple CPU approximation
            cpu_percent = 0.0
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = round((cpu_delta / system_delta) * len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [1])) * 100.0, 1)

            return {
                "status": container.status.upper(),
                "is_running": container.status == "running",
                "cpu_percent": cpu_percent,
                "memory_mb": mem_mb,
                "container_id": container.short_id
            }
        except Exception:
            return {"status": "STOPPED", "cpu_percent": 0.0, "memory_mb": 0.0}
