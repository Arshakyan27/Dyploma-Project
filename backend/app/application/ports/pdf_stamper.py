from typing import Protocol


class PdfStamper(Protocol):
    """Port for putting the document ID into a PDF (QR code + metadata) and reading it back."""

    def stamp(self, pdf: bytes, document_id: str) -> bytes: ...

    def extract_id(self, pdf: bytes) -> str | None: ...
