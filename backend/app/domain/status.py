from enum import StrEnum


class Status(StrEnum):
    """Result of checking a technical document against the registry."""

    VALID = "VALID"
    MODIFIED = "MODIFIED"
    NOT_REGISTERED = "NOT_REGISTERED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"
    ISSUER_NOT_AUTHORIZED = "ISSUER_NOT_AUTHORIZED"
    EXPIRED = "EXPIRED"
