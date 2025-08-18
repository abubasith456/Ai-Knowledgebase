# Disable ChromaDB telemetry globally
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from fastapi import UploadFile
from loguru import logger
import chromadb

try:
	from .schemas import IngestResponse, Chunk, ChunkMode
	from .parsing import parse_pdf_with_docling
	from .chunking import hybrid_chunk_document
	from .embeddings import get_embedding_function
	from .chroma_client import get_chroma_client
except ImportError:
	from schemas import IngestResponse, Chunk, ChunkMode
	from parsing import parse_pdf_with_docling
	from chunking import hybrid_chunk_document
	from embeddings import get_embedding_function
	from chroma_client import get_chroma_client


# Use a more reliable path for uploads
try:
    DATA_DIR = Path(os.environ.get("CHROMA_DATA_DIR") or "./data")
    UPLOAD_DIR = DATA_DIR / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    # Fallback to temp directory if we can't create the default path
    import tempfile
    UPLOAD_DIR = Path(tempfile.gettempdir()) / "doc_kb_uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _client() -> chromadb.Client:
	"""Get ChromaDB client with telemetry disabled."""
	return get_chroma_client()


def _sanitize_name(name: str) -> str:
	# Keep alphanumeric, underscore, hyphen; replace others with '_'
	import re
	name = re.sub(r"[^A-Za-z0-9_-]", "_", name)
	# Ensure starts/ends alphanumeric
	name = re.sub(r"^[^A-Za-z0-9]+", "", name)
	name = re.sub(r"[^A-Za-z0-9]+$", "", name)
	# Bound length 3..63; trim if needed
	if len(name) < 3:
		name = (name + "___")[:3]
	return name[:63]


def _collection_name(document_name: str, job_id: str) -> str:
	"""Create collection name based on document name and job ID."""
	prefix = os.environ.get("COLLECTION_PREFIX", "kb_")
	
	# Sanitize document name for collection name
	doc_part = _sanitize_name(document_name)
	
	# Create unique collection name with job ID
	collection_name = f"{prefix}{doc_part}_{job_id[:8]}"
	
	return _sanitize_name(collection_name)


def save_upload_temp(file: UploadFile) -> Tuple[str, str]:
	file_id = str(uuid.uuid4())
	# Use default user directory since no authentication
	user_dir = UPLOAD_DIR / "default_user"
	user_dir.mkdir(parents=True, exist_ok=True)
	path = user_dir / f"{file_id}_{file.filename}"
	with path.open("wb") as f:
		content = file.file.read()
		f.write(content)
	logger.info(f"Saved upload to {path}")
	return file_id, str(path)


def ingest_document(
    file_id: str, 
    document_name: str, 
    metadata: Dict[str, Any], 
    job_id: str,
    chunk_mode: ChunkMode = ChunkMode.AUTO,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> IngestResponse:
	# Locate file by pattern
	user_dir = UPLOAD_DIR / "default_user"
	matches = list(user_dir.glob(f"{file_id}_*"))
	if not matches:
		raise FileNotFoundError("Uploaded file not found")
	file_path = matches[0]

	# Parse
	logger.info("Parsing document with Docling/ OCR where needed")
	pages_text = parse_pdf_with_docling(str(file_path))

	# Chunk based on mode
	logger.info(f"Chunking document with {chunk_mode} mode")
	if chunk_mode == ChunkMode.AUTO:
		# Use default values for auto mode
		max_tokens = None
		overlap_tokens = None
	else:
		# Use manual values
		max_tokens = chunk_size
		overlap_tokens = chunk_overlap
	
	chunks: List[Chunk] = hybrid_chunk_document(
		pages_text=pages_text,
		metadata={"document_name": document_name, "job_id": job_id, **(metadata or {})},
		max_tokens=max_tokens,
		overlap_tokens=overlap_tokens,
	)

	# Embed
	logger.info("Embedding chunks and upserting into Chroma")
	client = _client()
	
	# Create collection name based on document name and job ID
	collection_name = _collection_name(document_name, job_id)
	collection = client.get_or_create_collection(name=collection_name)
	
	embedder = get_embedding_function()
	texts = [c.text for c in chunks]
	embs = embedder(texts)
	ids = [c.id for c in chunks]
	metas = [c.metadata for c in chunks]
	collection.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metas)

	logger.info(f"Created collection '{collection_name}' with {len(ids)} chunks for job {job_id}")

	return IngestResponse(document_name=document_name, num_chunks=len(ids), chunk_ids=ids)