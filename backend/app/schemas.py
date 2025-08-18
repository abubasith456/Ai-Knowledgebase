from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class APIKeyResponse(BaseModel):
	api_key: str


class APIKeyRegisterRequest(BaseModel):
	api_key: str


class APIKeyValidateResponse(BaseModel):
	valid: bool


class IngestRequest(BaseModel):
	file_id: str
	document_name: str
	metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
	index_id: Optional[str] = None


class Chunk(BaseModel):
	id: str
	text: str
	metadata: Dict[str, Any]


class IngestResponse(BaseModel):
	document_name: str
	num_chunks: int
	chunk_ids: List[str]
	job_id: Optional[str] = None


class QueryRequest(BaseModel):
	question: str
	top_k: Optional[int] = 5
	index_id: Optional[str] = None


class RetrievedContext(BaseModel):
	chunk_id: str
	score: float
	text: str
	metadata: Dict[str, Any]


class QueryResponse(BaseModel):
	answer: str
	contexts: List[RetrievedContext]


class JobCreateResponse(BaseModel):
	job_id: str


class JobInfo(BaseModel):
	id: str
	type: str  # 'upload' | 'ingest' | 'index_creation'
	status: str  # 'processing' | 'completed' | 'failed'
	message: Optional[str] = None
	file_id: Optional[str] = None
	document_name: Optional[str] = None
	num_chunks: Optional[int] = None
	indexing_status: Optional[str] = None  # 'pending' | 'processing' | 'completed' | 'failed'
	started_at: Optional[str] = None
	finished_at: Optional[str] = None
	progress: Optional[int] = None  # 0-100


class Parser(BaseModel):
	id: str
	name: str
	description: str
	supported_formats: List[str]


class Index(BaseModel):
	id: str
	name: str
	created_at: str
	document_count: int
	parser_id: str


class IndexCreateRequest(BaseModel):
	name: str
	parser_id: str


class IndexCreateResponse(BaseModel):
	index_id: str
	job_id: Optional[str] = None

