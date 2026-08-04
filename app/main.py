import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine, init_db
from app.repositories.user import UserRepository
from app.routers import auth, health, tasks

logger = logging.getLogger(__name__)


def _guard_settings():
    if not settings.DEBUG and settings.JWT_SECRET == "change-me-in-production":
        raise RuntimeError(
            "JWT_SECRET must be set in production (DEBUG=False). "
            "Do not run with the default secret."
        )


async def seed_admin():
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        if not await repo.get_by_email(settings.ADMIN_EMAIL):
            await repo.create(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
            )
            logger.info("Seeded admin user %s", settings.ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    await init_db()
    await seed_admin()
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

_guard_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(auth.router)
app.include_router(health.router)
app.include_router(tasks.router)
