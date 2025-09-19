"""Hospitality service for CRUD operations on hospitality collection."""
from __future__ import annotations

from typing import Optional, List, Dict, Any, Iterable, Tuple
from app.utils.firebase import get_firestore, server_timestamp, upload_bytes, delete_prefix
import secrets

IMAGE_FOLDER = "hospitality"  # root folder in storage

COLLECTION = "hospitality"


def _collection():
    return get_firestore().collection(COLLECTION)


def _detect_image_ext(data: bytes) -> Optional[str]:
    """Very small helper to detect image extension via signature.

    Returns extension (jpeg|png|gif|webp) or None if unknown.
    (Avoids dependency on deprecated/removed imghdr in some environments.)
    """
    if len(data) < 12:
        return None
    # JPEG
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    # GIF
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"
    # WEBP (RIFF....WEBP)
    if data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _sanitize_images(files: Optional[Iterable[Tuple[str, bytes, Optional[str]]]]) -> List[Dict[str, Any]]:
    """Validate image bytes and produce list of dicts with path + url.

    Input iterable elements: (filename, bytes, content_type)
    We attempt to detect image type via imghdr as a safety check.
    Unsupported files are skipped.
    """
    results: List[Dict[str, Any]] = []
    if not files:
        return results
    for original_name, data, content_type in files:
        if not data:
            continue
        # Basic image validation
        ext = _detect_image_ext(data)
        if ext is None:
            if not (content_type and content_type.startswith("image/")):
                continue
            ext = content_type.split("/")[-1]
        # create deterministic-ish random name
        rand = secrets.token_hex(8)
        safe_name = original_name.rsplit('.', 1)[0][:50]
        filename = f"{safe_name}-{rand}.{ext}" if safe_name else f"{rand}.{ext}"
        # path decided by caller when hospitality id known; we temporarily store name
        results.append({"_filename": filename, "original": original_name, "_data": data, "contentType": content_type or f"image/{ext}"})
    return results


def create_hospitality(*, htype: str, name: str, description: str, latitude: float, longitude: float, images: Optional[Iterable[tuple[str, bytes, Optional[str]]]] = None) -> Dict[str, Any]:
    col = _collection()
    ref = col.document()
    data = {
        "type": htype,
        "name": name,
        "description": description,
        "location": {"lat": latitude, "lng": longitude},
        "createdOn": server_timestamp(),
    }
    ref.set(data)
    data["id"] = ref.id

    # Handle image uploads after document creation (need id for path)
    image_entries = _sanitize_images(images)
    stored: List[Dict[str, str]] = []
    for entry in image_entries:
        filename = entry.pop("_filename")
        raw = entry.pop("_data")  # bytes
        path = f"{IMAGE_FOLDER}/{ref.id}/{filename}"
        url = upload_bytes(path, raw, content_type=entry["contentType"], make_public=True)
        stored.append({"path": path, "url": url, "original": entry["original"], "contentType": entry["contentType"]})
    if stored:
        ref.update({"images": stored})
        data["images"] = stored
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


def update_hospitality(hid: str, *, name: Optional[str] = None, description: Optional[str] = None, htype: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, new_images: Optional[Iterable[tuple[str, bytes, Optional[str]]]] = None, replace_images: bool = False) -> Optional[Dict[str, Any]]:
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
    if latitude is not None or longitude is not None:
        existing = snap.to_dict() or {}
        loc = existing.get("location", {}) or {}
        if latitude is not None:
            loc["lat"] = latitude
        if longitude is not None:
            loc["lng"] = longitude
        updates["location"] = loc
    if new_images:
        # load current images
        current = [] if replace_images else (snap.to_dict() or {}).get("images", [])
        image_entries = _sanitize_images(new_images)
        for entry in image_entries:
            filename = entry.pop("_filename")
            raw = entry.pop("_data")  # bytes
            path = f"{IMAGE_FOLDER}/{hid}/{filename}"
            url = upload_bytes(path, raw, content_type=entry["contentType"], make_public=True)
            current.append({"path": path, "url": url, "original": entry["original"], "contentType": entry["contentType"]})
        updates["images"] = current
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
    # Delete all images under this hospitality id
    prefix = f"{IMAGE_FOLDER}/{hid}/"
    delete_prefix(prefix)
    ref.delete()
    return True
