"""Firebase initialization utilities.

This module lazily initializes the Firebase Admin SDK using a service account JSON
path provided via environment variable FIREBASE_CREDENTIALS (path to file) or a
base64 encoded JSON string FIREBASE_CREDENTIALS_B64 (useful for CI secrets).

Exports helper functions:
  get_firestore() -> firestore.Client
  get_auth() -> firebase_admin.auth
  server_timestamp() -> datetime (UTC now for createdOn fields)
"""

from __future__ import annotations

import os
import json
import base64
from functools import lru_cache
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

from app.core.config import settings


def _load_credentials() -> credentials.Base:
	"""Load service account credentials from env variables.

	Priority:
	1. FIREBASE_CREDENTIALS (path to json file)
	2. FIREBASE_CREDENTIALS_B64 (base64 of json content)
	3. FIREBASE_CREDENTIALS_JSON (raw json string)
	Raises RuntimeError if none available.
	"""
	# Use settings (which already validated file existence if provided)
	path = settings.FIREBASE_CREDENTIALS
	if path and os.path.isfile(path):
		return credentials.Certificate(path)

	b64_content = settings.FIREBASE_CREDENTIALS_B64
	if b64_content:
		data = json.loads(base64.b64decode(b64_content).decode("utf-8"))
		return credentials.Certificate(data)

	raw_json = settings.FIREBASE_CREDENTIALS_JSON
	if raw_json:
		data = json.loads(raw_json)
		return credentials.Certificate(data)

	raise RuntimeError("Firebase credentials not provided. Set FIREBASE_CREDENTIALS or FIREBASE_CREDENTIALS_B64 or FIREBASE_CREDENTIALS_JSON.")


@lru_cache(maxsize=1)
def _init_app() -> firebase_admin.App:
	if not firebase_admin._apps:  # type: ignore[attr-defined]
		cred = _load_credentials()
		return firebase_admin.initialize_app(cred)
	# Return first app
	return list(firebase_admin._apps.values())[0]  # type: ignore[attr-defined]


def get_firestore():
	_init_app()
	return firestore.client()


def get_auth():  # return module for simplicity
	_init_app()
	return auth


def get_storage_bucket():
	"""Return default storage bucket. Requires FIREBASE_STORAGE_BUCKET setting.

	The bucket must be specified in settings. We create (initialize) the app with
	default bucket if provided or lazily call storage.bucket(name) otherwise.
	"""
	_init_app()
	bucket_name = settings.FIREBASE_STORAGE_BUCKET
	if bucket_name:
		return storage.bucket(bucket_name)
	# fallback to default bucket configured inside credentials (may be None)
	return storage.bucket()


from typing import Optional


def upload_bytes(path: str, data: bytes, content_type: Optional[str] = None, make_public: bool = True) -> str:
	"""Upload raw bytes to storage under path and return the public URL.

	If make_public is True, the blob will be made publicly readable.
	"""
	bucket = get_storage_bucket()
	blob = bucket.blob(path)
	if content_type is not None:
		blob.upload_from_string(data, content_type=content_type)
	else:
		blob.upload_from_string(data)
	if make_public:
		try:
			blob.make_public()
		except Exception:
			# Ignore inability to make public; caller can still build signed URL if needed.
			pass
	return blob.public_url or f"gs://{bucket.name}/{path}"


def delete_prefix(prefix: str) -> int:
	"""Delete all blobs with given prefix. Returns number deleted."""
	bucket = get_storage_bucket()
	blobs = bucket.list_blobs(prefix=prefix)
	count = 0
	for b in blobs:
		try:
			b.delete()
			count += 1
		except Exception:
			pass
	return count


def server_timestamp() -> datetime:
	return datetime.now(timezone.utc)


def to_firestore_timestamp(dt: datetime) -> Any:
	"""Currently Firestore python client accepts native datetime objects with tzinfo UTC."""
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	return dt
