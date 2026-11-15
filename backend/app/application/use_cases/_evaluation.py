from dataclasses import dataclass
from datetime import datetime

from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.domain.status import Status
from app.domain.verification import decide_status


@dataclass(frozen=True, slots=True)
class VerificationResult:
    status: Status
    document_id: str | None
    issuer: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    version: int | None = None
    superseded_by: str | None = None


async def evaluate_document(
    registry: Registry,
    clock: Clock,
    document_id: str | None,
    file_hash: bytes | None,
) -> VerificationResult:
    """Shared part of VerifyDocument and GetDocumentStatus."""
    if document_id is None:
        return VerificationResult(status=Status.NOT_REGISTERED, document_id=None)
    record = await registry.get(document_id)
    if record is None:
        return VerificationResult(status=Status.NOT_REGISTERED, document_id=document_id)
    issuer_authorized = await registry.is_issuer_authorized(record.issuer)
    status = decide_status(
        record,
        file_hash=file_hash,
        issuer_authorized=issuer_authorized,
        now=clock(),
    )
    return VerificationResult(
        status=status,
        document_id=document_id,
        issuer=record.issuer,
        issued_at=record.issued_at,
        expires_at=record.expires_at,
        version=record.version,
        superseded_by=record.superseded_by,
    )
