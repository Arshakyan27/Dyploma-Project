import os

# app.main creates the application at import time, which needs an API key.
os.environ.setdefault("TECHDOC_API_KEY", "test-key")

import pytest  # noqa: E402

from app.adapters.outbound.in_memory_registry import InMemoryRegistry  # noqa: E402
from tests.fakes import NOW, FakePdfStamper, MutableClock  # noqa: E402


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock(NOW)


@pytest.fixture
def registry(clock: MutableClock) -> InMemoryRegistry:
    return InMemoryRegistry(issuer="issuer-1", clock=clock)


@pytest.fixture
def stamper() -> FakePdfStamper:
    return FakePdfStamper()
