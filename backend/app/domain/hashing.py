import hashlib


def compute_hash(data: bytes) -> bytes:
    """SHA-256 of the file content (32 bytes)."""
    return hashlib.sha256(data).digest()
