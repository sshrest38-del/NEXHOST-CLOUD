"""
NEXHOST CLOUD - Backup and Disaster Recovery Tests
Author: @Harsh_54x
"""

import sys
import io
import zipfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from auth.registration import register_user
from core.project_manager import ProjectManager
from services.storage_service import StorageService
from services.backup_service import BackupService

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_backup_and_restore_cycle():
    _, _, user = register_user("backup_tester@test.com", "backup_tester", "Pass123456")

    # Create project with initial file
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr("original.py", "# Original Code v1\nprint('Version 1')\n")
    buf.seek(0)

    ok, _, project = ProjectManager.create_project_from_zip(user.id, "Backup Demo Bot", buf)
    assert ok is True

    # 1. Create Backup
    ok_b, msg_b, backup_path = BackupService.create_backup(user.id, project.id, project.slug)
    assert ok_b is True
    assert backup_path is not None
    assert Path(backup_path).exists()

    # 2. Modify project file to simulate accidental deletion or change
    StorageService.write_file(user.id, project.id, "original.py", "# Corrupted or Modified Code\n")
    read_corrupted = StorageService.read_file(user.id, project.id, "original.py")
    assert "Corrupted" in read_corrupted

    # 3. Restore from Backup
    backup_filename = Path(backup_path).name
    ok_r, msg_r = BackupService.restore_backup(user.id, project.id, backup_filename)
    assert ok_r is True

    # 4. Verify original code restored!
    restored_code = StorageService.read_file(user.id, project.id, "original.py")
    assert "Original Code v1" in restored_code
