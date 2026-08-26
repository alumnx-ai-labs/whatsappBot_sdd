import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import session as db_session
from app.db.models import Base


@pytest.fixture()
def test_db_engine() -> Generator:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    os.remove(path)


@pytest.fixture()
def client(test_db_engine, monkeypatch) -> Generator[TestClient, None, None]:
    test_session_local = sessionmaker(bind=test_db_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_session, "SessionLocal", test_session_local)

    from app.main import create_app

    app = create_app()

    def _override_get_db() -> Generator:
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session.get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
