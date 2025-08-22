## Doc KB - End-to-end Knowledgebase

Dockerized React + FastAPI application for uploading PDFs, parsing with OCR, hybrid chunking, embedding with Jina v3, and storing in ChromaDB. Includes REST APIs and a simple UI.

### Quick start

1. Build and run

```bash
docker compose up --build
```

2. Open UI at `http://localhost:5173`

3. Generate API key (UI header), Register, then upload a PDF, provide a document name, and click Ingest. Ask questions in the query box.

### REST API

- `POST /auth/generate` → `{ api_key }`
- `POST /auth/register` body `{ api_key }`
- `GET /auth/validate` header `x-api-key: <key>`
- `POST /upload` form-data `file=@doc.pdf` header `x-api-key`
- `POST /ingest` JSON `{ file_id, document_name, metadata? }` header `x-api-key`
- `POST /query` JSON `{ question, top_k? }` header `x-api-key`

OpenAPI docs at `http://localhost:8000/docs` after services are up.

### Notes

- OCR uses Tesseract via `pytesseract` if no text layer is found.
- Chunking capped at 8k tokens with overlap.
- Embeddings via `jinaai/jina-embeddings-v3-small` using transformers; adjust with `MODEL_NAME`.
- Chroma runs as a service with persistent volume.

# Ai-Knowledgebase

### v1 API (Production-ready, versioned)

Base URL: `http://localhost:8000/v1`

- Projects
  - `POST /projects` body `{ name, description? }` → `{ projectId, name }`
  - `GET /projects` → `[{ projectId, name }]`
  - `GET /projects/{projectId}` → `{ projectId, name, description }`
  - `PUT /projects/{projectId}` body `{ name, description? }` → `{ projectId, name }`
  - `DELETE /projects/{projectId}` → `{ status: "deleted", projectId }`

- Files
  - `POST /projects/{projectId}/files` form-data `file=@doc.pdf` → `{ fileId, projectId, status: "uploaded" }`
  - `GET /projects/{projectId}/files` → `[{ fileId, filename }]`
  - `GET /projects/{projectId}/files/{fileId}` → `{ fileId, filename, status }`
  - `DELETE /projects/{projectId}/files/{fileId}` → `{ status: "deleted", fileId }`

- Indexes
  - `POST /projects/{projectId}/indexes` body `{ name, embeddingModel? }` → `{ indexId, projectId, name }`
  - `GET /projects/{projectId}/indexes` → `[{ indexId, name }]`
  - `GET /projects/{projectId}/indexes/{indexId}` → `{ indexId, projectId, name }`
  - `PUT /projects/{projectId}/indexes/{indexId}` body `{ name }` → `{ indexId, name }`
  - `DELETE /projects/{projectId}/indexes/{indexId}` → `{ status: "deleted", indexId }`
  - `POST /projects/{projectId}/indexes/{indexId}/ingest` body `{ fileId }` → `{ status: "indexed", fileId, indexId, chunks }`

- Querying
  - `POST /projects/{projectId}/indexes/{indexId}/query` body `{ query, top_k }` → `{ query, answers: [{ text, source }] }`

- Testing
  - `POST /query/test` form-data `file=@doc.pdf`, `query=...` → `{ answers: [{ text }] }`