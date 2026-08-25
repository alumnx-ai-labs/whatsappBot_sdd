from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.admin.auth.require_session import require_admin_session
from app.admin.metadata.metadata_schema import MetadataInput, MetadataResponse
from app.admin.metadata.metadata_service import MetadataService, MetadataValidationError
from app.db.models import AdminUser, BusinessMetadata
from app.db.session import get_db
from app.shared.errors import AppError

router = APIRouter(prefix="/admin/metadata", tags=["admin-metadata"])
service = MetadataService()


@router.post("", response_model=dict, status_code=201)
def create_metadata(
    body: MetadataInput,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    try:
        record, outcome = service.save(db, body)
    except MetadataValidationError as exc:
        raise AppError(422, "validation_failed", str(exc)) from exc
    return {
        "id": record.id,
        "outcome": outcome,
        "record": MetadataResponse.model_validate(record).model_dump(by_alias=True),
    }


@router.put("/{record_id}", response_model=dict)
def update_metadata(
    record_id: str,
    body: MetadataInput,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    existing = service.get(db, record_id)
    if existing is None:
        raise AppError(404, "not_found", "Metadata record not found")
    try:
        record = service.update(db, existing, body)
    except MetadataValidationError as exc:
        raise AppError(422, "validation_failed", str(exc)) from exc
    return {
        "id": record.id,
        "outcome": "UPDATED",
        "record": MetadataResponse.model_validate(record).model_dump(by_alias=True),
    }


@router.get("", response_model=dict)
def list_metadata(
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    records = service.list(db)
    return {
        "records": [
            MetadataResponse.model_validate(record).model_dump(by_alias=True) for record in records
        ]
    }


@router.get("/{record_id}", response_model=MetadataResponse)
def get_metadata(
    record_id: str,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> BusinessMetadata:
    record = service.get(db, record_id)
    if record is None:
        raise AppError(404, "not_found", "Metadata record not found")
    return record
