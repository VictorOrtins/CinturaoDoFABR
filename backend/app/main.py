from contextlib import asynccontextmanager

from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alembic import command
from app.config import BACKEND_DIR, settings
from app.database import SessionLocal
from app.routers import assistant, cinturao, games, health, stats, teams
from app.seed import sync_from_csv


def run_migrations() -> None:
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    db = SessionLocal()
    try:
        sync_from_csv(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Cinturão do FABR API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(teams.router)
app.include_router(games.router)
app.include_router(cinturao.router)
app.include_router(stats.router)
app.include_router(assistant.router)
