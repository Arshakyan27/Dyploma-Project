# techdoc-integrity — backend core

Integrity and authenticity control for technical documents. This stage covers everything
except the blockchain and RAG parts: hexagonal core, in-memory registry, PDF stamping with
a QR code, FastAPI endpoints and tests. The registry is an in-memory adapter for now; the
Web3.py adapter for the smart contract replaces it later without touching the core.

## Layout

```
app/
  domain/        status, DocumentRecord, hashing, decide_status, domain errors (stdlib only)
  application/   errors, ports (Registry, PdfStamper, Clock), use cases
  adapters/
    inbound/api/   FastAPI: deps, schemas, error handlers, routers
    outbound/      in-memory registry, pypdf+reportlab stamper, system clock
  settings.py    pydantic-settings (TECHDOC_* env vars / .env)
  main.py        composition root (which adapter implements which port)
tests/           unit/, use_cases/, api/, fakes.py
```

## Run

```
cp .env.example .env      # set TECHDOC_API_KEY
just check                # ruff + basedpyright
just test                 # pytest
just run                  # fastapi dev app/main.py
```

## Endpoints

| Method | Path | Auth | Result |
|---|---|---|---|
| POST | /api/v1/documents | X-API-Key | 201, stamped PDF; `X-Document-Id`, `X-Transaction-Hash` headers |
| POST | /api/v1/documents/{id}/revoke | X-API-Key | 200; 404 if the ID is unknown |
| POST | /api/v1/verifications | public | 200, status of the uploaded file |
| GET | /api/v1/verifications/{id} | public | 200, status by ID (unknown ID: `NOT_REGISTERED`) |

`POST /api/v1/documents` accepts optional form fields `expires_at` (ISO 8601 with timezone)
and `supersedes_id` (ID of the version being replaced).

## Statuses and priority

`NOT_REGISTERED` > `MODIFIED` > `REVOKED` > `SUPERSEDED` > `ISSUER_NOT_AUTHORIZED` >
`EXPIRED` > `VALID`. Check by ID only skips the `MODIFIED` step.

Errors: `DocumentNotFound` 404, `DocumentAlreadyRegistered`/`VersionConflict` 409,
`InvalidDocumentFile`/`InvalidExpiryDate` 422, `RegistryUnavailable` 503, file larger than
`max_file_size_bytes` 413, missing or wrong key 401.

## Known limits

- The document ID is stored in the PDF metadata (`/TechDocId`); the QR image is not decoded.
  A forged copy that only reproduces the QR picture is `NOT_REGISTERED`; a file that carries
  another file's ID is `MODIFIED`.
- Pages with a `/Rotate` entry get the QR rotated with the page.
- Encrypted PDFs are rejected (422).
