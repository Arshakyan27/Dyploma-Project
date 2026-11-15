import pytest

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.domain.document import new_document_id
from app.domain.errors import DocumentNotFound
from app.domain.status import Status
from tests.fakes import SAMPLE_PDF, FakePdfStamper, MutableClock


async def test_revoked_document_is_revoked(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    result = await RevokeDocument(registry).execute(registered.document_id)
    assert not result.already_revoked
    assert result.transaction_hash is not None

    verified = await VerifyDocument(registry, stamper, clock).execute(registered.pdf)
    assert verified.status is Status.REVOKED
    by_id = await GetDocumentStatus(registry, clock).execute(registered.document_id)
    assert by_id.status is Status.REVOKED


async def test_revoking_unknown_document_raises_not_found(registry: InMemoryRegistry) -> None:
    with pytest.raises(DocumentNotFound):
        await RevokeDocument(registry).execute(new_document_id())


async def test_second_revoke_succeeds_without_a_new_registry_write(
    registry: InMemoryRegistry, stamper: FakePdfStamper
) -> None:
    registered = await RegisterDocument(registry, stamper).execute(SAMPLE_PDF)
    revoke = RevokeDocument(registry)
    await revoke.execute(registered.document_id)
    writes_before = registry.transaction_count

    again = await revoke.execute(registered.document_id)
    assert again.already_revoked
    assert again.transaction_hash is None
    assert registry.transaction_count == writes_before
