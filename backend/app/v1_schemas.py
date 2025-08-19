from pydantic import BaseModel
from typing import Optional, List


class ProjectCreate(BaseModel):
	name: str
	description: Optional[str] = None


class ProjectResponse(BaseModel):
	projectId: str
	name: str
	description: Optional[str] = None


class ProjectCreateResponse(BaseModel):
	projectId: str
	name: str


class ProjectUpdateResponse(BaseModel):
	projectId: str
	name: str


class ProjectSummary(BaseModel):
	projectId: str
	name: str


class FileUploadResponse(BaseModel):
	fileId: str
	projectId: str
	status: str


class FileSummary(BaseModel):
	fileId: str
	filename: str


class FileDetails(BaseModel):
	fileId: str
	filename: str
	status: str


class IndexCreate(BaseModel):
	name: str
	embeddingModel: Optional[str] = None


class IndexSummary(BaseModel):
	indexId: str
	name: str


class IndexDetails(BaseModel):
	indexId: str
	projectId: str
	name: str


class IndexUpdate(BaseModel):
	name: str


class IndexDeleteResponse(BaseModel):
	status: str
	indexId: str


class IngestIntoIndexRequest(BaseModel):
	fileId: str


class IngestIntoIndexResponse(BaseModel):
	status: str
	fileId: str
	indexId: str
	chunks: int


class QueryRequest(BaseModel):
	query: str
	top_k: Optional[int] = 3


class QueryAnswer(BaseModel):
	text: str
	source: Optional[str] = None


class QueryResponse(BaseModel):
	query: str
	answers: List[QueryAnswer]


class DeleteProjectResponse(BaseModel):
	status: str
	projectId: str


class DeleteFileResponse(BaseModel):
	status: str
	fileId: str


class QuickTestResponse(BaseModel):
	answers: List[QueryAnswer]

