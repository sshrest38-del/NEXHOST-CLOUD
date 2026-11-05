"""
NEXHOST CLOUD - Pytest Configuration and Test Fixtures
Author: @Harsh_54x
"""

import sys
import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import database.connection as db_conn
from database.connection import Base, init_db

@pytest.fixture(autouse=True)
def clean_test_database(monkeypatch):
    """
    Ensure each test function runs against a pristine, temporary SQLite database.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    test_db_url = f"sqlite:///{tmp_db_path}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    test_session = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=test_engine)

    monkeypatch.setattr(db_conn, "DATABASE_URL", test_db_url)
    monkeypatch.setattr(db_conn, "engine", test_engine)
    monkeypatch.setattr(db_conn, "SessionLocal", test_session)

    # Initialize tables, seed plans and owner
    init_db()

    yield

    # Teardown
    test_engine.dispose()
    try:
        os.remove(tmp_db_path)
    except Exception:
        pass
