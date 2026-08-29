from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db, make_engine
from app.main import app
from app.seed import sync_from_csv


@pytest.fixture
def db_session() -> Iterator[Session]:
    # Built straight from the ORM models, not via Alembic - tests only need the
    # current schema, not migration history.
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

    sync_from_csv(db_session, settings.seed_data_dir)
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
