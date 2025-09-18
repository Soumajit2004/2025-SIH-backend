"""Hospitality service for CRUD operations on hospitality collection."""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from app.utils.firebase import get_firestore, server_timestamp

COLLECTION = "hospitality"


def _collection():
    return get_firestore().collection(COLLECTION)


def create_hospitality(*, htype: str, name: str, description: str) -> Dict[str, Any]:
    col = _collection()
    ref = col.document()
    data = {
        "type": htype,
        "name": name,
        "description": description,
        "createdOn": server_timestamp(),
    }
    ref.set(data)
    data["id"] = ref.id
    return data


def list_hospitality() -> List[Dict[str, Any]]:
    docs = _collection().stream()
    out: List[Dict[str, Any]] = []
    for d in docs:
        data = d.to_dict() or {}
        data["id"] = d.id
        out.append(data)
    return out


def get_hospitality(hid: str) -> Optional[Dict[str, Any]]:
    ref = _collection().document(hid)
    snap = ref.get()
    if not snap.exists:
        return None
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return data


def update_hospitality(hid: str, *, name: Optional[str] = None, description: Optional[str] = None, htype: Optional[str] = None) -> Optional[Dict[str, Any]]:
    ref = _collection().document(hid)
    snap = ref.get()
    if not snap.exists:
        return None
    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if htype is not None:
        updates["type"] = htype
    if updates:
        ref.update(updates)
    data = ref.get().to_dict() or {}
    data["id"] = hid
    return data


def delete_hospitality(hid: str) -> bool:
    ref = _collection().document(hid)
    snap = ref.get()
    if not snap.exists:
        return False
    ref.delete()
    return True
