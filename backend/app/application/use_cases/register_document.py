from dataclasses import dataclass
from datetime import datetime

from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.domain.document import ensure_pdf, ensure_utc, new_document_id
from app.domain.hashing import compute_hash


@dataclass(frozen=True, slots=True)
class RegisterResult:
    document_id: str
    document_hash: bytes
    transaction_hash: str
    pdf: bytes


class RegisterDocument:
    def __init__(self, registry: Registry, stamper: PdfStamper) -> None:
        self._registry = registry
        self._stamper = stamper

    async def execute(
        self,
        pdf: bytes,
        *,
        expires_at: datetime | None = None,
        supersedes_id: str | None = None,
    ) -> RegisterResult:
        ensure_pdf(pdf)
        expires = ensure_utc(expires_at) if expires_at is not None else None
        document_id = new_document_id()
        stamped = self._stamper.stamp(pdf, document_id)
        # The hash is computed over the FINAL file (with QR and ID), the one that is issued.
        document_hash = compute_hash(stamped)
        transaction_hash = await self._registry.register(
            document_id, document_hash, expires, supersedes=supersedes_id
        )
        return RegisterResult(
            document_id=document_id,
            document_hash=document_hash,
            transaction_hash=transaction_hash,
            pdf=stamped,
        )
