from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from loguru import logger
from typing import List
try:
    from .schemas import (
		APIKeyResponse,
		APIKeyRegisterRequest,
		APIKeyValidateResponse,
		IngestRequest,
		IngestResponse,
		QueryRequest,
		QueryResponse,
		Parser,
		Index,
		IndexCreateRequest,
		IndexCreateResponse,
    )
    from .auth import generate_api_key_server, register_api_key, require_api_key, validate_api_key
    from .ingest import save_upload_temp, ingest_document
    from .query import query_knowledgebase
    from .indices import get_parsers, get_parser, create_index, get_index, get_all_indices
except ImportError:
    from schemas import (
		APIKeyResponse,
		APIKeyRegisterRequest,
		APIKeyValidateResponse,
		IngestRequest,
		IngestResponse,
		QueryRequest,
		QueryResponse,
		Parser,
		Index,
		IndexCreateRequest,
		IndexCreateResponse,
    )
    from auth import generate_api_key_server, register_api_key, require_api_key, validate_api_key
    from ingest import save_upload_temp, ingest_document
    from query import query_knowledgebase
    from indices import get_parsers, get_parser, create_index, get_index, get_all_indices

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
def upload(file: UploadFile = File(...), parser_id: str = "default", x_api_key: str = Depends(require_api_key)):
	try:
		# Validate parser exists
		parser = get_parser(parser_id)
		if not parser:
			raise HTTPException(status_code=400, detail=f"Parser '{parser_id}' not found")
		
		file_id, path = save_upload_temp(file, x_api_key)
		job_id = create_job("upload", file_id=file_id, message=f"Uploaded with {parser.name}")
		# Upload completes immediately; mark completed
		complete_job(job_id, message=f"uploaded with {parser.name}")
		return {"file_id": file_id, "path": path, "job_id": job_id, "parser_id": parser_id}
	except Exception as exc:
		logger.exception("Upload failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, background: BackgroundTasks, x_api_key: str = Depends(require_api_key)):
	# Validate index if provided
	if payload.index_id:
		index = get_index(payload.index_id)
		if not index:
			raise HTTPException(status_code=400, detail=f"Index '{payload.index_id}' not found")
	
	job_id = create_job("ingest", file_id=payload.file_id, document_name=payload.document_name)

	def _run_ingest():
		try:
			set_indexing_status(job_id, "processing")
			result = ingest_document(
				x_api_key=x_api_key,
				file_id=payload.file_id,
				document_name=payload.document_name,
				metadata=payload.metadata or {},
				index_id=payload.index_id,
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
		# Validate index if provided
		if payload.index_id:
			index = get_index(payload.index_id)
			if not index:
				raise HTTPException(status_code=400, detail=f"Index '{payload.index_id}' not found")
		
		return query_knowledgebase(
			x_api_key=x_api_key,
			question=payload.question,
			top_k=payload.top_k or 5,
			index_id=payload.index_id,
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


@app.get("/parsers", response_model=List[Parser])
def list_parsers(x_api_key: str = Depends(require_api_key)):
	"""Get all available parsers."""
	return get_parsers()


@app.get("/indices", response_model=List[Index])
def list_indices(x_api_key: str = Depends(require_api_key)):
	"""Get all created indices."""
	return get_all_indices()


@app.post("/indices", response_model=IndexCreateResponse)
def create_new_index(payload: IndexCreateRequest, background: BackgroundTasks, x_api_key: str = Depends(require_api_key)):
	"""Create a new index."""
	# Validate parser exists
	parser = get_parser(payload.parser_id)
	if not parser:
		raise HTTPException(status_code=400, detail=f"Parser '{payload.parser_id}' not found")
	
	try:
		index_id = create_index(payload.name, payload.parser_id)
		job_id = create_job("index_creation", message=f"Created index '{payload.name}'")
		
		def _complete_index_creation():
			try:
				complete_job(job_id, message=f"Index '{payload.name}' created successfully")
			except Exception as exc:
				fail_job(job_id, str(exc))
		
		background.add_task(_complete_index_creation)
		
		return IndexCreateResponse(index_id=index_id, job_id=job_id)
	except Exception as exc:
		logger.exception("Index creation failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.get("/indices/{index_id}", response_model=Index)
def get_index_details(index_id: str, x_api_key: str = Depends(require_api_key)):
	"""Get details of a specific index."""
	index = get_index(index_id)
	if not index:
		raise HTTPException(status_code=404, detail="Index not found")
	return index


# Fix the auth endpoints to match frontend expectations
@app.post("/auth/generate-key", response_model=APIKeyResponse)
def auth_generate_key():
	key = generate_api_key_server()
	logger.info("Generated API key")
	return APIKeyResponse(api_key=key)


@app.post("/auth/register-key", response_model=APIKeyValidateResponse)
def auth_register_key(payload: APIKeyRegisterRequest):
	valid = register_api_key(payload.api_key)
	return APIKeyValidateResponse(valid=valid)