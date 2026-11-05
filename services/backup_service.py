"""
NEXHOST CLOUD - Project Backup and Snapshot Restore Service
Author: @Harsh_54x
"""

import os
import zipfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from config import BACKUP_BASE_DIR
from services.storage_service import StorageService
from utils.logger import logger
from utils.validators import safe_extract_zip

class BackupService:
    @staticmethod
    def get_backup_dir(user_id: int, project_id: int) -> Path:
        """Directory for storing project backups."""
        path = (BACKUP_BASE_DIR / f"user_{user_id}" / f"project_{project_id}").resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def create_backup(cls, user_id: int, project_id: int, project_slug: str, note: str = "") -> Tuple[bool, str, Optional[str]]:
        """
        Create a timestamped compressed ZIP backup of the project's source files.
        """
        source_dir = StorageService.get_project_dir(user_id, project_id)
        if not source_dir.exists():
            return False, "Project source directory does not exist.", None

        backup_dir = cls.get_backup_dir(user_id, project_id)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{project_slug}_{timestamp}.zip"
        target_zip = backup_dir / filename

        try:
            with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        full_path = Path(root) / file
                        arcname = full_path.relative_to(source_dir)
                        zip_out.write(full_path, arcname)

            file_size = target_zip.stat().st_size
            logger.info(f"Backup created: {filename} ({file_size} bytes)")
            return True, f"Backup created successfully ({filename})", str(target_zip)
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, f"Failed to create backup: {str(e)}", None

    @classmethod
    def list_backups(cls, user_id: int, project_id: int) -> List[Dict[str, Any]]:
        """List all backups for a project."""
        backup_dir = cls.get_backup_dir(user_id, project_id)
        if not backup_dir.exists():
            return []

        backups = []
        for file in backup_dir.glob("*.zip"):
            stat = file.stat()
            backups.append({
                "filename": file.name,
                "path": str(file),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            })

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    @classmethod
    def restore_backup(cls, user_id: int, project_id: int, backup_filename: str) -> Tuple[bool, str]:
        """
        Restore project code from a specific backup archive.
        Overwrites current project code safely.
        """
        backup_dir = cls.get_backup_dir(user_id, project_id)
        backup_path = (backup_dir / backup_filename).resolve()
        if not backup_path.exists() or not str(backup_path).startswith(str(backup_dir)):
            return False, "Selected backup file does not exist."

        target_dir = StorageService.get_project_dir(user_id, project_id)

        try:
            # Clean existing source directory safely
            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Safe extraction
            success, msg, files = safe_extract_zip(backup_path, target_dir)
            if not success:
                return False, f"Failed to restore backup: {msg}"

            logger.info(f"Restored project {project_id} from {backup_filename} ({len(files)} files)")
            return True, f"Successfully restored project from {backup_filename}!"
        except Exception as e:
            logger.error(f"Restore error: {e}")
            return False, f"Error restoring backup: {str(e)}"
