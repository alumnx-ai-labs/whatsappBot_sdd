from fastapi import APIRouter, Cookie, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.admin.auth.admin_user_repository import find_by_email
from app.admin.auth.require_session import require_admin_session
from app.admin.auth.session_service import create_session_token, revoke_session
from app.db.models import AdminUser
from app.db.session import get_db
from app.shared.config import settings
from app.shared.errors import AppError
from app.shared.password_hashing import verify_password

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _cookie_kwargs() -> dict:
    return {
        "key": settings.admin_session_cookie_name,
        "httponly": True,
        "secure": settings.environment != "development",
        "samesite": "strict",
        "max_age": settings.admin_session_ttl_minutes * 60,
    }


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    admin = find_by_email(db, body.email)
    # Generic error message for both "no such user" and "wrong password" to avoid enumeration.
    if not admin or not verify_password(body.password, admin.password_hash):
        raise AppError(401, "invalid_credentials", "Invalid email or password")

    token = create_session_token(admin.id, admin.email)
    response.set_cookie(value=token, **_cookie_kwargs())
    return {"adminId": admin.id, "email": admin.email}


@router.post("/logout")
def logout(
    response: Response,
    admin_session: str | None = Cookie(default=None, alias=settings.admin_session_cookie_name),
) -> dict:
    if admin_session:
        revoke_session(admin_session)
    response.delete_cookie(key=settings.admin_session_cookie_name)
    return {"success": True}


@router.get("/session")
def session_status(admin: AdminUser = Depends(require_admin_session)) -> dict:
    return {"authenticated": True, "adminId": admin.id, "email": admin.email}
