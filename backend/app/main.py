# Disable ChromaDB telemetry globally
import os
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

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
from .schemas import RetrievedContext

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
				chunk_mode=payload.chunk_mode,
				chunk_size=payload.chunk_size,
				chunk_overlap=payload.chunk_overlap,
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
		# If no index_id provided, search across all collections
		if not payload.index_id:
			# Get all collections and search across them
			import chromadb
			from .ingest import _client
			
			client = _client()
			collections = client.list_collections()
			
			all_contexts = []
			all_answers = []
			
			for collection in collections:
				try:
					# Query each collection
					results = collection.query(
						query_texts=[payload.question],
						n_results=payload.top_k or 5
					)
					
					if results['ids'] and results['ids'][0]:
						for i, doc_id in enumerate(results['ids'][0]):
							context = RetrievedContext(
								chunk_id=doc_id,
								score=results['distances'][0][i] if results['distances'] else 0.0,
								text=results['documents'][0][i] if results['documents'] else "",
								metadata=results['metadatas'][0][i] if results['metadatas'] else {}
							)
							all_contexts.append(context)
				except Exception as e:
					# Skip collections with dimension mismatches or other issues
					if "Embedding dimension" in str(e):
						logger.info(f"Skipping collection {collection.name} due to dimension mismatch (old model)")
					else:
						logger.warning(f"Failed to query collection {collection.name}: {e}")
					continue
			
			# Sort by score and take top_k
			all_contexts.sort(key=lambda x: x.score, reverse=True)
			top_contexts = all_contexts[:payload.top_k or 5]
			
			# Generate answer from top contexts
			context_texts = [ctx.text for ctx in top_contexts]
			answer = f"Based on the search results, here are the most relevant findings:\n\n" + "\n\n".join(context_texts)
			
			return QueryResponse(answer=answer, contexts=top_contexts)
		else:
			# Validate index if provided
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


@app.get("/index/{index_id}/documents")
def get_index_documents(index_id: str):
	"""Get all documents in an index."""
	try:
		from .index import get_index
		index = get_index(index_id)
		if not index:
			raise HTTPException(status_code=404, detail="Index not found")
		
		# Get documents from ChromaDB collection
		import chromadb
		from .ingest import _client, _collection_name
		
		client = _client()
		collection_name = _collection_name("", index_id)
		collection = client.get_collection(name=collection_name)
		
		# Get all documents and group by document_name
		collection_info = collection.get()
		documents = {}
		
		if collection_info.get('metadatas'):
			for i, meta in enumerate(collection_info['metadatas']):
				if isinstance(meta, dict) and 'document_name' in meta:
					doc_name = meta['document_name']
					if doc_name not in documents:
						documents[doc_name] = {
							'id': doc_name,  # Use document name as ID
							'name': doc_name,
							'created_at': '',  # ChromaDB doesn't store creation time
							'num_chunks': 0,
							'index_id': index_id
						}
					documents[doc_name]['num_chunks'] += 1
		
		return list(documents.values())
	except Exception as exc:
		logger.exception("Failed to get index documents")
		raise HTTPException(status_code=500, detail=str(exc))


@app.get("/check-document-name/{index_id}/{document_name}")
def check_document_name(index_id: str, document_name: str):
	"""Check if a document name already exists in an index."""
	try:
		from .index import get_index
		index = get_index(index_id)
		if not index:
			raise HTTPException(status_code=404, detail="Index not found")
		
		# Check if document name exists in ChromaDB collection
		import chromadb
		from .ingest import _client, _collection_name
		
		client = _client()
		collection_name = _collection_name("", index_id)
		collection = client.get_collection(name=collection_name)
		
		# Query for documents with this name
		results = collection.query(
			query_texts=[""],  # Empty query to get all
			n_results=1000,
			where={"document_name": document_name}
		)
		
		exists = len(results['ids'][0]) > 0 if results['ids'] else False
		
		return {"exists": exists, "document_name": document_name, "index_id": index_id}
	except Exception as exc:
		logger.exception("Failed to check document name")
		raise HTTPException(status_code=500, detail=str(exc))


