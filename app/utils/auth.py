"""Authentication dependency using Firebase bearer token.

Usage:
    from app.utils.auth import get_current_user
    @router.get("/me")
    async def me(user=Depends(get_current_user)):
        return user

The dependency returns a dict representing the user document plus an 'id' field.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Dict

from .firebase import get_auth
from app.services.user import get_or_create_user
from app.core.config import settings

security = HTTPBearer(auto_error=True)

USERS_COLLECTION = "users"  # retained for backward compatibility; not used directly

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Return the current authenticated user.

    In development, when settings.DEV_USE_DUMMY_USER is True, bypass Firebase token
    verification and return (and persist) a dummy user. This allows local frontend
    development without integrating full Firebase auth flows.
    """
    if settings.DEV_USE_DUMMY_USER:
        # Create or fetch dummy user record
        return get_or_create_user(
            uid=settings.DEV_DUMMY_USER_UID,
            email=settings.DEV_DUMMY_USER_EMAIL,
        ) | {"_dev_dummy": True}

    token = creds.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    auth = get_auth()
    try:
        decoded = auth.verify_id_token(token)  # type: ignore[attr-defined]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = decoded.get("uid")
    email = decoded.get("email")
    if not uid:
        raise HTTPException(status_code=401, detail="Token missing uid")

    return get_or_create_user(uid=uid, email=email)


async def admin_required(user=Depends(get_current_user)):
    if user.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
