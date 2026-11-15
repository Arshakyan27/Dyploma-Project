from io import BytesIO

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from pypdf.errors import PyPdfError
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.domain.document import is_valid_document_id
from app.domain.errors import InvalidDocumentFile

METADATA_KEY = "/TechDocId"
QR_SIZE = 22 * mm
MARGIN = 10 * mm


class ReportlabPdfStamper:
    """Puts a QR code (link to the verification endpoint) on the first page and writes the
    document ID into the PDF metadata.

    Libraries: pypdf (BSD) for reading/merging and reportlab (BSD) for drawing, including
    its built-in QR generator, so no AGPL dependency and no extra QR package is needed.
    The ID is read back from the metadata only; the QR image itself is not decoded.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def verification_url(self, document_id: str) -> str:
        return f"{self._base_url}/api/v1/verifications/{document_id}"

    def stamp(self, pdf: bytes, document_id: str) -> bytes:
        reader = self._open(pdf)
        writer = PdfWriter(clone_from=reader)
        if len(writer.pages) == 0:
            raise InvalidDocumentFile("PDF document has no pages")
        page = writer.pages[0]
        box = page.mediabox
        overlay = self._build_overlay(
            float(box.width), float(box.height), self.verification_url(document_id)
        )
        # NOTE: pages with a /Rotate entry get the QR rotated together with the page.
        page.merge_transformed_page(
            overlay, Transformation().translate(float(box.left), float(box.bottom))
        )
        writer.add_metadata({METADATA_KEY: document_id})
        output = BytesIO()
        writer.write(output)
        return output.getvalue()

    def extract_id(self, pdf: bytes) -> str | None:
        reader = self._open(pdf)
        metadata = reader.metadata
        if metadata is None:
            return None
        value = metadata.get(METADATA_KEY)
        if value is None:
            return None
        candidate = str(value)
        return candidate if is_valid_document_id(candidate) else None

    @staticmethod
    def _open(pdf: bytes) -> PdfReader:
        try:
            reader = PdfReader(BytesIO(pdf))
            if reader.is_encrypted:
                raise InvalidDocumentFile("Encrypted PDF files are not supported")
            len(reader.pages)  # noqa: B018 - forces parsing of the page tree
        except (PyPdfError, ValueError, KeyError, TypeError) as exc:
            raise InvalidDocumentFile("File is not a readable PDF document") from exc
        return reader

    @staticmethod
    def _build_overlay(width: float, height: float, url: str) -> PageObject:
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(width, height))
        widget = QrCodeWidget(url, barLevel="M")
        x0, y0, x1, y1 = widget.getBounds()
        drawing = Drawing(
            QR_SIZE,
            QR_SIZE,
            transform=[QR_SIZE / (x1 - x0), 0, 0, QR_SIZE / (y1 - y0), 0, 0],
        )
        drawing.add(widget)
        x = width - MARGIN - QR_SIZE
        renderPDF.draw(drawing, pdf_canvas, x, MARGIN + 8)
        pdf_canvas.setFont("Helvetica", 6)
        pdf_canvas.drawCentredString(x + QR_SIZE / 2, MARGIN, "Scan to verify")
        pdf_canvas.save()
        buffer.seek(0)
        return PdfReader(buffer).pages[0]
