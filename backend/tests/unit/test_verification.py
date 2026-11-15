import dataclasses
from datetime import timedelta

import pytest

from app.domain.document import DocumentRecord
from app.domain.status import Status
from app.domain.verification import decide_status
from tests.fakes import NOW

FILE_HASH = b"\x01" * 32
OTHER_HASH = b"\x02" * 32
NEWER_ID = "b" * 32


def make_record(**changes: object) -> DocumentRecord:
    base = DocumentRecord(
        document_hash=FILE_HASH,
        issuer="issuer-1",
        issued_at=NOW - timedelta(days=1),
        expires_at=None,
    )
    return dataclasses.replace(base, **changes)


@pytest.mark.parametrize(
    ("record", "file_hash", "authorized", "expected"),
    [
        (None, FILE_HASH, True, Status.NOT_REGISTERED),
        (make_record(), FILE_HASH, True, Status.VALID),
        (make_record(), OTHER_HASH, True, Status.MODIFIED),
        (make_record(revoked=True), FILE_HASH, True, Status.REVOKED),
        (make_record(superseded_by=NEWER_ID), FILE_HASH, True, Status.SUPERSEDED),
        (make_record(), FILE_HASH, False, Status.ISSUER_NOT_AUTHORIZED),
        (make_record(expires_at=NOW - timedelta(seconds=1)), FILE_HASH, True, Status.EXPIRED),
        (make_record(expires_at=NOW + timedelta(seconds=1)), FILE_HASH, True, Status.VALID),
    ],
    ids=[
        "not-registered",
        "valid",
        "modified",
        "revoked",
        "superseded",
        "issuer-not-authorized",
        "expired",
        "not-yet-expired",
    ],
)
def test_each_status(
    record: DocumentRecord | None, file_hash: bytes, authorized: bool, expected: Status
) -> None:
    status = decide_status(record, file_hash=file_hash, issuer_authorized=authorized, now=NOW)
    assert status is expected


def test_expiry_boundary_counts_as_expired() -> None:
    record = make_record(expires_at=NOW)
    status = decide_status(record, file_hash=FILE_HASH, issuer_authorized=True, now=NOW)
    assert status is Status.EXPIRED


@pytest.mark.parametrize(
    ("record", "file_hash", "authorized", "expected"),
    [
        # Priority: NOT_REGISTERED > MODIFIED > REVOKED > SUPERSEDED
        #           > ISSUER_NOT_AUTHORIZED > EXPIRED > VALID
        (make_record(revoked=True), OTHER_HASH, True, Status.MODIFIED),
        (make_record(revoked=True, superseded_by=NEWER_ID), FILE_HASH, True, Status.REVOKED),
        (make_record(superseded_by=NEWER_ID), FILE_HASH, False, Status.SUPERSEDED),
        (
            make_record(expires_at=NOW - timedelta(days=1)),
            FILE_HASH,
            False,
            Status.ISSUER_NOT_AUTHORIZED,
        ),
        (make_record(revoked=True), FILE_HASH, False, Status.REVOKED),
    ],
)
def test_status_priority(
    record: DocumentRecord, file_hash: bytes, authorized: bool, expected: Status
) -> None:
    status = decide_status(record, file_hash=file_hash, issuer_authorized=authorized, now=NOW)
    assert status is expected


def test_check_by_id_skips_hash_comparison() -> None:
    assert (
        decide_status(make_record(), file_hash=None, issuer_authorized=True, now=NOW)
        is Status.VALID
    )
    assert (
        decide_status(make_record(revoked=True), file_hash=None, issuer_authorized=True, now=NOW)
        is Status.REVOKED
    )
