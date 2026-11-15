import re
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from pydantic import SecretStr

from app.adapters.inbound.api.deps import get_registry, get_stamper
from app.main import create_app
from app.settings import Settings
from tests.fakes import OTHER_PDF, SAMPLE_PDF, FailingRegistry, FakePdfStamper, make_real_pdf

API_KEY = "secret"
HEADERS = {"X-API-Key": API_KEY}
UNKNOWN_ID = "0" * 32


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_key=SecretStr(API_KEY),
        public_base_url="http://testserver",
        max_file_size_bytes=100_000,
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    application.dependency_overrides[get_stamper] = FakePdfStamper
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def real_client(settings: Settings) -> Iterator[TestClient]:
    """Client without the fake stamper: the real PDF + QR adapter is used."""
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def register(client: TestClient, pdf: bytes = SAMPLE_PDF, **form: str) -> Response:
    return client.post(
        "/api/v1/documents",
        headers=HEADERS,
        files={"file": ("spec.pdf", pdf, "application/pdf")},
        data=form,
    )


def verify(client: TestClient, pdf: bytes) -> Response:
    return client.post(
        "/api/v1/verifications", files={"file": ("spec.pdf", pdf, "application/pdf")}
    )


def test_full_cycle_register_verify_revoke_verify(client: TestClient) -> None:
    registered = register(client)
    assert registered.status_code == 201
    assert registered.headers["content-type"] == "application/pdf"
    document_id = registered.headers["x-document-id"]
    assert re.fullmatch(r"[0-9a-f]{32}", document_id)
    assert registered.headers["x-transaction-hash"].startswith("0x")

    checked = verify(client, registered.content)
    assert checked.status_code == 200
    assert checked.json()["status"] == "VALID"
    assert checked.json()["document_id"] == document_id
    assert checked.json()["version"] == 1

    assert client.get(f"/api/v1/verifications/{document_id}").json()["status"] == "VALID"

    revoked = client.post(f"/api/v1/documents/{document_id}/revoke", headers=HEADERS)
    assert revoked.status_code == 200
    assert revoked.json()["already_revoked"] is False

    assert verify(client, registered.content).json()["status"] == "REVOKED"
    assert client.get(f"/api/v1/verifications/{document_id}").json()["status"] == "REVOKED"


def test_modified_file_is_reported_as_modified(client: TestClient) -> None:
    registered = register(client)
    document_id = registered.headers["x-document-id"]
    forged = FakePdfStamper().stamp(OTHER_PDF, document_id)
    assert verify(client, forged).json()["status"] == "MODIFIED"


def test_unknown_id_is_200_not_registered(client: TestClient) -> None:
    response = client.get(f"/api/v1/verifications/{UNKNOWN_ID}")
    assert response.status_code == 200
    assert response.json()["status"] == "NOT_REGISTERED"
    assert response.json()["document_id"] == UNKNOWN_ID


def test_malformed_id_in_path_is_422(client: TestClient) -> None:
    assert client.get("/api/v1/verifications/not-an-id").status_code == 422


def test_new_version_supersedes_old_one(client: TestClient) -> None:
    first = register(client).headers["x-document-id"]
    second = register(client, OTHER_PDF, supersedes_id=first).headers["x-document-id"]
    old = client.get(f"/api/v1/verifications/{first}").json()
    assert old["status"] == "SUPERSEDED"
    assert old["superseded_by"] == second
    assert client.get(f"/api/v1/verifications/{second}").json()["version"] == 2


def test_missing_and_wrong_api_key_are_401(client: TestClient) -> None:
    files = {"file": ("spec.pdf", SAMPLE_PDF, "application/pdf")}
    assert client.post("/api/v1/documents", files=files).status_code == 401
    wrong = {"X-API-Key": "wrong"}
    assert client.post("/api/v1/documents", files=files, headers=wrong).status_code == 401
    revoke_url = f"/api/v1/documents/{UNKNOWN_ID}/revoke"
    assert client.post(revoke_url).status_code == 401
    assert client.post(revoke_url, headers=wrong).status_code == 401


def test_non_pdf_is_422(client: TestClient) -> None:
    assert register(client, b"just text").status_code == 422
    assert verify(client, b"just text").status_code == 422


def test_naive_expiry_date_is_422_and_aware_is_accepted(client: TestClient) -> None:
    assert register(client, expires_at="2030-01-01T00:00:00").status_code == 422
    assert register(client, expires_at="2030-01-01T00:00:00Z").status_code == 201


def test_too_large_file_is_413(client: TestClient) -> None:
    assert register(client, b"%PDF-" + b"0" * 200_000).status_code == 413
    assert verify(client, b"%PDF-" + b"0" * 200_000).status_code == 413


def test_revoking_unknown_document_is_404(client: TestClient) -> None:
    response = client.post(f"/api/v1/documents/{UNKNOWN_ID}/revoke", headers=HEADERS)
    assert response.status_code == 404


def test_unavailable_registry_is_503(app: FastAPI, client: TestClient) -> None:
    stamped = FakePdfStamper().stamp(SAMPLE_PDF, UNKNOWN_ID)
    app.dependency_overrides[get_registry] = FailingRegistry
    assert verify(client, stamped).status_code == 503
    assert register(client).status_code == 503
    assert client.get(f"/api/v1/verifications/{UNKNOWN_ID}").status_code == 503


def test_real_pdf_with_qr_is_valid_after_registration(real_client: TestClient) -> None:
    registered = register(real_client, make_real_pdf())
    assert registered.status_code == 201
    assert registered.content.startswith(b"%PDF-")
    checked = verify(real_client, registered.content)
    assert checked.json()["status"] == "VALID"
    assert checked.json()["document_id"] == registered.headers["x-document-id"]
