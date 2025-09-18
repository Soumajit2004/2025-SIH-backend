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
from firebase_admin import credentials, firestore, auth


def _load_credentials() -> credentials.Base:
	"""Load service account credentials from env variables.

	Priority:
	1. FIREBASE_CREDENTIALS (path to json file)
	2. FIREBASE_CREDENTIALS_B64 (base64 of json content)
	3. FIREBASE_CREDENTIALS_JSON (raw json string)
	Raises RuntimeError if none available.
	"""
	path = os.getenv("FIREBASE_CREDENTIALS")
	if path and os.path.isfile(path):
		return credentials.Certificate(path)

	b64_content = os.getenv("FIREBASE_CREDENTIALS_B64")
	if b64_content:
		data = json.loads(base64.b64decode(b64_content).decode("utf-8"))
		return credentials.Certificate(data)

	raw_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
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


def server_timestamp() -> datetime:
	return datetime.now(timezone.utc)


def to_firestore_timestamp(dt: datetime) -> Any:
	"""Currently Firestore python client accepts native datetime objects with tzinfo UTC."""
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	return dt
