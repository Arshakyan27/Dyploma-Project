from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile

from app.adapters.inbound.api.deps import (
    SettingsDep,
    get_register_document,
    get_revoke_document,
    read_upload,
    require_api_key,
)
from app.adapters.inbound.api.schemas import RevokeResponse
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.domain.document import DOCUMENT_ID_PATTERN

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", status_code=201, response_class=Response)
async def register_document(
    file: Annotated[UploadFile, File(description="PDF document to register")],
    settings: SettingsDep,
    use_case: Annotated[RegisterDocument, Depends(get_register_document)],
    expires_at: Annotated[datetime | None, Form(description="ISO 8601 date with timezone")] = None,
    supersedes_id: Annotated[
        str | None,
        Form(pattern=DOCUMENT_ID_PATTERN, description="ID of the version this one replaces"),
    ] = None,
) -> Response:
    """Stamp the PDF with its ID and a QR code, register its hash, return the final PDF.

    The ID and the transaction hash are returned in X-Document-Id / X-Transaction-Hash.
    """
    data = await read_upload(file, settings)
    result = await use_case.execute(data, expires_at=expires_at, supersedes_id=supersedes_id)
    return Response(
        content=result.pdf,
        status_code=201,
        media_type="application/pdf",
        headers={
            "X-Document-Id": result.document_id,
            "X-Transaction-Hash": result.transaction_hash,
            "Content-Disposition": f'attachment; filename="{result.document_id}.pdf"',
        },
    )


@router.post("/{document_id}/revoke")
async def revoke_document(
    document_id: Annotated[str, Path(pattern=DOCUMENT_ID_PATTERN)],
    use_case: Annotated[RevokeDocument, Depends(get_revoke_document)],
) -> RevokeResponse:
    result = await use_case.execute(document_id)
    return RevokeResponse.from_result(result)
