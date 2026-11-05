"""
NEXHOST CLOUD - Storage Service and Isolated Project Filesystem
Author: @Harsh_54x
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from config import STORAGE_BASE_DIR
from utils.logger import logger
from utils.validators import safe_extract_zip

class StorageService:
    @staticmethod
    def get_user_root(user_id: int) -> Path:
        """Get absolute path to user root storage directory."""
        path = (STORAGE_BASE_DIR / f"user_{user_id}").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_project_dir(user_id: int, project_id: int) -> Path:
        """Get absolute isolated path to specific project code root."""
        path = (STORAGE_BASE_DIR / f"user_{user_id}" / f"project_{project_id}" / "src").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_payments_dir() -> Path:
        """Directory for uploaded payment proof screenshots."""
        path = (STORAGE_BASE_DIR / "payments_proof").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _validate_safe_path(base_dir: Path, relative_path: str) -> Optional[Path]:
        """
        Verify relative path does not escape the project directory.
        Returns resolved Path if safe, or None if malicious.
        """
        try:
            # Clean leading slashes
            clean_rel = relative_path.lstrip("/\\")
            target = (base_dir / clean_rel).resolve()
            if not str(target).startswith(str(base_dir.resolve())):
                logger.warning(f"Storage path traversal attempt blocked: {relative_path}")
                return None
            return target
        except Exception:
            return None

    @classmethod
    def list_files(cls, user_id: int, project_id: int, subpath: str = "") -> List[Dict[str, Any]]:
        """List files and folders within a project subfolder."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target_dir = cls._validate_safe_path(base_dir, subpath)
        if not target_dir or not target_dir.exists() or not target_dir.is_dir():
            return []

        items = []
        for entry in os.scandir(target_dir):
            try:
                rel = os.path.relpath(entry.path, base_dir).replace("\\", "/")
                is_dir = entry.is_dir()
                size = 0 if is_dir else entry.stat().st_size
                mtime = entry.stat().st_mtime
                items.append({
                    "name": entry.name,
                    "relative_path": rel,
                    "is_dir": is_dir,
                    "size_bytes": size,
                    "modified_timestamp": mtime
                })
            except Exception:
                continue

        # Sort: directories first, then alphabetically
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

    @classmethod
    def read_file(cls, user_id: int, project_id: int, relative_path: str) -> Optional[str]:
        """Read text file safely."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target = cls._validate_safe_path(base_dir, relative_path)
        if not target or not target.exists() or not target.is_file():
            return None
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to read file {relative_path}: {e}")
            return None

    @classmethod
    def write_file(cls, user_id: int, project_id: int, relative_path: str, content: str) -> bool:
        """Write text file safely."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target = cls._validate_safe_path(base_dir, relative_path)
        if not target:
            return False
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {relative_path}: {e}")
            return False

    @classmethod
    def save_uploaded_binary(cls, user_id: int, project_id: int, relative_path: str, data: bytes) -> bool:
        """Save binary file data safely."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target = cls._validate_safe_path(base_dir, relative_path)
        if not target:
            return False
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            logger.error(f"Failed to save binary file {relative_path}: {e}")
            return False

    @classmethod
    def create_directory(cls, user_id: int, project_id: int, relative_path: str) -> bool:
        """Create directory safely."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target = cls._validate_safe_path(base_dir, relative_path)
        if not target:
            return False
        try:
            target.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {relative_path}: {e}")
            return False

    @classmethod
    def delete_item(cls, user_id: int, project_id: int, relative_path: str) -> bool:
        """Delete file or directory safely."""
        base_dir = cls.get_project_dir(user_id, project_id)
        target = cls._validate_safe_path(base_dir, relative_path)
        if not target or not target.exists() or target == base_dir:
            return False
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete item {relative_path}: {e}")
            return False

    @classmethod
    def extract_project_zip(cls, user_id: int, project_id: int, zip_file) -> Tuple[bool, str, List[str]]:
        """Extract uploaded ZIP safely into project directory."""
        target_dir = cls.get_project_dir(user_id, project_id)
        return safe_extract_zip(zip_file, target_dir)

    @classmethod
    def calculate_project_size(cls, user_id: int, project_id: int) -> int:
        """Calculate total size in bytes of a project."""
        base_dir = cls.get_project_dir(user_id, project_id)
        total_size = 0
        if not base_dir.exists():
            return 0
        for root, _, files in os.walk(base_dir):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
        return total_size

    @classmethod
    def calculate_user_total_storage(cls, user_id: int) -> int:
        """Calculate total storage in bytes across all projects for user."""
        user_root = cls.get_user_root(user_id)
        total_size = 0
        for root, _, files in os.walk(user_root):
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total_size

    @classmethod
    def delete_entire_project(cls, user_id: int, project_id: int) -> bool:
        """Remove all project files on disk."""
        base_dir = (STORAGE_BASE_DIR / f"user_{user_id}" / f"project_{project_id}").resolve()
        if base_dir.exists():
            try:
                shutil.rmtree(base_dir)
                return True
            except Exception as e:
                logger.error(f"Failed to remove project dir: {e}")
                return False
        return True
