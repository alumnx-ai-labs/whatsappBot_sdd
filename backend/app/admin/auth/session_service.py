from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.shared.config import settings

_ALGORITHM = "HS256"
_revoked_tokens: set[str] = set()


def create_session_token(admin_id: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.admin_session_ttl_minutes)
    payload = {"sub": admin_id, "email": email, "exp": expire, "jti": str(uuid4())}
    return jwt.encode(payload, settings.admin_session_secret, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.admin_session_secret, algorithms=[_ALGORITHM])
        if payload.get("jti") in _revoked_tokens:
            return None
        return payload
    except JWTError:
        return None


def revoke_session(token: str) -> None:
    payload = decode_session_token(token)
    if payload and payload.get("jti"):
        _revoked_tokens.add(payload["jti"])
