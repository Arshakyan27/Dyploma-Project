from fastapi import FastAPI

from app.adapters.inbound.api import documents, verifications
from app.adapters.inbound.api.errors import register_error_handlers
from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.adapters.outbound.pdf_stamper import ReportlabPdfStamper
from app.adapters.outbound.system_clock import utc_now
from app.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Composition root: decides which adapter implements which port."""
    resolved = settings if settings is not None else Settings()  # pyright: ignore[reportCallIssue]

    app = FastAPI(title="Technical Document Integrity API", version="0.1.0")
    app.state.settings = resolved
    app.state.clock = utc_now
    app.state.registry = InMemoryRegistry(issuer="dev-issuer", clock=utc_now)
    app.state.stamper = ReportlabPdfStamper(base_url=resolved.public_base_url)

    register_error_handlers(app)
    app.include_router(documents.router)
    app.include_router(verifications.router)
    return app


app = create_app()
