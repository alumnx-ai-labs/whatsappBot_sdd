from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.admin.auth.admin_user_repository import find_by_id
from app.admin.auth.session_service import decode_session_token
from app.db.models import AdminUser
from app.db.session import get_db
from app.shared.config import settings
from app.shared.errors import AppError


def require_admin_session(
    db: Session = Depends(get_db),
    admin_session: str | None = Cookie(default=None, alias=settings.admin_session_cookie_name),
) -> AdminUser:
    if not admin_session:
        raise AppError(401, "unauthenticated", "Admin session required")

    payload = decode_session_token(admin_session)
    if not payload:
        raise AppError(401, "unauthenticated", "Invalid or expired admin session")

    admin = find_by_id(db, payload["sub"])
    if not admin:
        raise AppError(401, "unauthenticated", "Admin account no longer exists")

    return admin
