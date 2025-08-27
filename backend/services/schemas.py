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
