"""
NEXHOST CLOUD - Deployment, Worker Execution, and ZIP Security Tests
Author: @Harsh_54x
"""

import sys
import io
import zipfile
import time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db
from auth.registration import register_user
from core.project_manager import ProjectManager
from core.process_manager import ProcessManager
from utils.validators import safe_extract_zip
from utils.security import mask_sensitive_text

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_zip_path_traversal_attack_blocked():
    """Verify malicious ZIP with traversal paths (Zip Slip) is rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr("../../etc/passwd", "malicious_content")
        z.writestr("../malicious.py", "print('hacked')")
    buf.seek(0)

    target_dir = Path("data/storage/test_safety").resolve()
    ok, msg, files = safe_extract_zip(buf, target_dir)
    assert ok is False
    assert "Security violation" in msg

def test_zip_project_deployment_and_worker_execution():
    """Test full cycle: ZIP upload -> safe extraction -> start bot -> verify logs -> stop."""
    _, _, user = register_user("deploy_tester@test.com", "deploy_tester", "Pass123456")

    # Create valid dummy bot project ZIP in memory
    buf = io.BytesIO()
    bot_code = (
        "import time, os\n"
        "token = os.getenv('BOT_TOKEN', 'none')\n"
        "print('NEXHOST TEST BOT STARTED SUCCESSFULLY!')\n"
        "print(f'Active Bot Token: {token}')\n"
        "for i in range(5):\n"
        "    time.sleep(0.5)\n"
    )
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr("bot.py", bot_code)
        z.writestr("requirements.txt", "# standard library only\n")
    buf.seek(0)

    # Create project
    ok, msg, project = ProjectManager.create_project_from_zip(
        user_id=user.id,
        name="Automated Test Bot",
        zip_file=buf,
        startup_cmd="python bot.py"
    )
    assert ok is True
    assert project is not None
    assert project.name == "Automated Test Bot"

    # Start bot
    start_ok, start_msg = ProcessManager.start_bot(user.id, project.id)
    assert start_ok is True

    # Give process brief moment to output log
    time.sleep(1.2)

    # Check live logs
    logs = ProcessManager.get_live_logs(user.id, project.id)
    assert "NEXHOST TEST BOT STARTED SUCCESSFULLY!" in logs

    # Stop bot
    stop_ok, stop_msg = ProcessManager.stop_bot(user.id, project.id)
    assert stop_ok is True

def test_sensitive_secret_masking():
    """Ensure Telegram bot tokens and API keys are masked from logs."""
    fake_token = "1234567890:ABCdefGhIjkLmNoPqRsTuVwXyZ123456789"
    log_sample = f"Connecting to Telegram gateway with token {fake_token} on port 443"

    masked = mask_sensitive_text(log_sample, [fake_token])
    assert fake_token not in masked
    assert "[MASKED_TELEGRAM_BOT_TOKEN]" in masked or "********" in masked
