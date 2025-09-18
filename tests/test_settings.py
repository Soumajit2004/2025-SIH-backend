from __future__ import annotations

import os
import base64
import json
from app.core.config import Settings


def test_settings_allows_missing_firebase_credentials():
    s = Settings()
    assert s.PORT == 8000


def test_settings_file_priority(tmp_path):
    cred_data = {"type": "service_account", "project_id": "demo"}
    raw_json = json.dumps(cred_data)
    b64_json = base64.b64encode(raw_json.encode()).decode()
    fpath = tmp_path / "sa.json"
    fpath.write_text(raw_json)

    # Provide all three; expect path to win
    s = Settings(
        FIREBASE_CREDENTIALS=str(fpath),
        FIREBASE_CREDENTIALS_B64=b64_json,
        FIREBASE_CREDENTIALS_JSON=raw_json,
    )
    assert s.FIREBASE_CREDENTIALS == str(fpath)
