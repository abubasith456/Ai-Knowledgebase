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


class Chunk(BaseModel):
	id: str
	text: str
	metadata: Dict[str, Any]


class IngestResponse(BaseModel):
	document_name: str
	num_chunks: int
	chunk_ids: List[str]


class QueryRequest(BaseModel):
	question: str
	top_k: Optional[int] = 5


class RetrievedContext(BaseModel):
	chunk_id: str
	score: float
	text: str
	metadata: Dict[str, Any]


class QueryResponse(BaseModel):
	answer: str
	contexts: List[RetrievedContext]

