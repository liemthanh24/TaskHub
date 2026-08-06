from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None = None
    due_date: datetime | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Page(BaseModel):
    items: list[Task]
    total: int
    page: int
    per_page: int
    pages: int


class TaskCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Học FastAPI",
                    "description": "Hoàn thành chương 5",
                    "due_date": "2026-08-10T18:00:00Z",
                }
            ]
        }
    )

    title: str
    description: str | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Học FastAPI nâng cao",
                    "completed": True,
                }
            ]
        }
    )

    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    completed: bool | None = None
