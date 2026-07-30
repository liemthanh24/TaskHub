import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.database import engine, init_db
from app.routers import health, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.include_router(health.router)
app.include_router(tasks.router)
