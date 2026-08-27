from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.admin.csv.csv_parser import CsvValidationError, parse_csv
from app.admin.metadata.metadata_schema import MetadataInput
from app.admin.metadata.metadata_service import MetadataService, MetadataValidationError
from app.db.models import AdminUser, CsvUploadBatch, CsvUploadRow
from app.shared.config import settings


class CsvUploadService:
    def __init__(self, metadata_service: MetadataService | None = None) -> None:
        self.metadata_service = metadata_service or MetadataService()

    def process(self, db: Session, *, content: bytes, filename: str, admin: AdminUser) -> dict:
        if len(content) > settings.csv_max_file_bytes:
            raise CsvValidationError("file_too_large")
        rows, ignored_columns = parse_csv(content, settings.csv_max_rows)
        batch = CsvUploadBatch(
            uploaded_by_admin_id=admin.id,
            file_name=filename,
            total_rows=len(rows),
            accepted_rows=0,
            rejected_rows=0,
        )
        db.add(batch)
        db.flush()
        seen_phones: set[str] = set()
        first_row_by_phone: dict[str, int] = {}
        results = []
        row_errors = []
        created_rows = 0
        updated_rows = 0
        failed_rows = 0
        skipped_rows = 0
        for row_number, row in enumerate(rows, start=2):
            try:
                data = MetadataInput.model_validate(row)
                phone = data.whatsapp_phone
                from app.webhook.phone_normalizer import normalize_phone

                normalized_phone = normalize_phone(phone)
                if normalized_phone in seen_phones:
                    duplicate_of_row = first_row_by_phone[normalized_phone]
                    results.append(
                        {
                            "row_number": row_number,
                            "outcome": "SKIPPED",
                            "reason": "duplicate within file",
                            "duplicate_of_row": duplicate_of_row,
                        }
                    )
                    db.add(
                        CsvUploadRow(
                            batch_id=batch.id,
                            row_number=row_number,
                            outcome="SKIPPED",
                            error_reason="duplicate within file",
                            raw_row_data=row,
                        )
                    )
                    skipped_rows += 1
                    continue
                seen_phones.add(normalized_phone)
                first_row_by_phone[normalized_phone] = row_number
                data = data.model_copy(update={"whatsapp_phone": normalized_phone})
                record, outcome = self.metadata_service.save(db, data, source_type="CSV")
                results.append({"row_number": row_number, "outcome": outcome})
                db.add(
                    CsvUploadRow(
                        batch_id=batch.id, row_number=row_number, outcome=outcome, raw_row_data=row
                    )
                )
                batch.accepted_rows += 1
                if outcome == "CREATED":
                    created_rows += 1
                elif outcome == "UPDATED":
                    updated_rows += 1
            except ValidationError as exc:
                field_errors = {
                    str(error["loc"][0]): str(error["msg"])
                    for error in exc.errors()
                    if error.get("loc")
                }
                results.append(
                    {
                        "row_number": row_number,
                        "outcome": "REJECTED",
                        "errors": field_errors,
                    }
                )
                row_errors.append({"row_number": row_number, "errors": field_errors})
                db.add(
                    CsvUploadRow(
                        batch_id=batch.id,
                        row_number=row_number,
                        outcome="REJECTED",
                        error_reason=str(field_errors),
                        raw_row_data=row,
                    )
                )
                batch.rejected_rows += 1
                failed_rows += 1
            except (MetadataValidationError, ValueError) as exc:
                reason = str(exc)
                field = "whatsappPhone" if "phone" in reason.casefold() else "row"
                errors = {field: reason}
                results.append({"row_number": row_number, "outcome": "REJECTED", "errors": errors})
                row_errors.append({"row_number": row_number, "errors": errors})
                db.add(
                    CsvUploadRow(
                        batch_id=batch.id,
                        row_number=row_number,
                        outcome="REJECTED",
                        error_reason=reason,
                        raw_row_data=row,
                    )
                )
                batch.rejected_rows += 1
                failed_rows += 1
            except Exception:
                reason = "processing_error"
                results.append({"row_number": row_number, "outcome": "REJECTED", "reason": reason})
                row_errors.append({"row_number": row_number, "reason": reason})
                db.add(
                    CsvUploadRow(
                        batch_id=batch.id,
                        row_number=row_number,
                        outcome="REJECTED",
                        error_reason=reason,
                        raw_row_data=row,
                    )
                )
                batch.rejected_rows += 1
                failed_rows += 1

        db.commit()
        return {
            "batch_id": batch.id,
            "total_rows": len(rows),
            "successful_rows": created_rows + updated_rows,
            "created_rows": created_rows,
            "updated_rows": updated_rows,
            "failed_rows": failed_rows,
            "skipped_rows": skipped_rows,
            "row_errors": row_errors,
            "rows": results,
            **({"ignored_columns": ignored_columns} if ignored_columns else {}),
        }
