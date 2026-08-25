from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Customer


def find_customer_by_phone(db: Session, canonical_phone: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.canonical_phone == canonical_phone))


def create_customer(
    db: Session,
    *,
    canonical_phone: str,
    name: str,
    business_name: str,
    contact_info: str | None = None,
) -> Customer:
    customer = Customer(
        canonical_phone=canonical_phone,
        name=name,
        business_name=business_name,
        contact_info=contact_info,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
