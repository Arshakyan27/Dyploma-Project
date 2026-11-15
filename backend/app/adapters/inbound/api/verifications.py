from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile

from app.adapters.inbound.api.deps import (
    SettingsDep,
    get_document_status,
    get_verify_document,
    read_upload,
)
from app.adapters.inbound.api.schemas import VerificationResponse
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.verify_document import VerifyDocument
from app.domain.document import DOCUMENT_ID_PATTERN

# Verification is public: the QR code printed on a document points to the GET endpoint.
router = APIRouter(prefix="/api/v1/verifications", tags=["verifications"])


@router.post("")
async def verify_document(
    file: Annotated[UploadFile, File(description="PDF file to check")],
    settings: SettingsDep,
    use_case: Annotated[VerifyDocument, Depends(get_verify_document)],
) -> VerificationResponse:
    data = await read_upload(file, settings)
    return VerificationResponse.from_result(await use_case.execute(data))


@router.get("/{document_id}")
async def get_status(
    document_id: Annotated[str, Path(pattern=DOCUMENT_ID_PATTERN)],
    use_case: Annotated[GetDocumentStatus, Depends(get_document_status)],
) -> VerificationResponse:
    """Status by ID. An unknown ID is a normal result (NOT_REGISTERED), not a 404."""
    return VerificationResponse.from_result(await use_case.execute(document_id))
