"""
NEXHOST CLOUD - Resource Manager and Telemetry Collector
Author: @Harsh_54x
"""

from typing import Dict, Any, Optional
from database.projects import ProjectRepository
from database.usage import UsageRepository
from services.storage_service import StorageService

class ResourceManager:
    @classmethod
    def get_project_metrics(cls, user_id: int, project_id: int) -> Dict[str, Any]:
        """
        Fetch the latest resource consumption metrics for a project.
        """
        proj = ProjectRepository.get_user_project(user_id, project_id)
        if not proj:
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "storage_mb": 0.0, "status": "STOPPED"}

        # Calculate current storage
        storage_bytes = StorageService.calculate_project_size(user_id, project_id)
        storage_mb = round(storage_bytes / (1024 * 1024), 2)

        # Get latest recorded telemetry from worker
        usage = UsageRepository.get_latest(project_id)
        cpu = usage.cpu_percent if usage else 0.0
        memory = usage.memory_mb if usage else 0.0

        return {
            "status": proj.status,
            "cpu_percent": round(cpu, 1),
            "memory_mb": round(memory, 1),
            "storage_mb": storage_mb,
            "restart_count": proj.restart_count,
            "auto_restart": proj.auto_restart
        }
