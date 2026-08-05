import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def openapi():
    return app.openapi()


def test_openapi_has_description(openapi):
    assert "TaskHub" in openapi["info"]["description"]


def test_openapi_has_tags(openapi):
    names = [t["name"] for t in openapi["tags"]]
    assert {"auth", "tasks", "health"} <= set(names)


def test_endpoint_has_summary(openapi):
    assert openapi["paths"]["/auth/register"]["post"]["summary"]


def test_schema_has_examples(openapi):
    schemas = openapi["components"]["schemas"]
    assert "examples" in schemas["TaskCreate"]
    assert schemas["TaskCreate"]["examples"][0]["title"] == "Học FastAPI"


def test_docs_endpoint_served():
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
