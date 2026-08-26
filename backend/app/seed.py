from app.db.models import AdminUser, BusinessMetadata
from app.db.session import SessionLocal
from app.shared.password_hashing import hash_password

SEED_ADMIN_EMAIL = "admin@example.com"
SEED_ADMIN_PASSWORD = "ChangeMe123!"


def run() -> None:
    db = SessionLocal()
    try:
        if not db.query(AdminUser).filter(AdminUser.email == SEED_ADMIN_EMAIL).first():
            db.add(
                AdminUser(
                    email=SEED_ADMIN_EMAIL,
                    password_hash=hash_password(SEED_ADMIN_PASSWORD),
                )
            )
        if (
            not db.query(BusinessMetadata)
            .filter(BusinessMetadata.whatsapp_phone == "+15550001111")
            .first()
        ):
            db.add(
                BusinessMetadata(
                    business_name="Sample Business",
                    contact_person="Jane Doe",
                    whatsapp_phone="+15550001111",
                    address="123 Main St",
                    sector="Retail",
                    business_description="Seeded sample record",
                    source_type="FORM",
                )
            )
        db.commit()
        print(f"Seeded admin user: {SEED_ADMIN_EMAIL} / {SEED_ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
