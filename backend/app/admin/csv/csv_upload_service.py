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
        results = []
        for row_number, row in enumerate(rows, start=2):
            try:
                data = MetadataInput.model_validate(row)
                phone = data.whatsapp_phone
                from app.webhook.phone_normalizer import normalize_phone

                normalized_phone = normalize_phone(phone)
                if normalized_phone in seen_phones:
                    results.append(
                        {
                            "rowNumber": row_number,
                            "outcome": "SKIPPED",
                            "reason": "duplicate within file",
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
                    continue
                seen_phones.add(normalized_phone)
                data = data.model_copy(update={"whatsapp_phone": normalized_phone})
                record, outcome = self.metadata_service.save(db, data, source_type="CSV")
                results.append({"rowNumber": row_number, "outcome": outcome})
                db.add(
                    CsvUploadRow(
                        batch_id=batch.id, row_number=row_number, outcome=outcome, raw_row_data=row
                    )
                )
                batch.accepted_rows += 1
            except (MetadataValidationError, ValueError) as exc:
                reason = str(exc)
                results.append({"rowNumber": row_number, "outcome": "REJECTED", "reason": reason})
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

        db.commit()
        return {
            "batchId": batch.id,
            "totalRows": len(rows),
            "accepted": batch.accepted_rows,
            "rejected": batch.rejected_rows,
            "rows": results,
            **({"ignoredColumns": ignored_columns} if ignored_columns else {}),
        }
