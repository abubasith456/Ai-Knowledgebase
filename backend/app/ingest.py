import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple

from fastapi import UploadFile
from loguru import logger
import chromadb

try:
	from .schemas import IngestResponse, Chunk
	from .parsing import parse_pdf_with_docling
	from .chunking import hybrid_chunk_document
	from .embeddings import get_embedding_function
except ImportError:
	from schemas import IngestResponse, Chunk
	from parsing import parse_pdf_with_docling
	from chunking import hybrid_chunk_document
	from embeddings import get_embedding_function


DATA_DIR = Path(os.environ.get("CHROMA_DATA_DIR", "/data/chroma"))
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _client() -> chromadb.Client:
	return chromadb.HttpClient(host=os.environ.get("CHROMA_HOST", "chroma"), port=int(os.environ.get("CHROMA_PORT", "8000")))


def _collection_name(x_api_key: str, document_name: str) -> str:
	prefix = os.environ.get("COLLECTION_PREFIX", "kb_")
	user_key = str(abs(hash(x_api_key)))[:10]
	return f"{prefix}{user_key}_{document_name}"


def save_upload_temp(file: UploadFile, x_api_key: str) -> Tuple[str, str]:
	file_id = str(uuid.uuid4())
	user_dir = UPLOAD_DIR / (str(abs(hash(x_api_key)))[:8])
	user_dir.mkdir(parents=True, exist_ok=True)
	path = user_dir / f"{file_id}_{file.filename}"
	with path.open("wb") as f:
		content = file.file.read()
		f.write(content)
	logger.info(f"Saved upload to {path}")
	return file_id, str(path)


def ingest_document(x_api_key: str, file_id: str, document_name: str, metadata: Dict[str, Any]) -> IngestResponse:
	# Locate file by pattern
	user_dir = UPLOAD_DIR / (str(abs(hash(x_api_key)))[:8])
	matches = list(user_dir.glob(f"{file_id}_*"))
	if not matches:
		raise FileNotFoundError("Uploaded file not found")
	file_path = matches[0]

	# Parse
	logger.info("Parsing document with Docling/ OCR where needed")
	pages_text = parse_pdf_with_docling(str(file_path))

	# Chunk
	logger.info("Chunking document with hybrid strategy")
	chunks: List[Chunk] = hybrid_chunk_document(
		pages_text=pages_text,
		max_tokens=8000,
		overlap_tokens=200,
		metadata={"document_name": document_name, **(metadata or {})},
	)

	# Embed
	logger.info("Embedding chunks and upserting into Chroma")
	client = _client()
	collection = client.get_or_create_collection(name=_collection_name(x_api_key, document_name))
	embedder = get_embedding_function()
	texts = [c.text for c in chunks]
	embs = embedder(texts)
	ids = [c.id for c in chunks]
	metas = [c.metadata for c in chunks]
	collection.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metas)

	return IngestResponse(document_name=document_name, num_chunks=len(ids), chunk_ids=ids)