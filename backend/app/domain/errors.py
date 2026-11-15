class DomainError(Exception):
    """Base class for errors raised by the domain and application core."""


class DocumentNotFound(DomainError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document {document_id} is not registered")
        self.document_id = document_id


class DocumentAlreadyRegistered(DomainError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document {document_id} is already registered")
        self.document_id = document_id


class VersionConflict(DomainError):
    """A new version must supersede the latest version of a document."""

    def __init__(self, document_id: str, superseded_by: str) -> None:
        super().__init__(f"Document {document_id} is already superseded by {superseded_by}")
        self.document_id = document_id
        self.superseded_by = superseded_by


class InvalidDocumentFile(DomainError):
    """The uploaded file is not a readable PDF document."""


class InvalidExpiryDate(DomainError):
    """Dates must be timezone-aware."""
