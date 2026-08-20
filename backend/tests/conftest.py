from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB = Path(tempfile.gettempdir()) / f"oraculo-tests-{os.getpid()}.db"
TEST_ENV = Path(tempfile.gettempdir()) / f"oraculo-tests-{os.getpid()}.env.local"
TEST_DB.unlink(missing_ok=True)
os.environ["ORACULO_DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["ORACULO_ENV_FILE"] = str(TEST_ENV)
os.environ["OPENAI_API_KEY"] = ""
os.environ["ORACULO_SCHEDULER_ENABLED"] = "false"

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    yield
    from app.core.database import engine

    engine.dispose()
    TEST_DB.unlink(missing_ok=True)
