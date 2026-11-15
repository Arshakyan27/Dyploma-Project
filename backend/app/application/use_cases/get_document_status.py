from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.application.use_cases._evaluation import VerificationResult, evaluate_document


class GetDocumentStatus:
    """Status by ID only (e.g. after scanning the QR code); the file hash is not checked."""

    def __init__(self, registry: Registry, clock: Clock) -> None:
        self._registry = registry
        self._clock = clock

    async def execute(self, document_id: str) -> VerificationResult:
        return await evaluate_document(self._registry, self._clock, document_id, file_hash=None)
