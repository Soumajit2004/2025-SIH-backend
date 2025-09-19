from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app

# Monkeypatch the LLM generation to avoid external calls
from app.services import chatbot as cb_service

def fake_generate_reply(history):  # pragma: no cover - simplicity
    return {"type": "assistant", "message": "stub reply", "timestamp": history[-1]["timestamp"]}

cb_service._generate_reply = fake_generate_reply  # type: ignore

client = TestClient(app)

def test_chatbot_new_session():
    resp = client.post("/chatbot/new", json={"message": "Hello"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "id" in data
    assert len(data["history"]) >= 2  # system + user + maybe assistant


def test_chatbot_append():
    new_resp = client.post("/chatbot/new", json={"message": "Start"})
    sid = new_resp.json()["id"]
    resp = client.post(f"/chatbot/{sid}", json={"message": "Next"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sid
    assert any(msg["type"] == "user" for msg in data["history"])  # user messages present
