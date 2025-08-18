import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

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


DATA_DIR = Path(os.environ.get("CHROMA_DATA_DIR") or (Path.cwd() / "data" / "chroma"))
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _client() -> chromadb.Client:
	host = os.environ.get("CHROMA_HOST")
	if host:
		return chromadb.HttpClient(host=host, port=int(os.environ.get("CHROMA_PORT", "8000")))
	else:
		# Local persistent client for non-Docker/local dev
		from chromadb.config import Settings
		DATA_DIR.mkdir(parents=True, exist_ok=True)
		return chromadb.PersistentClient(path=str(DATA_DIR))


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


def _collection_name(document_name: str, index_id: Optional[str] = None) -> str:
	prefix = os.environ.get("COLLECTION_PREFIX", "kb_")
	
	if index_id:
		# Use index-based collection name
		base = f"{prefix}index_{index_id}"
	else:
		# Use document-based collection name (legacy)
		doc_part = _sanitize_name(document_name)
		base = f"{prefix}{doc_part}"
	
	return _sanitize_name(base)


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


def ingest_document(file_id: str, document_name: str, metadata: Dict[str, Any], index_id: Optional[str] = None) -> IngestResponse:
	# Locate file by pattern
	user_dir = UPLOAD_DIR / "default_user"
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
	collection = client.get_or_create_collection(name=_collection_name(document_name, index_id))
	embedder = get_embedding_function()
	texts = [c.text for c in chunks]
	embs = embedder(texts)
	ids = [c.id for c in chunks]
	metas = [c.metadata for c in chunks]
	collection.upsert(ids=ids, embeddings=embs, documents=texts, metadatas=metas)

	# Update index document count if using an index
	if index_id:
		try:
			from .index import update_index_document_count, get_index
			index = get_index(index_id)
			if index:
				# Get current document count from ChromaDB collection
				collection_info = collection.get()
				unique_docs = set()
				if collection_info.get('metadatas'):
					for meta in collection_info['metadatas']:
						if isinstance(meta, dict) and 'document_name' in meta:
							unique_docs.add(meta['document_name'])
				update_index_document_count(index_id, len(unique_docs))
		except Exception as e:
			logger.warning(f"Failed to update index document count: {e}")

	return IngestResponse(document_name=document_name, num_chunks=len(ids), chunk_ids=ids)