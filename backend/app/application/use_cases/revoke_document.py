from dataclasses import dataclass

from app.application.ports.registry import Registry
from app.domain.errors import DocumentNotFound


@dataclass(frozen=True, slots=True)
class RevokeResult:
    document_id: str
    already_revoked: bool
    transaction_hash: str | None


class RevokeDocument:
    def __init__(self, registry: Registry) -> None:
        self._registry = registry

    async def execute(self, document_id: str) -> RevokeResult:
        record = await self._registry.get(document_id)
        if record is None:
            raise DocumentNotFound(document_id)
        if record.revoked:
            # Idempotent: nothing is written to the registry a second time.
            return RevokeResult(document_id, already_revoked=True, transaction_hash=None)
        transaction_hash = await self._registry.revoke(document_id)
        return RevokeResult(document_id, already_revoked=False, transaction_hash=transaction_hash)
