from datetime import datetime

from pydantic import BaseModel

from app.application.use_cases._evaluation import VerificationResult
from app.application.use_cases.revoke_document import RevokeResult
from app.domain.status import Status


class VerificationResponse(BaseModel):
    status: Status
    document_id: str | None
    issuer: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    version: int | None = None
    superseded_by: str | None = None

    @classmethod
    def from_result(cls, result: VerificationResult) -> "VerificationResponse":
        return cls(
            status=result.status,
            document_id=result.document_id,
            issuer=result.issuer,
            issued_at=result.issued_at,
            expires_at=result.expires_at,
            version=result.version,
            superseded_by=result.superseded_by,
        )


class RevokeResponse(BaseModel):
    document_id: str
    revoked: bool
    already_revoked: bool
    transaction_hash: str | None

    @classmethod
    def from_result(cls, result: RevokeResult) -> "RevokeResponse":
        return cls(
            document_id=result.document_id,
            revoked=True,
            already_revoked=result.already_revoked,
            transaction_hash=result.transaction_hash,
        )
