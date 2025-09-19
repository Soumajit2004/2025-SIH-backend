from __future__ import annotations

"""Chatbot service layer using Google Generative AI (Gemini) SDK directly.

This module encapsulates Firestore persistence and LLM invocation so the router
layer stays thin. The design:

Collection: chatbot_sessions
Document ID: session id (string)
Document schema:
  {
    "createdAt": <timestamp>,
    "updatedAt": <timestamp>,
    "history": [
        {"type": "system"|"user"|"assistant", "message": str, "timestamp": <ts>},
        ...
    ]
  }

We return only system/user pairs in response history per spec (the spec allowed
system|user, but we'll keep assistant messages as well internally. The router can
filter if strict). For now we'll expose all three; caller can ignore.

Environment Variable Expected:
  GOOGLE_API_KEY: API key for Google Generative AI (Gemini). Not validated here to
  allow the backend to start even if unset (similar to Firebase approach). The LLM
  call will raise if the key is missing.

System Prompt:
  Placeholder constant SYSTEM_PROMPT is defined so integrators can customize.
"""

import os
import uuid
from functools import lru_cache
from typing import Dict, Any, List

from app.utils.firebase import get_firestore, server_timestamp, to_firestore_timestamp
from app.core.config import settings

import google.generativeai as genai  # type: ignore

# Load system prompt from external text file so it can be edited without code changes.
_SYSTEM_PROMPT_FALLBACK = "You are a helpful tourism assistant. Provide concise, factual answers."
_SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    """Return the system prompt loaded from `system_prompt.txt`.

    Fallback to default string if file missing or unreadable. Cached to avoid
    repeated disk I/O per process lifecycle. In tests, cache can be cleared via
    _load_system_prompt.cache_clear().
    """
    try:
        with open(_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content or _SYSTEM_PROMPT_FALLBACK
    except Exception:
        return _SYSTEM_PROMPT_FALLBACK


def get_system_prompt() -> str:
    return _load_system_prompt()

COLLECTION = "chatbot_sessions"


def _configure():
    api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set (env or settings)")
    # configure only once
    if not getattr(_configure, "_done", False):  # type: ignore[attr-defined]
        # Some versions expose configure; if not, set env var is enough for default client libs.
        if hasattr(genai, "configure"):
            try:
                genai.configure(api_key=api_key)  # type: ignore[attr-defined]
            except Exception:
                pass
        _configure._done = True  # type: ignore[attr-defined]


def _model():
    _configure()
    model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
    model_cls = getattr(genai, "GenerativeModel", None)
    if model_cls is None:
        raise RuntimeError("google.generativeai.GenerativeModel not available in installed SDK")
    return model_cls(model_name)


def _firestore():
    return get_firestore()


def _now_ts():
    return to_firestore_timestamp(server_timestamp())


def create_session(initial_user_message: str) -> Dict[str, Any]:
    db = _firestore()
    sid = str(uuid.uuid4())
    now = _now_ts()
    system_prompt = get_system_prompt()
    history: List[Dict[str, Any]] = [
        {"type": "system", "message": system_prompt, "timestamp": now},
        {"type": "user", "message": initial_user_message, "timestamp": now},
    ]

    # Generate assistant reply
    assistant_msg = _generate_reply(history)
    history.append(assistant_msg)

    doc = {
        "createdAt": now,
        "updatedAt": now,
        "history": history,
    }
    db.collection(COLLECTION).document(sid).set(doc)

    return {"id": sid, "history": _public_history(history)}


def append_message(session_id: str, user_message: str) -> Dict[str, Any]:
    db = _firestore()
    ref = db.collection(COLLECTION).document(session_id)
    snap = ref.get()
    if not snap.exists:
        raise KeyError("Session not found")
    data = snap.to_dict() or {}
    history: List[Dict[str, Any]] = data.get("history", [])

    now = _now_ts()
    user_entry = {"type": "user", "message": user_message, "timestamp": now}
    history.append(user_entry)

    assistant_msg = _generate_reply(history)
    history.append(assistant_msg)

    ref.update({
        "history": history,
        "updatedAt": now,
    })

    return {"id": session_id, "history": _public_history(history)}


def _generate_reply(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Build a single prompt concatenating system + conversation (simple approach)
    system_prompt = get_system_prompt()
    convo_lines: List[str] = []
    for item in history:
        if item["type"] == "system":
            # take first system prompt only
            if system_prompt == get_system_prompt():  # default unchanged
                system_prompt = item["message"] or get_system_prompt()
        elif item["type"] == "user":
            convo_lines.append(f"User: {item['message']}")
        elif item["type"] == "assistant":
            convo_lines.append(f"Assistant: {item['message']}")

    full_prompt = system_prompt + "\n\n" + "\n".join(convo_lines) + "\nAssistant:"

    try:
        model = _model()
        resp = model.generate_content(full_prompt)
        if hasattr(resp, "text"):
            content = resp.text
        else:
            # Fallback attempt
            content = getattr(resp, "candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "(no response)")
    except Exception as e:  # pragma: no cover - network / API failure
        content = f"(error generating reply: {e})"

    return {"type": "assistant", "message": content, "timestamp": _now_ts()}


def _public_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Exclude system prompt from outward facing history
    return [h for h in history if h["type"] != "system"]

__all__ = [
    "create_session",
    "append_message",
    "get_system_prompt",
]
