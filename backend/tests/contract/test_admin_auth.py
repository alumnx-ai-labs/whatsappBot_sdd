from app.db.models import AdminUser
from app.shared.password_hashing import hash_password


def _create_admin(test_db_engine, email="admin@example.com", password="Sup3rSecret!") -> None:
    from sqlalchemy.orm import Session

    with Session(test_db_engine) as db:
        db.add(AdminUser(email=email, password_hash=hash_password(password)))
        db.commit()


def test_login_success_sets_cookie_and_returns_profile(client, test_db_engine) -> None:
    _create_admin(test_db_engine)
    response = client.post(
        "/admin/auth/login", json={"email": "admin@example.com", "password": "Sup3rSecret!"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@example.com"
    assert "adminId" in body
    assert "admin_session" in response.cookies


def test_login_failure_returns_generic_error(client, test_db_engine) -> None:
    _create_admin(test_db_engine)
    response = client.post(
        "/admin/auth/login", json={"email": "admin@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_login_unknown_email_returns_same_generic_error(client, test_db_engine) -> None:
    response = client.post(
        "/admin/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_session_check_requires_authentication(client) -> None:
    response = client.get("/admin/auth/session")
    assert response.status_code == 401
    assert response.json()["error"] == "unauthenticated"


def test_session_check_succeeds_after_login(client, test_db_engine) -> None:
    _create_admin(test_db_engine)
    client.post(
        "/admin/auth/login", json={"email": "admin@example.com", "password": "Sup3rSecret!"}
    )
    response = client.get("/admin/auth/session")
    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_logout_clears_session(client, test_db_engine) -> None:
    _create_admin(test_db_engine)
    client.post(
        "/admin/auth/login", json={"email": "admin@example.com", "password": "Sup3rSecret!"}
    )
    logout_response = client.post("/admin/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"success": True}

    session_response = client.get("/admin/auth/session")
    assert session_response.status_code == 401
