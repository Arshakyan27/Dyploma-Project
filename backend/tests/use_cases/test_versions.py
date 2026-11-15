import pytest

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.domain.document import new_document_id
from app.domain.errors import DocumentNotFound, VersionConflict
from app.domain.status import Status
from tests.fakes import OTHER_PDF, SAMPLE_PDF, FakePdfStamper, MutableClock


async def test_new_version_supersedes_the_old_one(
    registry: InMemoryRegistry, stamper: FakePdfStamper, clock: MutableClock
) -> None:
    register = RegisterDocument(registry, stamper)
    verify = VerifyDocument(registry, stamper, clock)

    first = await register.execute(SAMPLE_PDF)
    second = await register.execute(OTHER_PDF, supersedes_id=first.document_id)

    old = await verify.execute(first.pdf)
    assert old.status is Status.SUPERSEDED
    assert old.version == 1
    assert old.superseded_by == second.document_id

    new = await verify.execute(second.pdf)
    assert new.status is Status.VALID
    assert new.version == 2
    assert new.superseded_by is None


async def test_superseding_unknown_document_raises_not_found(
    registry: InMemoryRegistry, stamper: FakePdfStamper
) -> None:
    with pytest.raises(DocumentNotFound):
        await RegisterDocument(registry, stamper).execute(
            SAMPLE_PDF, supersedes_id=new_document_id()
        )


async def test_only_the_latest_version_can_be_superseded(
    registry: InMemoryRegistry, stamper: FakePdfStamper
) -> None:
    register = RegisterDocument(registry, stamper)
    first = await register.execute(SAMPLE_PDF)
    await register.execute(OTHER_PDF, supersedes_id=first.document_id)
    with pytest.raises(VersionConflict):
        await register.execute(OTHER_PDF, supersedes_id=first.document_id)
