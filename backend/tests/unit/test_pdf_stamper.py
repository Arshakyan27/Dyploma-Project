from io import BytesIO

import pytest
from pypdf import PdfReader

from app.adapters.outbound.pdf_stamper import ReportlabPdfStamper
from app.domain.document import new_document_id
from app.domain.errors import InvalidDocumentFile
from tests.fakes import make_real_pdf

stamper = ReportlabPdfStamper(base_url="https://docs.example.org/")


def test_extract_id_returns_the_stamped_id() -> None:
    document_id = new_document_id()
    stamped = stamper.stamp(make_real_pdf(), document_id)
    assert stamper.extract_id(stamped) == document_id


def test_stamped_file_is_still_a_pdf_with_the_same_pages() -> None:
    original = make_real_pdf(pages=3)
    stamped = stamper.stamp(original, new_document_id())
    assert stamped.startswith(b"%PDF-")
    assert len(PdfReader(BytesIO(stamped)).pages) == 3
    assert stamped != original


def test_file_without_id_returns_none() -> None:
    assert stamper.extract_id(make_real_pdf()) is None


def test_restamping_replaces_the_id() -> None:
    first, second = new_document_id(), new_document_id()
    restamped = stamper.stamp(stamper.stamp(make_real_pdf(), first), second)
    assert stamper.extract_id(restamped) == second


def test_verification_url_has_no_double_slash() -> None:
    document_id = new_document_id()
    expected = f"https://docs.example.org/api/v1/verifications/{document_id}"
    assert stamper.verification_url(document_id) == expected


@pytest.mark.parametrize("data", [b"%PDF-1.4 but not really a pdf", b"%PDF-"])
def test_unreadable_pdf_is_rejected(data: bytes) -> None:
    with pytest.raises(InvalidDocumentFile):
        stamper.stamp(data, new_document_id())
    with pytest.raises(InvalidDocumentFile):
        stamper.extract_id(data)
