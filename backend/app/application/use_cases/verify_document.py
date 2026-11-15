from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.application.use_cases._evaluation import VerificationResult, evaluate_document
from app.domain.document import ensure_pdf
from app.domain.hashing import compute_hash


class VerifyDocument:
    """Check a file: extract its ID, compare its hash with the registry, decide the status."""

    def __init__(self, registry: Registry, stamper: PdfStamper, clock: Clock) -> None:
        self._registry = registry
        self._stamper = stamper
        self._clock = clock

    async def execute(self, pdf: bytes) -> VerificationResult:
        ensure_pdf(pdf)
        document_id = self._stamper.extract_id(pdf)
        return await evaluate_document(
            self._registry, self._clock, document_id, file_hash=compute_hash(pdf)
        )
