from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_preflight_localhost():
    origin = "http://localhost:5173"  # typical Vite dev server
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code in (200, 204)
    # FastAPI's CORSMiddleware sends these headers when origin matches
    assert response.headers.get("access-control-allow-origin") == origin
    allow_methods = response.headers.get("access-control-allow-methods")
    assert allow_methods is not None and "GET" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers")
    assert allow_headers is not None


def test_cors_disallowed_external_origin():
    origin = "https://example.com"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    # Not allowed, so no CORS allow-origin header
    assert "access-control-allow-origin" not in response.headers
