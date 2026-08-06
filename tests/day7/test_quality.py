import importlib

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("module_name", ["app.api.deps", "app.core.queue", "app.routers.tasks", "app.routers.auth"])
def test_modules_import_cleanly(module_name):
    importlib.import_module(module_name)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_has_expected_paths(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for path in ("/health", "/auth/register", "/auth/login", "/auth/me", "/tasks/", "/tasks/page", "/tasks/all"):
        assert path in paths


def test_dead_code_dependencies_module_removed():
    with pytest.raises(ImportError):
        importlib.import_module("app.dependencies")


def test_serialize_helper_matches_task_schema():
    from app.routers.tasks import _serialize_task

    payload = {
        "id": 1,
        "user_id": 1,
        "title": "Demo",
        "description": None,
        "due_date": None,
        "completed": False,
        "created_at": "2026-01-01T00:00:00Z",
    }
    assert _serialize_task(payload)["title"] == "Demo"
