"""Test doubles and sample data."""

from datetime import UTC, datetime, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.application.errors import RegistryUnavailable
from app.domain.document import DocumentRecord

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

# Minimal "PDFs" for tests that use FakePdfStamper (only the %PDF- signature matters there).
SAMPLE_PDF = b"%PDF-1.4\n% technical specification, revision A\n%%EOF\n"
OTHER_PDF = b"%PDF-1.4\n% technical specification, revision B\n%%EOF\n"


def make_real_pdf(text: str = "Technical specification", pages: int = 1) -> bytes:
    """A real one-or-more-page PDF for tests of the actual stamper."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    for number in range(pages):
        pdf_canvas.drawString(72, 750, f"{text} - page {number + 1}")
        pdf_canvas.showPage()
    pdf_canvas.save()
    return buffer.getvalue()


class MutableClock:
    """Fixed clock that tests can move."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


class FakePdfStamper:
    """Appends an ID marker to the bytes and looks for it in extract_id."""

    _MARKER = b"\n%%DOC-ID:"

    def stamp(self, pdf: bytes, document_id: str) -> bytes:
        return pdf + self._MARKER + document_id.encode() + b"\n"

    def extract_id(self, pdf: bytes) -> str | None:
        start = pdf.rfind(self._MARKER)
        if start == -1:
            return None
        start += len(self._MARKER)
        end = pdf.find(b"\n", start)
        return pdf[start:end].decode()


class FailingRegistry:
    """Every call fails, as if the blockchain node were unreachable."""

    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
        supersedes: str | None = None,
    ) -> str:
        raise RegistryUnavailable("registry is down")

    async def get(self, document_id: str) -> DocumentRecord | None:
        raise RegistryUnavailable("registry is down")

    async def revoke(self, document_id: str) -> str:
        raise RegistryUnavailable("registry is down")

    async def is_issuer_authorized(self, issuer: str) -> bool:
        raise RegistryUnavailable("registry is down")
