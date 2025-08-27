from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class ProjectOut(BaseModel):
    id: str
    name: str
    secret: str


class DocumentOut(BaseModel):
    id: str
    project_id: str
    filename: str
    status: str
    md_url: str | None = None
    chunk_count: int | None = None
    total_characters: int | None = None
    uploaded_at: float | None = None
    processing_started: bool | None = None
    processing_started_at: float | None = None
    completed_at: float | None = None
    processing_duration: float | None = None
    error_message: str | None = None
    last_error_at: float | None = None


class IndexCreate(BaseModel):
    name: str
    document_ids: List[str]


class IndexOut(BaseModel):
    id: str
    project_id: str
    name: str
    status: str
    document_ids: List[str]


class PaginatedDocs(BaseModel):
    items: List[DocumentOut]
    total: int


class QueryRequest(BaseModel):
    index_id: str
    query: str
    n_results: int = Field(default=5, ge=1, le=20)


class QueryResult(BaseModel):
    document: str
    metadata: Dict[str, Any]
    distance: float


class QueryResponse(BaseModel):
    query: str
    results: List[QueryResult]
    total_results: int
