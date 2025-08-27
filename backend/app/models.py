from pydantic import BaseModel, Field
from functools import partial
from typing import List
from uuid import uuid4


# Common response.
class CommonResponse(BaseModel):
    message: str
    data: dict = {}
    error: str | None = None


# Helpers
def gen_uuid(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}"


# PROJECT
class ProjectCreate(BaseModel):
    name: str


class Project(BaseModel):
    proj_uuid: str = Field(default_factory=partial(gen_uuid, "proj_"))
    name: str
    documents: List[str] = []


# DOCUMENT
class DocumentStatus(str):
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    project_uuid: str
    filename: str
    status: str = DocumentStatus.PENDING


class Document(BaseModel):
    doc_uuid: str = Field(default_factory=partial(gen_uuid, "doc_"))
    project_uuid: str
    filename: str
    status: str = DocumentStatus.PENDING


# INDEX
class IndexCreate(BaseModel):
    name: str
    project_uuid: str
    document_ids: List[str]  # list of doc_uuid


class Index(BaseModel):
    index_uuid: str = Field(default_factory=partial(gen_uuid, "index_"))
    name: str
    project_uuid: str
    document_ids: List[str]


class QueryRequest(BaseModel):
    query: str
