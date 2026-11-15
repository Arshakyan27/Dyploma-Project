from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.document import (
    ensure_pdf,
    ensure_utc,
    is_valid_document_id,
    new_document_id,
)
from app.domain.errors import InvalidDocumentFile, InvalidExpiryDate


def test_new_document_id_is_32_hex_chars() -> None:
    document_id = new_document_id()
    assert len(document_id) == 32
    assert is_valid_document_id(document_id)


def test_new_document_ids_are_unique() -> None:
    assert len({new_document_id() for _ in range(100)}) == 100


@pytest.mark.parametrize("value", ["", "abc", "G" * 32, "a" * 31, "a" * 33, "A" * 32])
def test_invalid_document_id_formats(value: str) -> None:
    assert not is_valid_document_id(value)


def test_ensure_pdf_accepts_pdf_signature() -> None:
    ensure_pdf(b"%PDF-1.7\n...")


@pytest.mark.parametrize("data", [b"", b"hello", b"<html></html>", b" %PDF-1.4"])
def test_ensure_pdf_rejects_other_files(data: bytes) -> None:
    with pytest.raises(InvalidDocumentFile):
        ensure_pdf(data)


def test_ensure_utc_rejects_naive_datetime() -> None:
    with pytest.raises(InvalidExpiryDate):
        ensure_utc(datetime(2030, 1, 1))


def test_ensure_utc_converts_offset_to_utc() -> None:
    yerevan = timezone(timedelta(hours=4))
    result = ensure_utc(datetime(2030, 1, 1, 12, 0, tzinfo=yerevan))
    assert result == datetime(2030, 1, 1, 8, 0, tzinfo=UTC)
    assert result.utcoffset() == timedelta(0)
