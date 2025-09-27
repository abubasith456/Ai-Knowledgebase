from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4

def generate_uuid() -> str:
    return str(uuid4())

# Database Models (MongoDB Collections)
class ProjectStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"

class JobStatus(str, Enum):
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"

class IndexStatus(str, Enum):
    CREATED = "created"
    SYNCING = "syncing"
    SYNCED = "synced"
    SYNC_FAILED = "sync_failed"
    DELETED = "deleted"

# Database Models with AUTO UUID generation
class ProjectDB(BaseModel):
    id: str = Field(default_factory=generate_uuid)  # AUTO GENERATES UUID
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME
    updated_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME

class JobDB(BaseModel):
    id: str = Field(default_factory=generate_uuid)  # AUTO GENERATES UUID
    project_id: str
    filename: str
    status: JobStatus = JobStatus.PARSING
    file_size: Optional[int] = None
    markdown_size: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME
    updated_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME

class IndexDB(BaseModel):
    id: str = Field(default_factory=generate_uuid)  # AUTO GENERATES UUID
    project_id: str
    name: str
    description: Optional[str] = None
    job_ids: List[str] = Field(default_factory=list)
    status: IndexStatus = IndexStatus.CREATED
    synced: bool = False
    embedding_model: Optional[str] = None
    chunks_count: Optional[int] = None
    embedding_dimension: Optional[int] = None
    sync_started_at: Optional[datetime] = None
    sync_completed_at: Optional[datetime] = None
    sync_failed_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME
    updated_at: datetime = Field(default_factory=datetime.now)  # AUTO GENERATES TIME

# Request/Response Models (same as before)
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    created_at: datetime
    jobs_count: int = 0
    indexes_count: int = 0

class JobResponse(BaseModel):
    job_id: str
    project_id: str
    filename: str
    status: JobStatus
    message: Optional[str] = None

class IndexCreate(BaseModel):
    name: str
    description: Optional[str] = None
    job_ids: List[str]
    
    @field_validator('job_ids')
    @classmethod
    def validate_job_ids(cls, v):
        if len(v) == 0:
            raise ValueError("At least one job_id is required")
        if len(v) > 5:
            raise ValueError("Maximum 5 jobs allowed per index")
        return v

class IndexSync(BaseModel):
    index_id: str
    embedding_model: str = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    chunk_ratio: float = 0.8
    overlap_ratio: float = 0.2

class IndexResponse(BaseModel):
    index_id: str
    project_id: str
    name: str
    description: Optional[str] = None
    job_ids: List[str]
    status: IndexStatus
    jobs_info: Optional[List[Dict]] = None

class QueryRequest(BaseModel):
    index_id: str
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    index_info: Optional[Dict] = None
