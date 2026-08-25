import csv
import io
from typing import Any

REQUIRED_HEADERS = {"businessName", "contactPerson", "whatsappPhone"}
KNOWN_HEADERS = REQUIRED_HEADERS | {"address", "sector", "businessDescription"}


class CsvValidationError(ValueError):
    pass


def parse_csv(content: bytes, max_rows: int) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvValidationError("malformed_csv") from exc
    if not text.strip():
        raise CsvValidationError("empty_file")

    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_HEADERS - headers)
    if missing:
        raise CsvValidationError(f"missing_headers:{','.join(missing)}")

    rows = list(reader)
    if len(rows) > max_rows:
        raise CsvValidationError("file_too_large")
    return rows, sorted(headers - KNOWN_HEADERS)
