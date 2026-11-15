import hashlib
from dataclasses import replace
from datetime import datetime

from app.application.ports.clock import Clock
from app.domain.document import DocumentRecord
from app.domain.errors import DocumentAlreadyRegistered, DocumentNotFound, VersionConflict


class InMemoryRegistry:
    """Registry adapter that keeps everything in memory (development and tests).

    Replaced by the Web3.py adapter once the smart contract is ready; the core is unchanged.
    """

    def __init__(self, issuer: str, clock: Clock) -> None:
        self._issuer = issuer
        self._clock = clock
        self._records: dict[str, DocumentRecord] = {}
        self._authorized: set[str] = {issuer}
        self._transactions = 0

    @property
    def transaction_count(self) -> int:
        return self._transactions

    def authorize(self, issuer: str) -> None:
        self._authorized.add(issuer)

    def deauthorize(self, issuer: str) -> None:
        """Test helper: withdraw the issuer's authorization."""
        self._authorized.discard(issuer)

    def _next_transaction_hash(self) -> str:
        self._transactions += 1
        digest = hashlib.sha256(f"fake-transaction-{self._transactions}".encode()).hexdigest()
        return "0x" + digest

    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
        supersedes: str | None = None,
    ) -> str:
        if document_id in self._records:
            raise DocumentAlreadyRegistered(document_id)
        version = 1
        previous: DocumentRecord | None = None
        if supersedes is not None:
            previous = self._records.get(supersedes)
            if previous is None:
                raise DocumentNotFound(supersedes)
            if previous.superseded_by is not None:
                raise VersionConflict(supersedes, previous.superseded_by)
            version = previous.version + 1
        self._records[document_id] = DocumentRecord(
            document_hash=document_hash,
            issuer=self._issuer,
            issued_at=self._clock(),
            expires_at=expires_at,
            version=version,
        )
        if supersedes is not None and previous is not None:
            self._records[supersedes] = replace(previous, superseded_by=document_id)
        return self._next_transaction_hash()

    async def get(self, document_id: str) -> DocumentRecord | None:
        return self._records.get(document_id)

    async def revoke(self, document_id: str) -> str:
        record = self._records.get(document_id)
        if record is None:
            raise DocumentNotFound(document_id)
        self._records[document_id] = replace(record, revoked=True)
        return self._next_transaction_hash()

    async def is_issuer_authorized(self, issuer: str) -> bool:
        return issuer in self._authorized
