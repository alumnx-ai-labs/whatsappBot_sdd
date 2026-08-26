from sqlalchemy.orm import Session

from app.db.models import AdminUser


def find_by_email(db: Session, email: str) -> AdminUser | None:
    return db.query(AdminUser).filter(AdminUser.email == email).first()


def find_by_id(db: Session, admin_id: str) -> AdminUser | None:
    return db.query(AdminUser).filter(AdminUser.id == admin_id).first()
