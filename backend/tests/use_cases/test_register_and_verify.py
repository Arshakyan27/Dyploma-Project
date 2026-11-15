from datetime import timedelta

import pytest

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.errors import RegistryUnavailable
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.domain.document import new_document_id
from app.domain.errors import InvalidDocumentFile, InvalidExpiryDate
from app.domain.status import Status
from tests.fakes import NOW, OTHER_PDF, SAMPLE_PDF, FailingRegistry, FakePdfStamper, MutableClock


async def test_registered_document_is_valid(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    result = await VerifyDocument(registry, stamper, clock).execute(registered.pdf)
    assert result.status is Status.VALID
    assert result.document_id == registered.document_id
    assert result.issuer == "issuer-1"
    assert result.issued_at == NOW
    assert result.version == 1
    assert registered.transaction_hash.startswith("0x")


async def test_one_changed_byte_is_modified(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    tampered = bytearray(registered.pdf)
    tampered[12] ^= 0x01
    result = await VerifyDocument(registry, stamper, clock).execute(bytes(tampered))
    assert result.status is Status.MODIFIED


async def test_other_file_with_the_same_id_is_modified(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    forged = stamper.stamp(OTHER_PDF, registered.document_id)
    result = await VerifyDocument(registry, stamper, clock).execute(forged)
    assert result.status is Status.MODIFIED


async def test_file_without_id_is_not_registered(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    result = await VerifyDocument(registry, stamper, clock).execute(SAMPLE_PDF)
    assert result.status is Status.NOT_REGISTERED
    assert result.document_id is None


async def test_unknown_id_is_not_registered(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    unknown = new_document_id()
    result = await VerifyDocument(registry, stamper, clock).execute(
        stamper.stamp(SAMPLE_PDF, unknown)
    )
    assert result.status is Status.NOT_REGISTERED
    assert result.document_id == unknown


async def test_document_after_expiry_is_expired(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    expires_at = NOW + timedelta(days=30)
    registered = await RegisterDocument(registry, stamper).execute(
        SAMPLE_PDF, expires_at=expires_at
    )
    verify = VerifyDocument(registry, stamper, clock)

    assert (await verify.execute(registered.pdf)).status is Status.VALID
    clock.now = expires_at
    assert (await verify.execute(registered.pdf)).status is Status.EXPIRED
    clock.now = expires_at + timedelta(days=1)
    assert (await verify.execute(registered.pdf)).status is Status.EXPIRED


async def test_withdrawn_authorization_gives_issuer_not_authorized(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    registry.deauthorize("issuer-1")
    result = await VerifyDocument(registry, stamper, clock).execute(registered.pdf)
    assert result.status is Status.ISSUER_NOT_AUTHORIZED


async def test_registry_failure_propagates_and_no_status_is_returned(
    stamper: FakePdfStamper, clock: MutableClock
) -> None:
    stamped = stamper.stamp(SAMPLE_PDF, new_document_id())
    with pytest.raises(RegistryUnavailable):
        await VerifyDocument(FailingRegistry(), stamper, clock).execute(stamped)
    with pytest.raises(RegistryUnavailable):
        await RegisterDocument(FailingRegistry(), stamper).execute(SAMPLE_PDF)
    with pytest.raises(RegistryUnavailable):
        await GetDocumentStatus(FailingRegistry(), clock).execute(new_document_id())


async def test_non_pdf_is_rejected(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    with pytest.raises(InvalidDocumentFile):
        await RegisterDocument(registry, stamper).execute(b"hello")
    with pytest.raises(InvalidDocumentFile):
        await VerifyDocument(registry, stamper, clock).execute(b"hello")


async def test_naive_expiry_date_is_rejected(
    registry: InMemoryRegistry, stamper: FakePdfStamper
) -> None:
    with pytest.raises(InvalidExpiryDate):
        await RegisterDocument(registry, stamper).execute(
            SAMPLE_PDF, expires_at=NOW.replace(tzinfo=None)
        )


async def test_status_by_id_does_not_check_the_file(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    status = GetDocumentStatus(registry, clock)

    assert (await status.execute(registered.document_id)).status is Status.VALID
    unknown = new_document_id()
    result = await status.execute(unknown)
    assert result.status is Status.NOT_REGISTERED
    assert result.document_id == unknown
