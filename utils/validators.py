"""
NEXHOST CLOUD - Input Validation and Security Sanity Checks
Author: @Harsh_54x
"""

import re
import os
import zipfile
from pathlib import Path
from typing import Tuple, List

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
# UPI UTR is typically a 12-digit numeric reference or alphanumeric bank ref of 8-30 chars
UPI_REF_REGEX = re.compile(r'^[a-zA-Z0-9]{8,35}$')

def validate_email(email: str) -> bool:
    """Validate format of an email address."""
    if not email or len(email) > 120:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_username(username: str) -> bool:
    """Validate username (letters, numbers, underscore, 3-30 chars)."""
    if not username:
        return False
    return bool(USERNAME_REGEX.match(username.strip()))

def validate_upi_reference(ref: str) -> bool:
    """Validate UPI Transaction ID / UTR format."""
    if not ref:
        return False
    clean = ref.strip()
    return bool(UPI_REF_REGEX.match(clean))

def safe_extract_zip(zip_source, destination_dir: Path) -> Tuple[bool, str, List[str]]:
    """
    Safely extract a ZIP archive while strictly preventing Zip-Slip directory traversal attacks.
    Ensures no file extracts outside the intended destination directory.
    
    Returns:
        (success: bool, message: str, extracted_files: List[str])
    """
    destination_dir = destination_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = []

    try:
        with zipfile.ZipFile(zip_source, 'r') as archive:
            for member in archive.infolist():
                # Check for malicious path components
                member_path = Path(member.filename)
                
                # Reject absolute paths or parent traversal components
                if member_path.is_absolute() or '..' in member_path.parts:
                    return False, f"Security violation: Archive contains forbidden path '{member.filename}'", []

                # Resolve target path and verify it starts with destination directory
                target_path = (destination_dir / member_path).resolve()
                if not str(target_path).startswith(str(destination_dir)):
                    return False, f"Security violation: Archive attempts to write outside destination '{member.filename}'", []

            # All members validated; safe to extract
            archive.extractall(destination_dir)
            extracted_files = [m.filename for m in archive.infolist() if not m.is_dir()]
            return True, f"Successfully extracted {len(extracted_files)} files.", extracted_files

    except zipfile.BadZipFile:
        return False, "Uploaded file is not a valid or readable ZIP archive.", []
    except Exception as e:
        return False, f"Error extracting archive: {str(e)}", []

def validate_startup_command(command: str) -> Tuple[bool, str]:
    """
    Validate Python bot startup command.
    Ensures command starts with python/python3 and blocks destructive commands.
    """
    if not command or not command.strip():
        return False, "Startup command cannot be empty."

    cmd = command.strip()
    forbidden_tokens = ['rm -rf /', ':(){ :|:& };:', 'mkfs', 'dd if=', 'chmod -R 777 /', '> /dev/sd']
    for token in forbidden_tokens:
        if token in cmd:
            return False, f"Dangerous command detected: '{token}' is prohibited."

    if not (cmd.startswith("python") or cmd.startswith("python3") or cmd.startswith("uvicorn") or cmd.startswith("bash")):
        return False, "Command must begin with a valid runtime invocation (e.g. 'python main.py' or 'python3 bot.py')."

    return True, "Valid command."
