"""
NEXHOST CLOUD - Runtime and Requirements Detection Engine
Author: @Harsh_54x
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from services.storage_service import StorageService

SUPPORTED_RUNTIMES = [
    {"id": "python:3.11", "label": "Python 3.11 (Recommended - Stable & Fast)"},
    {"id": "python:3.12", "label": "Python 3.12 (Latest Performance)"},
    {"id": "python:3.10", "label": "Python 3.10 (Legacy Compatibility)"},
]

ENTRYPOINT_CANDIDATES = [
    "bot.py",
    "main.py",
    "app.py",
    "run.py",
    "index.py",
    "start.py",
]

class RuntimeManager:
    @staticmethod
    def get_supported_runtimes() -> List[Dict[str, str]]:
        return SUPPORTED_RUNTIMES

    @classmethod
    def analyze_project_files(cls, user_id: int, project_id: int) -> Dict[str, Any]:
        """
        Scan unpacked project files to detect:
        1. presence of requirements.txt
        2. best guess for startup file and command
        3. list of python source files
        """
        base_dir = StorageService.get_project_dir(user_id, project_id)
        has_requirements = (base_dir / "requirements.txt").is_file()

        detected_entrypoint = None
        python_files = []

        if base_dir.exists():
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.endswith(".py"):
                        rel_path = os.path.relpath(os.path.join(root, f), base_dir).replace("\\", "/")
                        python_files.append(rel_path)

            # Prioritize standard names
            for candidate in ENTRYPOINT_CANDIDATES:
                if (base_dir / candidate).is_file():
                    detected_entrypoint = candidate
                    break

            if not detected_entrypoint and python_files:
                detected_entrypoint = python_files[0]

        suggested_command = f"python {detected_entrypoint}" if detected_entrypoint else "python bot.py"

        return {
            "has_requirements": has_requirements,
            "detected_entrypoint": detected_entrypoint,
            "suggested_command": suggested_command,
            "python_files": python_files,
            "file_count": len(python_files)
        }
