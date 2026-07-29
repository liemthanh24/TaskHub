from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="TaskHub API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(tasks.router)
