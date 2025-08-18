from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from loguru import logger
try:
    from .schemas import (
		APIKeyResponse,
		APIKeyRegisterRequest,
		APIKeyValidateResponse,
		IngestRequest,
		IngestResponse,
		QueryRequest,
		QueryResponse,
    )
    from .auth import generate_api_key_server, register_api_key, require_api_key, validate_api_key
    from .ingest import save_upload_temp, ingest_document
    from .query import query_knowledgebase
except ImportError:
    from schemas import (
		APIKeyResponse,
		APIKeyRegisterRequest,
		APIKeyValidateResponse,
		IngestRequest,
		IngestResponse,
		QueryRequest,
		QueryResponse,
    )
    from auth import generate_api_key_server, register_api_key, require_api_key, validate_api_key
    from ingest import save_upload_temp, ingest_document
    from query import query_knowledgebase

from fastapi import BackgroundTasks
from .jobs import create_job, complete_job, fail_job, get_job, set_indexing_status

app = FastAPI(title="Doc KB", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health():
	return {"status": "ok"}


@app.post("/auth/generate", response_model=APIKeyResponse)
def auth_generate():
	key = generate_api_key_server()
	logger.info("Generated API key")
	return APIKeyResponse(api_key=key)


@app.post("/auth/register", response_model=APIKeyValidateResponse)
def auth_register(payload: APIKeyRegisterRequest):
	valid = register_api_key(payload.api_key)
	return APIKeyValidateResponse(valid=valid)


@app.get("/auth/validate", response_model=APIKeyValidateResponse)
def auth_validate(x_api_key: str = Depends(require_api_key)):
	return APIKeyValidateResponse(valid=validate_api_key(x_api_key))


@app.post("/upload")
def upload(file: UploadFile = File(...), x_api_key: str = Depends(require_api_key)):
	try:
		file_id, path = save_upload_temp(file, x_api_key)
		job_id = create_job("upload", file_id=file_id)
		# Upload completes immediately; mark completed
		complete_job(job_id, message="uploaded")
		return {"file_id": file_id, "path": path, "job_id": job_id}
	except Exception as exc:
		logger.exception("Upload failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, background: BackgroundTasks, x_api_key: str = Depends(require_api_key)):
	job_id = create_job("ingest", file_id=payload.file_id, document_name=payload.document_name)

	def _run_ingest():
		try:
			set_indexing_status(job_id, "processing")
			result = ingest_document(
				x_api_key=x_api_key,
				file_id=payload.file_id,
				document_name=payload.document_name,
				metadata=payload.metadata or {},
			)
			complete_job(job_id, message="ingested", num_chunks=result.num_chunks)
		except Exception as exc:
			fail_job(job_id, str(exc))

	background.add_task(_run_ingest)
	# Immediate response with job info placeholder
	return IngestResponse(document_name=payload.document_name, num_chunks=0, chunk_ids=[], job_id=job_id)


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest, x_api_key: str = Depends(require_api_key)):
	try:
		return query_knowledgebase(
			x_api_key=x_api_key,
			question=payload.question,
			top_k=payload.top_k or 5,
		)
	except Exception as exc:
		logger.exception("Query failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.get("/jobs/{job_id}")
def job_status(job_id: str, x_api_key: str = Depends(require_api_key)):
	info = get_job(job_id)
	if not info:
		raise HTTPException(status_code=404, detail="Job not found")
	return info