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
    from .index import get_parsers, get_parser, create_index, get_index, get_all_indices
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
    from index import get_parsers, get_parser, create_index, get_index, get_all_indices

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





@app.post("/upload")
def upload(file: UploadFile = File(...)):
	try:
		# Use filename as document name
		document_name = file.filename or "unknown_file"
		job_name = f"Upload: {document_name}"
		
		file_id, path = save_upload_temp(file)
		job_id = create_job(
			job_type="upload", 
			file_id=file_id, 
			document_name=document_name,
			job_name=job_name,
			message=f"Uploading {document_name} with Docling OCR"
		)
		# Upload completes immediately; mark completed
		complete_job(job_id, message=f"Successfully uploaded {document_name}")
		return {
			"file_id": file_id, 
			"path": path, 
			"job_id": job_id, 
			"document_name": document_name
		}
	except Exception as exc:
		logger.exception("Upload failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, background: BackgroundTasks):
	# Validate index if provided
	if payload.index_id:
		index = get_index(payload.index_id)
		if not index:
			raise HTTPException(status_code=400, detail=f"Index '{payload.index_id}' not found")
	
	# Create descriptive job name
	job_name = f"Ingest: {payload.document_name}"
	if payload.index_id:
		index_name = get_index(payload.index_id).name if get_index(payload.index_id) else "Unknown Index"
		job_name += f" → {index_name}"
	
	job_id = create_job(
		job_type="ingest", 
		file_id=payload.file_id, 
		document_name=payload.document_name,
		job_name=job_name,
		message=f"Starting ingestion of {payload.document_name}"
	)

	def _run_ingest():
		try:
			set_indexing_status(job_id, "processing")
			result = ingest_document(
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
def query(payload: QueryRequest):
	try:
		# Validate index if provided
		if payload.index_id:
			index = get_index(payload.index_id)
			if not index:
				raise HTTPException(status_code=400, detail=f"Index '{payload.index_id}' not found")
		
		return query_knowledgebase(
			question=payload.question,
			top_k=payload.top_k or 5,
			index_id=payload.index_id,
		)
	except Exception as exc:
		logger.exception("Query failed")
		raise HTTPException(status_code=500, detail=str(exc))


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
	info = get_job(job_id)
	if not info:
		raise HTTPException(status_code=404, detail="Job not found")
	return info


@app.get("/parsers", response_model=List[Parser])
def list_parsers():
	"""Get all available parsers."""
	return get_parsers()


@app.get("/index", response_model=List[Index])
def list_index():
	"""Get all created index."""
	return get_all_indices()


@app.post("/index", response_model=IndexCreateResponse)
def create_new_index(payload: IndexCreateRequest, background: BackgroundTasks):
	"""Create a new index."""
	try:
		# Always use default parser (Docling OCR)
		index_id = create_index(payload.name, "docling_ocr")
		job_name = f"Create Index: {payload.name}"
		job_id = create_job(
			job_type="index_creation", 
			job_name=job_name,
			message=f"Creating index '{payload.name}' with Docling OCR and hybrid chunking"
		)
		
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


@app.get("/index/{index_id}", response_model=Index)
def get_index_details(index_id: str):
	"""Get details of a specific index."""
	index = get_index(index_id)
	if not index:
		raise HTTPException(status_code=404, detail="Index not found")
	return index


