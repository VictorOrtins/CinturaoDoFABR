from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db, make_engine
from app.main import app
from app.seed import seed_if_empty


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = make_engine(":memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded_db_session(db_session: Session) -> Session:
    from app.config import settings

    seed_if_empty(db_session, settings.seed_data_dir)
    return db_session


@pytest.fixture
def client(seeded_db_session: Session) -> Iterator[TestClient]:
    """Note: deliberately not used as a context manager, so the app's real
    lifespan (which targets the on-disk DB) never runs; routes use the
    in-memory seeded_db_session via the get_db override instead."""

    def override_get_db() -> Iterator[Session]:
        yield seeded_db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
