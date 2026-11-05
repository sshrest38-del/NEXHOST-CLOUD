"""
NEXHOST CLOUD - Isolated Process Sandbox Execution Engine
Author: @Harsh_54x
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import psutil
from utils.logger import logger
from utils.security import mask_sensitive_text

class SandboxProcessManager:
    """
    Manages isolated background processes for bot deployments.
    Tracks PID, streams logs, enforces timeouts and gathers real-time resource telemetry.
    """
    _instances: Dict[int, "SandboxProcessManager"] = {}
    _lock = threading.Lock()

    def __init__(self, project_id: int, user_id: int, project_dir: Path, startup_command: str,
                 env_vars: Dict[str, str], memory_limit_mb: int = 512, cpu_limit: float = 1.0):
        self.project_id = project_id
        self.user_id = user_id
        self.project_dir = project_dir.resolve()
        self.startup_command = startup_command
        self.env_vars = env_vars
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit = cpu_limit

        self.process: Optional[subprocess.Popen] = None
        self.log_buffer: List[str] = []
        self.max_log_lines = 1000
        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        self.exit_code: Optional[int] = None
        self.status = "STOPPED"  # STOPPED, RUNNING, FAILED
        self._reader_thread: Optional[threading.Thread] = None

    @classmethod
    def get_or_create(cls, project_id: int, user_id: int, project_dir: Path, startup_command: str,
                      env_vars: Dict[str, str], memory_limit_mb: int = 512, cpu_limit: float = 1.0) -> "SandboxProcessManager":
        with cls._lock:
            if project_id not in cls._instances:
                cls._instances[project_id] = cls(
                    project_id=project_id,
                    user_id=user_id,
                    project_dir=project_dir,
                    startup_command=startup_command,
                    env_vars=env_vars,
                    memory_limit_mb=memory_limit_mb,
                    cpu_limit=cpu_limit
                )
            else:
                inst = cls._instances[project_id]
                inst.startup_command = startup_command
                inst.env_vars = env_vars
                inst.memory_limit_mb = memory_limit_mb
                inst.cpu_limit = cpu_limit
            return cls._instances[project_id]

    @classmethod
    def get(cls, project_id: int) -> Optional["SandboxProcessManager"]:
        with cls._lock:
            return cls._instances.get(project_id)

    def _append_log(self, raw_line: str):
        masked_line = mask_sensitive_text(raw_line.strip(), list(self.env_vars.values()))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {masked_line}"
        self.log_buffer.append(formatted)
        if len(self.log_buffer) > self.max_log_lines:
            self.log_buffer.pop(0)

    def _stream_output(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self._append_log(line)
                elif self.process.poll() is not None:
                    break
        except Exception as e:
            self._append_log(f"[NEXHOST] Log streaming closed: {str(e)}")
        finally:
            if self.process:
                self.process.poll()
                self.exit_code = self.process.returncode
                self.stopped_at = time.time()
                self.status = "STOPPED" if self.exit_code == 0 else "FAILED"
                self._append_log(f"[NEXHOST] Bot process exited with code {self.exit_code}")

    def start(self) -> Tuple[bool, str]:
        """Launch bot process in isolated environment."""
        if self.process and self.process.poll() is None:
            return False, "Bot is already running."

        if not self.project_dir.exists():
            return False, "Project directory does not exist on disk."

        # Prepare isolated execution environment
        custom_env = os.environ.copy()
        custom_env.update(self.env_vars)
        custom_env["PYTHONUNBUFFERED"] = "1"
        custom_env["NEXHOST_PROJECT_ID"] = str(self.project_id)
        custom_env["NEXHOST_USER_ID"] = str(self.user_id)

        try:
            self._append_log(f"[NEXHOST] Starting bot with command: '{self.startup_command}'")
            self.process = subprocess.Popen(
                self.startup_command,
                shell=True,
                cwd=str(self.project_dir),
                env=custom_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.started_at = time.time()
            self.stopped_at = None
            self.exit_code = None
            self.status = "RUNNING"

            # Background thread to capture logs
            self._reader_thread = threading.Thread(target=self._stream_output, daemon=True)
            self._reader_thread.start()

            logger.info(f"Launched project {self.project_id} (PID: {self.process.pid})")
            return True, f"Bot started successfully (PID: {self.process.pid})"

        except Exception as e:
            self.status = "FAILED"
            self._append_log(f"[NEXHOST] Startup failure: {str(e)}")
            logger.error(f"Failed to start project {self.project_id}: {e}")
            return False, f"Failed to start bot: {str(e)}"

    def stop(self, timeout_sec: int = 5) -> Tuple[bool, str]:
        """Gracefully stop bot process with SIGTERM followed by SIGKILL if needed."""
        if not self.process or self.process.poll() is not None:
            self.status = "STOPPED"
            return True, "Bot is already stopped."

        try:
            self._append_log("[NEXHOST] Sending SIGTERM to process...")
            # Try terminating child processes first
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
            except Exception:
                pass

            self.process.terminate()
            try:
                self.process.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                self._append_log("[NEXHOST] Process did not terminate within timeout; forcing SIGKILL...")
                try:
                    parent = psutil.Process(self.process.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                except Exception:
                    pass
                self.process.kill()

            self.stopped_at = time.time()
            self.status = "STOPPED"
            self._append_log("[NEXHOST] Bot process stopped successfully.")
            return True, "Bot stopped successfully."
        except Exception as e:
            logger.error(f"Error stopping process {self.project_id}: {e}")
            return False, f"Error stopping bot: {str(e)}"

    def restart(self) -> Tuple[bool, str]:
        """Restart the bot process."""
        self.stop()
        time.sleep(1)
        return self.start()

    def install_requirements(self) -> Tuple[bool, str]:
        """Run pip install -r requirements.txt inside project directory."""
        req_file = self.project_dir / "requirements.txt"
        if not req_file.exists():
            return False, "requirements.txt not found in project root."

        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        self._append_log("[NEXHOST] Installing dependencies: pip install -r requirements.txt...")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=180
            )
            for line in result.stdout.splitlines():
                if line:
                    self._append_log(line)
            if result.returncode == 0:
                self._append_log("[NEXHOST] Dependencies installed successfully!")
                return True, "Requirements installed successfully!"
            else:
                self._append_log(f"[NEXHOST] Pip installation error:\n{result.stderr}")
                return False, f"Pip installation failed with exit code {result.returncode}"
        except subprocess.TimeoutExpired:
            self._append_log("[NEXHOST] Error: Pip install timed out after 180 seconds.")
            return False, "Pip installation timed out."
        except Exception as e:
            self._append_log(f"[NEXHOST] Pip error: {str(e)}")
            return False, f"Error installing requirements: {str(e)}"

    def get_metrics(self) -> Dict[str, Any]:
        """Collect live CPU and RAM consumption via psutil."""
        if not self.process or self.process.poll() is not None:
            return {
                "status": self.status,
                "is_running": False,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "uptime_seconds": 0,
                "exit_code": self.exit_code,
                "pid": None
            }

        try:
            p = psutil.Process(self.process.pid)
            cpu = p.cpu_percent(interval=0.1)
            mem_info = p.memory_info()
            mem_mb = round(mem_info.rss / (1024 * 1024), 2)
            uptime = int(time.time() - self.started_at) if self.started_at else 0

            return {
                "status": "RUNNING",
                "is_running": True,
                "cpu_percent": round(cpu, 1),
                "memory_mb": mem_mb,
                "uptime_seconds": uptime,
                "exit_code": None,
                "pid": self.process.pid
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "status": "STOPPED",
                "is_running": False,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "uptime_seconds": 0,
                "exit_code": self.process.poll(),
                "pid": None
            }

    def get_logs(self, limit: int = 200) -> str:
        """Return the recent in-memory log lines."""
        return "\n".join(self.log_buffer[-limit:])

    def clear_logs(self):
        """Clear log buffer."""
        self.log_buffer.clear()
        self._append_log("[NEXHOST] Console log buffer cleared by user.")
