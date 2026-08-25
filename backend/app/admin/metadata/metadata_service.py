from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin.metadata.metadata_schema import MetadataInput
from app.db.models import BusinessMetadata
from app.webhook.phone_normalizer import InvalidPhoneNumberError, normalize_phone


class MetadataValidationError(ValueError):
    pass


class MetadataService:
    def save(
        self, db: Session, data: MetadataInput, source_type: str = "FORM"
    ) -> tuple[BusinessMetadata, str]:
        try:
            canonical_phone = normalize_phone(data.whatsapp_phone)
        except InvalidPhoneNumberError as exc:
            raise MetadataValidationError(str(exc)) from exc

        record = db.scalar(
            select(BusinessMetadata).where(BusinessMetadata.whatsapp_phone == canonical_phone)
        )
        outcome = "UPDATED" if record else "CREATED"
        if record is None:
            record = BusinessMetadata(whatsapp_phone=canonical_phone)
            db.add(record)

        record.business_name = data.business_name.strip()
        record.contact_person = data.contact_person.strip()
        record.whatsapp_phone = canonical_phone
        record.address = data.address.strip() if data.address else None
        record.sector = data.sector.strip() if data.sector else None
        record.business_description = (
            data.business_description.strip() if data.business_description else None
        )
        record.source_type = source_type
        db.commit()
        db.refresh(record)
        return record, outcome

    def list(self, db: Session) -> list[BusinessMetadata]:
        return list(db.scalars(select(BusinessMetadata).order_by(BusinessMetadata.business_name)))

    def get(self, db: Session, record_id: str) -> BusinessMetadata | None:
        return db.get(BusinessMetadata, record_id)

    def update(
        self, db: Session, record: BusinessMetadata, data: MetadataInput
    ) -> BusinessMetadata:
        try:
            canonical_phone = normalize_phone(data.whatsapp_phone)
        except InvalidPhoneNumberError as exc:
            raise MetadataValidationError(str(exc)) from exc

        conflict = db.scalar(
            select(BusinessMetadata).where(
                BusinessMetadata.whatsapp_phone == canonical_phone,
                BusinessMetadata.id != record.id,
            )
        )
        if conflict is not None:
            raise MetadataValidationError("whatsappPhone is already assigned to another record")

        record.business_name = data.business_name.strip()
        record.contact_person = data.contact_person.strip()
        record.whatsapp_phone = canonical_phone
        record.address = data.address.strip() if data.address else None
        record.sector = data.sector.strip() if data.sector else None
        record.business_description = (
            data.business_description.strip() if data.business_description else None
        )
        db.commit()
        db.refresh(record)
        return record
