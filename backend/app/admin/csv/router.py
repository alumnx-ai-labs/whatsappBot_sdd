from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.admin.auth.require_session import require_admin_session
from app.admin.csv.csv_parser import CsvValidationError
from app.admin.csv.csv_upload_service import CsvUploadService
from app.db.models import AdminUser
from app.db.session import get_db
from app.shared.config import settings
from app.shared.errors import AppError

router = APIRouter(prefix="/admin/metadata/csv", tags=["admin-csv"])
service = CsvUploadService()


@router.post("")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin_session),
) -> dict:
    content = await file.read()
    if len(content) > settings.csv_max_file_bytes:
        raise AppError(413, "file_too_large", "CSV exceeds configured file size limit")
    try:
        return service.process(
            db, content=content, filename=file.filename or "upload.csv", admin=admin
        )
    except CsvValidationError as exc:
        code = str(exc)
        if code.startswith("missing_headers:"):
            missing = code.split(":", 1)[1].split(",")
            raise AppError(
                400, "invalid_schema", "Required CSV headers are missing", missing
            ) from exc
        if code == "empty_file":
            raise AppError(400, "empty_file", "CSV file is empty") from exc
        if code == "file_too_large":
            raise AppError(413, "file_too_large", "CSV exceeds configured row limit") from exc
        raise AppError(400, "malformed_csv", "CSV file could not be parsed") from exc
