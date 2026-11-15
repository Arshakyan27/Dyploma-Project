import hmac
from datetime import datetime

from app.domain.document import DocumentRecord
from app.domain.status import Status


def decide_status(
    record: DocumentRecord | None,
    *,
    file_hash: bytes | None,
    issuer_authorized: bool,
    now: datetime,
) -> Status:
    """Decide the verification status.

    Priority: NOT_REGISTERED -> MODIFIED -> REVOKED -> SUPERSEDED ->
    ISSUER_NOT_AUTHORIZED -> EXPIRED -> VALID.
    With `file_hash=None` (check by ID only) the MODIFIED step is skipped.
    `now` and all record dates must be timezone-aware.
    """
    if record is None:
        return Status.NOT_REGISTERED
    if file_hash is not None and not hmac.compare_digest(file_hash, record.document_hash):
        return Status.MODIFIED
    if record.revoked:
        return Status.REVOKED
    if record.superseded_by is not None:
        return Status.SUPERSEDED
    if not issuer_authorized:
        return Status.ISSUER_NOT_AUTHORIZED
    if record.expires_at is not None and now >= record.expires_at:
        return Status.EXPIRED
    return Status.VALID
