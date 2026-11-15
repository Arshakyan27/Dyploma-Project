from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import RegistryUnavailable
from app.domain.errors import (
    DocumentAlreadyRegistered,
    DocumentNotFound,
    InvalidDocumentFile,
    InvalidExpiryDate,
    VersionConflict,
)

_Handler = Callable[[Request, Exception], Awaitable[JSONResponse]]


def _handler_for(status_code: int) -> _Handler:
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handle


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DocumentNotFound, _handler_for(404))
    app.add_exception_handler(DocumentAlreadyRegistered, _handler_for(409))
    app.add_exception_handler(VersionConflict, _handler_for(409))
    app.add_exception_handler(InvalidDocumentFile, _handler_for(422))
    app.add_exception_handler(InvalidExpiryDate, _handler_for(422))
    app.add_exception_handler(RegistryUnavailable, _handler_for(503))
