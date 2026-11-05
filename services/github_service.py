"""
NEXHOST CLOUD - GitHub Integration Service
Author: @Harsh_54x
"""

import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import requests
from utils.logger import logger
from utils.validators import safe_extract_zip

class GitHubService:
    @staticmethod
    def parse_repo_url(repo_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse 'owner/repo' or 'https://github.com/owner/repo' into (owner, repo)."""
        url = (repo_url or "").strip().rstrip("/")
        if not url:
            return None, None
        if "github.com/" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1].replace(".git", "")
                return owner, repo
        elif "/" in url and len(url.split("/")) == 2:
            owner, repo = url.split("/")
            return owner, repo
        return None, None

    @classmethod
    def test_repo_access(cls, repo_url: str, token: Optional[str] = None) -> Tuple[bool, str, Dict]:
        """Verify repository exists and can be accessed."""
        owner, repo = cls.parse_repo_url(repo_url)
        if not owner or not repo:
            return False, "Invalid GitHub repository URL or format. Use 'owner/repo' or full URL.", {}

        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token.strip()}"

        try:
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return True, "Repository reachable.", {
                    "full_name": data.get("full_name"),
                    "default_branch": data.get("default_branch", "main"),
                    "description": data.get("description", ""),
                    "stars": data.get("stargazers_count", 0),
                    "is_private": data.get("private", False)
                }
            elif resp.status_code == 404:
                return False, "Repository not found. If this is a private repo, provide a valid GitHub Personal Access Token.", {}
            elif resp.status_code == 401:
                return False, "Invalid GitHub token provided.", {}
            else:
                return False, f"GitHub API responded with HTTP {resp.status_code}", {}
        except Exception as e:
            return False, f"Network error connecting to GitHub: {str(e)}", {}

    @classmethod
    def clone_or_download_repo(cls, repo_url: str, target_dir: Path, branch: str = "main", token: Optional[str] = None) -> Tuple[bool, str]:
        """
        Download and unpack GitHub repo archive into target directory.
        Uses GitHub zipball API for maximum reliability across systems without requiring git CLI.
        """
        owner, repo = cls.parse_repo_url(repo_url)
        if not owner or not repo:
            return False, "Invalid repository format."

        zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token.strip()}"

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading GitHub archive from {owner}/{repo} (branch {branch})...")
            resp = requests.get(zip_url, headers=headers, stream=True, timeout=30)
            if resp.status_code != 200:
                return False, f"Failed to download repository zipball. HTTP status: {resp.status_code}"

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                for chunk in resp.iter_content(chunk_size=65536):
                    tmp_file.write(chunk)
                tmp_zip_path = Path(tmp_file.name)

            # Unpack into temporary extraction directory
            temp_extract_dir = Path(tempfile.mkdtemp())
            success, msg, files = safe_extract_zip(tmp_zip_path, temp_extract_dir)
            tmp_zip_path.unlink(missing_ok=True)

            if not success:
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                return False, f"Archive extraction failed: {msg}"

            # GitHub wraps contents in a root folder like 'owner-repo-sha/'
            subdirs = [p for p in temp_extract_dir.iterdir() if p.is_dir()]
            source_content_dir = subdirs[0] if subdirs else temp_extract_dir

            # Move all contents to target_dir
            for item in source_content_dir.iterdir():
                dest = target_dir / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(target_dir))

            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return True, f"Successfully imported repository {owner}/{repo} ({branch})."

        except Exception as e:
            logger.error(f"GitHub import failed: {e}")
            return False, f"GitHub import failed: {str(e)}"
