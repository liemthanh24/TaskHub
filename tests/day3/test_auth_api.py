from jose import jwt

from app.core.config import settings


class TestRegister:
    def test_register_valid(self, client):
        resp = client.post("/auth/register", json={
            "email": "user@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["token_type"] == "bearer"
        payload = jwt.decode(data["access_token"], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert int(payload["sub"]) >= 1

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "secret123"}
        first = client.post("/auth/register", json=payload)
        assert first.status_code == 201
        second = client.post("/auth/register", json=payload)
        assert second.status_code == 400
        assert second.json()["detail"] == "Email already registered"

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={"email": "not-an-email", "password": "secret123"})
        assert resp.status_code == 422

    def test_register_short_password(self, client):
        resp = client.post("/auth/register", json={"email": "user@example.com", "password": "123"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_valid(self, client):
        client.post("/auth/register", json={"email": "user@example.com", "password": "secret123"})
        resp = client.post("/auth/login", json={"email": "user@example.com", "password": "secret123"})
        assert resp.status_code == 200
        assert resp.json()["token_type"] == "bearer"
        assert resp.json()["access_token"]

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={"email": "user@example.com", "password": "secret123"})
        resp = client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpass"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/login", json={"email": "ghost@example.com", "password": "secret123"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"


class TestToken:
    def test_token_sub_matches_user_id(self, client):
        reg = client.post("/auth/register", json={"email": "user@example.com", "password": "secret123"})
        token = reg.json()["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert int(payload["sub"]) == 1
        assert payload["exp"] > 0
