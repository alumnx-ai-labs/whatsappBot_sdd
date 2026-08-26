from app.admin.auth.session_service import decode_session_token
from app.db.models import AdminUser
from app.shared.password_hashing import hash_password


def test_logout_revokes_copied_session_token(client, test_db_engine) -> None:
    from sqlalchemy.orm import Session

    with Session(test_db_engine) as db:
        db.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("Sup3rSecret!"),
            )
        )
        db.commit()

    login = client.post(
        "/admin/auth/login",
        json={"email": "admin@example.com", "password": "Sup3rSecret!"},
    )
    token = login.cookies.get("admin_session")
    assert token is not None
    assert decode_session_token(token) is not None

    client.post("/admin/auth/logout")
    assert decode_session_token(token) is None
