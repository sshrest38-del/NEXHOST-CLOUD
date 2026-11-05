"""
NEXHOST CLOUD - Dedicated Worker REST API (FastAPI)
Author: @Harsh_54x
"""

from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from config import WORKER_API_KEY, WORKER_TYPE
from services.storage_service import StorageService
from workers.sandbox import SandboxProcessManager
from workers.docker_manager import DockerContainerManager
from workers.monitor import WorkerTelemetryMonitor

app = FastAPI(
    title="NEXHOST CLOUD Worker API",
    description="Isolated Execution Node API for NEXHOST CLOUD bots",
    version="1.0.0"
)

docker_mgr = DockerContainerManager()
WorkerTelemetryMonitor.start_background_collector()

def verify_worker_auth(x_worker_key: Optional[str] = Header(None)):
    """Enforce worker shared secret key."""
    if not x_worker_key or x_worker_key != WORKER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized worker key."
        )

class StartRequest(BaseModel):
    user_id: int
    startup_command: str = "python bot.py"
    runtime_version: str = "python:3.11"
    env_vars: Dict[str, str] = {}
    memory_mb: int = 512
    cpu_limit: float = 1.0

@app.get("/api/v1/health")
def health_check():
    """Worker node health and system status."""
    host_metrics = WorkerTelemetryMonitor.get_host_metrics()
    return {
        "status": "HEALTHY",
        "worker_type": WORKER_TYPE,
        "docker_available": docker_mgr.is_docker_ready(),
        "metrics": host_metrics
    }

@app.post("/api/v1/projects/{project_id}/start")
def start_bot(project_id: int, req: StartRequest, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    proj_dir = StorageService.get_project_dir(req.user_id, project_id)

    if WORKER_TYPE == "docker" and docker_mgr.is_docker_ready():
        ok, msg, cid = docker_mgr.start_container(
            project_id=project_id,
            user_id=req.user_id,
            project_dir=proj_dir,
            startup_cmd=req.startup_command,
            env_vars=req.env_vars,
            memory_mb=req.memory_mb,
            cpu_limit=req.cpu_limit
        )
        return {"success": ok, "message": msg, "container_id": cid}
    else:
        # Fallback to Sandbox Process Manager
        sandbox = SandboxProcessManager.get_or_create(
            project_id=project_id,
            user_id=req.user_id,
            project_dir=proj_dir,
            startup_command=req.startup_command,
            env_vars=req.env_vars,
            memory_limit_mb=req.memory_mb,
            cpu_limit=req.cpu_limit
        )
        ok, msg = sandbox.start()
        return {"success": ok, "message": msg, "pid": sandbox.process.pid if sandbox.process else None}

@app.post("/api/v1/projects/{project_id}/stop")
def stop_bot(project_id: int, user_id: int = 1, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    if WORKER_TYPE == "docker" and docker_mgr.is_docker_ready():
        ok, msg = docker_mgr.stop_container(project_id)
        return {"success": ok, "message": msg}
    else:
        sandbox = SandboxProcessManager.get(project_id)
        if sandbox:
            ok, msg = sandbox.stop()
            return {"success": ok, "message": msg}
        return {"success": True, "message": "Bot process was not running."}

@app.post("/api/v1/projects/{project_id}/restart")
def restart_bot(project_id: int, req: StartRequest, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    stop_bot(project_id, user_id=req.user_id, x_worker_key=x_worker_key)
    return start_bot(project_id, req, x_worker_key=x_worker_key)

@app.get("/api/v1/projects/{project_id}/status")
def get_status(project_id: int, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    if WORKER_TYPE == "docker" and docker_mgr.is_docker_ready():
        return docker_mgr.get_container_metrics(project_id)
    else:
        sandbox = SandboxProcessManager.get(project_id)
        if sandbox:
            return sandbox.get_metrics()
        return {"status": "STOPPED", "is_running": False, "cpu_percent": 0.0, "memory_mb": 0.0}

@app.get("/api/v1/projects/{project_id}/logs")
def get_logs(project_id: int, limit: int = 200, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    if WORKER_TYPE == "docker" and docker_mgr.is_docker_ready():
        return {"logs": docker_mgr.get_container_logs(project_id, tail=limit)}
    else:
        sandbox = SandboxProcessManager.get(project_id)
        return {"logs": sandbox.get_logs(limit) if sandbox else "No logs available. Bot is offline."}

@app.post("/api/v1/projects/{project_id}/install")
def install_requirements(project_id: int, req: StartRequest, x_worker_key: Optional[str] = Header(None)):
    verify_worker_auth(x_worker_key)
    proj_dir = StorageService.get_project_dir(req.user_id, project_id)
    sandbox = SandboxProcessManager.get_or_create(
        project_id=project_id,
        user_id=req.user_id,
        project_dir=proj_dir,
        startup_command=req.startup_command,
        env_vars=req.env_vars
    )
    ok, msg = sandbox.install_requirements()
    return {"success": ok, "message": msg}
