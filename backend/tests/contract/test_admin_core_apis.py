from datetime import date

from sqlalchemy.orm import Session

from app.db.models import AdminUser, Booking, ConversationSession, Customer
from app.shared.password_hashing import hash_password


def _login(client, test_db_engine) -> None:
    with Session(test_db_engine) as db:
        db.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("Sup3rSecret!"),
            )
        )
        db.commit()
    response = client.post(
        "/admin/auth/login",
        json={"email": "admin@example.com", "password": "Sup3rSecret!"},
    )
    assert response.status_code == 200


def test_metadata_requires_admin_and_supports_create_and_update(client, test_db_engine) -> None:
    unauthorized = client.post(
        "/admin/metadata",
        json={
            "businessName": "Acme",
            "contactPerson": "Jane",
            "whatsappPhone": "+919494151816",
        },
    )
    assert unauthorized.status_code == 401

    _login(client, test_db_engine)
    created = client.post(
        "/admin/metadata",
        json={
            "businessName": "Acme",
            "contactPerson": "Jane",
            "whatsappPhone": "+919494151816",
        },
    )
    assert created.status_code == 201
    record_id = created.json()["id"]

    updated = client.put(
        f"/admin/metadata/{record_id}",
        json={
            "businessName": "Acme Updated",
            "contactPerson": "Jane",
            "whatsappPhone": "919494151816",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["record"]["businessName"] == "Acme Updated"


def test_csv_reports_each_row(client, test_db_engine) -> None:
    _login(client, test_db_engine)
    csv = (
        b"businessName,contactPerson,whatsappPhone,address,sector,businessDescription\n"
        b"Acme,Jane,+919494151816,,,,\n"
        b"Bad,Row,not-a-phone,,,,\n"
        b"Duplicate,Row,919494151816,,,,\n"
    )
    response = client.post(
        "/admin/metadata/csv",
        files={"file": ("metadata.csv", csv, "text/csv")},
    )
    assert response.status_code == 200
    assert [row["outcome"] for row in response.json()["rows"]] == [
        "CREATED",
        "REJECTED",
        "SKIPPED",
    ]
    body = response.json()
    assert body["total_rows"] == 3
    assert body["successful_rows"] == 1
    assert body["created_rows"] == 1
    assert body["updated_rows"] == 0
    assert body["failed_rows"] == 1
    assert body["skipped_rows"] == 1
    assert body["row_errors"][0]["row_number"] == 3
    assert "whatsappPhone" in body["row_errors"][0]["errors"]


def test_bookings_api_returns_confirmed_only(client, test_db_engine) -> None:
    _login(client, test_db_engine)
    with Session(test_db_engine) as db:
        customer = Customer(canonical_phone="+919494151816", name="Jane", business_name="Acme")
        session = ConversationSession(canonical_phone=customer.canonical_phone)
        db.add_all([customer, session])
        db.commit()
        db.refresh(customer)
        db.refresh(session)
        db.add_all(
            [
                Booking(
                    booking_attempt_id="confirmed-1",
                    customer_id=customer.id,
                    customer_name="Jane",
                    business_name="Acme",
                    meeting_date=date(2099, 9, 1),
                    meeting_time="2pm",
                    location="Office",
                    status="CONFIRMED",
                    external_booking_id="HO-1",
                    session_id=session.id,
                ),
                Booking(
                    booking_attempt_id="failed-1",
                    customer_id=customer.id,
                    customer_name="Jane",
                    business_name="Acme",
                    meeting_date=date(2099, 9, 2),
                    meeting_time="3pm",
                    location="Office",
                    status="FAILED",
                    session_id=session.id,
                ),
            ]
        )
        db.commit()

    response = client.get("/admin/bookings?status=CONFIRMED")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["bookings"][0]["status"] == "CONFIRMED"
