import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.errors import InvalidDocumentFile, InvalidExpiryDate

DOCUMENT_ID_PATTERN = r"^[0-9a-f]{32}$"
_DOCUMENT_ID_RE = re.compile(DOCUMENT_ID_PATTERN)
_PDF_SIGNATURE = b"%PDF-"


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """What the registry stores about one registered version of a document.

    All datetimes are timezone-aware (UTC). `version` and `superseded_by` track the
    version chain: a new version supersedes the previous one.
    """

    document_hash: bytes
    issuer: str
    issued_at: datetime
    expires_at: datetime | None
    revoked: bool = False
    version: int = 1
    superseded_by: str | None = None


def new_document_id() -> str:
    """128-bit random ID: 32 hex chars, URL-safe and later fits into a bytes32."""
    return secrets.token_hex(16)


def is_valid_document_id(value: str) -> bool:
    return _DOCUMENT_ID_RE.fullmatch(value) is not None


def ensure_pdf(data: bytes) -> None:
    if not data.startswith(_PDF_SIGNATURE):
        raise InvalidDocumentFile("File is not a PDF document")


def ensure_utc(value: datetime) -> datetime:
    """Reject naive datetimes and normalise aware ones to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidExpiryDate("Date must include a timezone, e.g. 2030-01-01T00:00:00Z")
    return value.astimezone(UTC)
