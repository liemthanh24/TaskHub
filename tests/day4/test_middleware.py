from tests.day4.conftest import headers


class TestMiddleware:
    def test_request_id_header(self, client, user_token):
        resp = client.get("/tasks", headers=headers(user_token))
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID")

    def test_request_id_passthrough(self, client):
        resp = client.get("/health", headers={"X-Request-ID": "my-custom-id"})
        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == "my-custom-id"

    def test_process_time_header(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Process-Time-Ms")
        assert float(resp.headers["X-Process-Time-Ms"]) >= 0

    def test_cors_headers_present(self, client):
        resp = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


class TestErrorHandling:
    def test_unknown_route_404(self, client):
        resp = client.get("/nope")
        assert resp.status_code == 404
