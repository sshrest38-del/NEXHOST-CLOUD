"""
NEXHOST CLOUD - Worker Health and Resource Telemetry Monitor
Author: @Harsh_54x
"""

import time
import threading
from typing import Dict, Any, List, Optional
import psutil
from database.usage import UsageRepository
from database.projects import ProjectRepository
from workers.sandbox import SandboxProcessManager
from utils.logger import logger

class WorkerTelemetryMonitor:
    """
    Background telemetry collector for worker host and active bot processes.
    """
    _thread: Optional = None
    _running = False

    @classmethod
    def get_host_metrics(cls) -> Dict[str, Any]:
        """Collect host system overall hardware metrics."""
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(".")
        return {
            "host_cpu_percent": round(cpu, 1),
            "host_memory_used_mb": round(mem.used / (1024 * 1024), 1),
            "host_memory_total_mb": round(mem.total / (1024 * 1024), 1),
            "host_memory_percent": mem.percent,
            "host_disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "host_disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "host_disk_percent": disk.percent,
            "boot_time": psutil.boot_time(),
        }

    @classmethod
    def start_background_collector(cls, interval_seconds: int = 15):
        """Start thread to sample active bots and store usage."""
        if cls._running:
            return
        cls._running = True

        def _loop():
            while cls._running:
                try:
                    # Scan running sandbox instances
                    with SandboxProcessManager._lock:
                        instances = list(SandboxProcessManager._instances.items())
                    for project_id, mgr in instances:
                        if mgr.status == "RUNNING":
                            metrics = mgr.get_metrics()
                            UsageRepository.record(
                                project_id=project_id,
                                cpu_percent=metrics.get("cpu_percent", 0.0),
                                memory_mb=metrics.get("memory_mb", 0.0),
                                storage_mb=0.0
                            )
                except Exception as e:
                    logger.debug(f"Telemetry loop error: {e}")
                time.sleep(interval_seconds)

        cls._thread = threading.Thread(target=_loop, daemon=True)
        cls._thread.start()
        logger.info("Worker background telemetry monitor started.")
