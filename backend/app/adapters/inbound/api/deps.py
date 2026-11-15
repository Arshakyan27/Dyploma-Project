import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, UploadFile
from fastapi.security import APIKeyHeader

from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.settings import Settings

# The objects below are created once in main.py (composition root) and stored in app.state.


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_registry(request: Request) -> Registry:
    registry: Registry = request.app.state.registry
    return registry


def get_stamper(request: Request) -> PdfStamper:
    stamper: PdfStamper = request.app.state.stamper
    return stamper


def get_clock(request: Request) -> Clock:
    clock: Clock = request.app.state.clock
    return clock


SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[Registry, Depends(get_registry)]
StamperDep = Annotated[PdfStamper, Depends(get_stamper)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def get_register_document(registry: RegistryDep, stamper: StamperDep) -> RegisterDocument:
    return RegisterDocument(registry, stamper)


def get_verify_document(
    registry: RegistryDep, stamper: StamperDep, clock: ClockDep
) -> VerifyDocument:
    return VerifyDocument(registry, stamper, clock)


def get_document_status(registry: RegistryDep, clock: ClockDep) -> GetDocumentStatus:
    return GetDocumentStatus(registry, clock)


def get_revoke_document(registry: RegistryDep) -> RevokeDocument:
    return RevokeDocument(registry)


# auto_error=False: the 401 is raised explicitly, because the automatic status code
# for a missing key depends on the FastAPI version.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    settings: SettingsDep,
    api_key: Annotated[str | None, Security(_api_key_header)],
) -> None:
    expected = settings.api_key.get_secret_value().encode()
    if api_key is None or not secrets.compare_digest(api_key.encode(), expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


async def read_upload(file: UploadFile, settings: Settings) -> bytes:
    """Read an upload, refusing files larger than the limit without loading all of them."""
    limit = settings.max_file_size_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File is larger than {limit} bytes")
    return data
