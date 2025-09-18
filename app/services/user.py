"""User service handling Firestore user retrieval / creation."""
from __future__ import annotations

from typing import Dict, Any, Optional

from app.utils.firebase import get_firestore, server_timestamp

USERS_COLLECTION = "users"


def get_or_create_user(uid: str, email: Optional[str]) -> Dict[str, Any]:
    db = get_firestore()
    ref = db.collection(USERS_COLLECTION).document(uid)
    snap = ref.get()
    if snap.exists:
        data = snap.to_dict() or {}
    else:
        # New user defaults: regular user (not admin)
        data = {"email": email, "type": "user", "createdOn": server_timestamp()}
        ref.set(data)
    data["id"] = uid
    return data
