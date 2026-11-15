from datetime import datetime
from typing import Protocol

from app.domain.document import DocumentRecord


class Registry(Protocol):
    """Port to the document registry (smart contract in production)."""

    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
        supersedes: str | None = None,
    ) -> str:
        """Register a document version. Returns the transaction hash.

        The issuer is not a parameter: the registry takes it from the server signing key
        (`msg.sender` in the contract). If `supersedes` is given, the previous version is
        marked as superseded in the same operation.
        """
        ...

    async def get(self, document_id: str) -> DocumentRecord | None: ...

    async def revoke(self, document_id: str) -> str:
        """Revoke a document. Returns the transaction hash."""
        ...

    async def is_issuer_authorized(self, issuer: str) -> bool: ...
