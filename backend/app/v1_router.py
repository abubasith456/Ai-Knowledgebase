import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger

import chromadb

from .parsing import parse_pdf_with_docling
from .chunking import hybrid_chunk_document
from .embeddings import get_embedding_function
from .v1_schemas import (
	ProjectCreate,
	ProjectResponse,
	ProjectCreateResponse,
	ProjectUpdateResponse,
	ProjectSummary,
	JobSummary,
	JobDetails,
	IndexCreate,
	IndexSummary,
	IndexDetails,
	IndexUpdate,
	IndexDeleteResponse,
	IngestIntoIndexRequest,
	IngestIntoIndexResponse,
	QueryRequest,
	QueryResponse,
	QueryAnswer,
	DeleteProjectResponse,
	DeleteJobResponse,
	QuickTestResponse,
)


router = APIRouter(prefix="/v1")


# Root data directory (shared volume or local)
DATA_ROOT = Path(os.environ.get("CHROMA_DATA_DIR") or "./data").resolve()
PROJECTS_DIR = DATA_ROOT / "projects"
FILES_DIR = DATA_ROOT / "files"
INDEX_DIR = DATA_ROOT / "indexes"
JOBS_DIR = DATA_ROOT / "jobs"
for d in [PROJECTS_DIR, FILES_DIR, INDEX_DIR, JOBS_DIR]:
	d.mkdir(parents=True, exist_ok=True)


def _project_file(project_id: str) -> Path:
	return PROJECTS_DIR / f"{project_id}.json"


def _index_file(project_id: str, index_id: str) -> Path:
	return INDEX_DIR / f"{project_id}_{index_id}.json"


def _client() -> chromadb.Client:
	host = os.environ.get("CHROMA_HOST")
	if host:
		return chromadb.HttpClient(host=host, port=int(os.environ.get("CHROMA_PORT", "8000")))
	from chromadb.config import Settings
	return chromadb.PersistentClient(path=str(DATA_ROOT))


def _ensure_project_exists(project_id: str) -> Dict:
	p = _project_file(project_id)
	if not p.exists():
		raise HTTPException(status_code=404, detail="Project not found")
	import json
	return json.loads(p.read_text())


def _save_project(data: Dict):
	import json
	_project_file(data["projectId"]).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
	from datetime import datetime, timezone
	return datetime.now(timezone.utc).isoformat()


def _save_index_meta(meta: Dict):
	import json
	(INDEX_DIR / f"{meta['projectId']}_{meta['indexId']}.json").write_text(json.dumps(meta, indent=2))


def _read_index_meta(project_id: str, index_id: str) -> Dict:
	import json
	path = _index_file(project_id, index_id)
	if not path.exists():
		raise HTTPException(status_code=404, detail="Index not found")
	return json.loads(path.read_text())


def _list_indexes(project_id: str) -> List[Dict]:
	import json
	items: List[Dict] = []
	for p in INDEX_DIR.glob(f"{project_id}_*.json"):
		try:
			items.append(json.loads(p.read_text()))
		except Exception:
			continue
	return items


def _delete_index_meta(project_id: str, index_id: str):
	path = _index_file(project_id, index_id)
	if path.exists():
		path.unlink()


def _job_meta_path(project_id: str, job_id: str) -> Path:
	return JOBS_DIR / f"{project_id}_{job_id}.json"


def _save_job_meta(meta: Dict):
	import json
	meta["updatedAt"] = _now_iso()
	_job_meta_path(meta["projectId"], meta["jobId"]).write_text(json.dumps(meta, indent=2))


def _read_job_meta(project_id: str, job_id: str) -> Dict:
	import json
	path = _job_meta_path(project_id, job_id)
	if not path.exists():
		raise HTTPException(status_code=404, detail="Job not found")
	return json.loads(path.read_text())


def _list_jobs(project_id: str) -> List[Dict]:
	import json
	items: List[Dict] = []
	for p in JOBS_DIR.glob(f"{project_id}_*.json"):
		try:
			items.append(json.loads(p.read_text()))
		except Exception:
			continue
	return items


def _delete_job(project_id: str, job_id: str):
	path = _job_meta_path(project_id, job_id)
	if path.exists():
		path.unlink()


def _collection_name(project_id: str, index_id: Optional[str] = None) -> str:
	prefix = os.environ.get("COLLECTION_PREFIX", "kb_")
	if index_id:
		return f"{prefix}{project_id}_{index_id}"
	return f"{prefix}{project_id}"


# 1. PROJECT MANAGEMENT
@router.post("/projects", response_model=ProjectCreateResponse)
def create_project(payload: ProjectCreate):
	project_id = f"proj_{uuid.uuid4().hex[:8]}"
	data = {"projectId": project_id, "name": payload.name, "description": payload.description or ""}
	_save_project(data)
	return ProjectCreateResponse(projectId=data["projectId"], name=data["name"])


@router.get("/projects", response_model=List[ProjectSummary])
def list_projects():
	import json
	items: List[ProjectSummary] = []
	for p in PROJECTS_DIR.glob("*.json"):
		try:
			obj = json.loads(p.read_text())
			items.append(ProjectSummary(projectId=obj["projectId"], name=obj["name"]))
		except Exception:
			continue
	return items


@router.get("/projects/{projectId}", response_model=ProjectResponse)
def get_project_details(projectId: str):
	obj = _ensure_project_exists(projectId)
	return ProjectResponse(**obj)


@router.put("/projects/{projectId}", response_model=ProjectUpdateResponse)
def update_project(projectId: str, payload: ProjectCreate):
	obj = _ensure_project_exists(projectId)
	obj["name"] = payload.name
	obj["description"] = payload.description or ""
	_save_project(obj)
	return ProjectUpdateResponse(projectId=obj["projectId"], name=obj["name"])


@router.delete("/projects/{projectId}", response_model=DeleteProjectResponse)
def delete_project(projectId: str):
	p = _project_file(projectId)
	if not p.exists():
		raise HTTPException(status_code=404, detail="Project not found")
	# delete jobs (meta + binaries)
	for meta in JOBS_DIR.glob(f"{projectId}_*.json"):
		meta.unlink()
	for binf in FILES_DIR.glob(f"{projectId}_job_*.bin"):
		binf.unlink()
	# delete indexes meta
	for meta in INDEX_DIR.glob(f"{projectId}_*.json"):
		meta.unlink()
	p.unlink()
	return DeleteProjectResponse(status="deleted", projectId=projectId)


# 2. JOB MANAGEMENT (file-as-job)
@router.post("/projects/{projectId}/jobs", response_model=JobDetails)
def create_job(projectId: str, file: UploadFile = File(...)):
	_ensure_project_exists(projectId)
	job_id = f"job_{uuid.uuid4().hex[:8]}"
	filename = file.filename or "upload.bin"
	filetype = (filename.split('.')[-1].lower() if '.' in filename else 'bin')
	binary_path = FILES_DIR / f"{projectId}_{job_id}.bin"
	raw = file.file.read()
	with binary_path.open("wb") as f:
		f.write(raw)
	filesize = len(raw)
	job = {
		"jobId": job_id,
		"projectId": projectId,
		"filename": filename,
		"filetype": filetype,
		"filesize": filesize,
		"status": "uploaded",
		"parsingStatus": "pending",
		"indexingStatus": "idle",
		"pages": None,
		"chunks": None,
		"indexId": None,
		"createdAt": _now_iso(),
		"updatedAt": _now_iso(),
	}
	_save_job_meta(job)
	return JobDetails(**job)


@router.get("/projects/{projectId}/jobs", response_model=List[JobSummary])
def list_jobs(projectId: str):
	_ensure_project_exists(projectId)
	items = _list_jobs(projectId)
	return [JobSummary(jobId=i["jobId"], filename=i.get("filename", ""), status=i.get("status", "uploaded")) for i in items]


@router.get("/projects/{projectId}/jobs/{jobId}", response_model=JobDetails)
def get_job_details(projectId: str, jobId: str):
	meta = _read_job_meta(projectId, jobId)
	return JobDetails(**meta)


@router.delete("/projects/{projectId}/jobs/{jobId}", response_model=DeleteJobResponse)
def delete_job(projectId: str, jobId: str):
	_read_job_meta(projectId, jobId)
	_delete_job(projectId, jobId)
	bin_path = FILES_DIR / f"{projectId}_{jobId}.bin"
	if bin_path.exists():
		bin_path.unlink()
	return DeleteJobResponse(status="deleted", jobId=jobId)


@router.post("/projects/{projectId}/jobs/{jobId}/parse", response_model=JobDetails)
def parse_job(projectId: str, jobId: str):
	meta = _read_job_meta(projectId, jobId)
	bin_path = FILES_DIR / f"{projectId}_{jobId}.bin"
	if not bin_path.exists():
		raise HTTPException(status_code=404, detail="File data missing")
	try:
		pages_text = parse_pdf_with_docling(str(bin_path))
		meta["parsingStatus"] = "completed"
		meta["status"] = "parsed"
		meta["pages"] = len(pages_text)
		_save_job_meta(meta)
		return JobDetails(**meta)
	except Exception as exc:
		meta["parsingStatus"] = "failed"
		meta["status"] = "failed"
		_save_job_meta(meta)
		raise HTTPException(status_code=500, detail=str(exc))


# 3. INDEXING
@router.post("/projects/{projectId}/indexes", response_model=IndexDetails)
def create_index(projectId: str, payload: IndexCreate):
	_ensure_project_exists(projectId)
	index_id = f"index_{uuid.uuid4().hex[:6]}"
	meta = {
		"indexId": index_id,
		"projectId": projectId,
		"name": payload.name,
		"embeddingModel": payload.embeddingModel or os.environ.get("MODEL_NAME", "jinaai/jina-embeddings-v3-small"),
	}
	_save_index_meta(meta)
	return IndexDetails(indexId=index_id, projectId=projectId, name=payload.name)


@router.get("/projects/{projectId}/indexes", response_model=List[IndexSummary])
def list_indexes(projectId: str):
	_ensure_project_exists(projectId)
	items = _list_indexes(projectId)
	return [IndexSummary(indexId=i["indexId"], name=i["name"]) for i in items]


@router.get("/projects/{projectId}/indexes/{indexId}", response_model=IndexDetails)
def get_index_details(projectId: str, indexId: str):
	meta = _read_index_meta(projectId, indexId)
	return IndexDetails(indexId=meta["indexId"], projectId=meta["projectId"], name=meta["name"])


@router.put("/projects/{projectId}/indexes/{indexId}", response_model=IndexSummary)
def update_index(projectId: str, indexId: str, payload: IndexUpdate):
	meta = _read_index_meta(projectId, indexId)
	meta["name"] = payload.name
	_save_index_meta(meta)
	return IndexSummary(indexId=indexId, name=payload.name)


@router.delete("/projects/{projectId}/indexes/{indexId}", response_model=IndexDeleteResponse)
def delete_index(projectId: str, indexId: str):
	_read_index_meta(projectId, indexId)
	_delete_index_meta(projectId, indexId)
	return IndexDeleteResponse(status="deleted", indexId=indexId)


@router.post("/projects/{projectId}/indexes/{indexId}/ingest", response_model=IngestIntoIndexResponse)
def ingest_into_index(projectId: str, indexId: str, payload: IngestIntoIndexRequest):
	_read_index_meta(projectId, indexId)
	job = _read_job_meta(projectId, payload.jobId)
	bin_path = FILES_DIR / f"{projectId}_{payload.jobId}.bin"
	if not bin_path.exists():
		raise HTTPException(status_code=404, detail="File data missing")
	# Parse if needed
	pages_text = []
	if job.get("parsingStatus") != "completed" or not job.get("pages"):
		pages_text = parse_pdf_with_docling(str(bin_path))
		job["parsingStatus"] = "completed"
		job["status"] = "parsed"
		job["pages"] = len(pages_text)
		_save_job_meta(job)
	else:
		# If already parsed, parse again to get text for chunking
		pages_text = parse_pdf_with_docling(str(bin_path))
	# Chunk and embed
	chunks = hybrid_chunk_document(
		pages_text=pages_text,
		max_tokens=8000,
		overlap_tokens=200,
		metadata={"projectId": projectId, "jobId": payload.jobId, "filename": job.get("filename", "")},
	)
	client = _client()
	collection = client.get_or_create_collection(name=_collection_name(projectId, indexId))
	embedder = get_embedding_function()
	embs = embedder([c.text for c in chunks])
	ids = [c.id for c in chunks]
	metas = [c.metadata for c in chunks]
	collection.upsert(ids=ids, embeddings=embs, documents=[c.text for c in chunks], metadatas=metas)
	# Update job
	job["indexingStatus"] = "completed"
	job["status"] = "indexed"
	job["chunks"] = len(ids)
	job["indexId"] = indexId
	_save_job_meta(job)
	return IngestIntoIndexResponse(status="indexed", jobId=payload.jobId, indexId=indexId, chunks=len(ids))


# 4. QUERYING
@router.post("/projects/{projectId}/indexes/{indexId}/query", response_model=QueryResponse)
def query_index(projectId: str, indexId: str, payload: QueryRequest):
	_read_index_meta(projectId, indexId)
	client = _client()
	collection = client.get_or_create_collection(name=_collection_name(projectId, indexId))
	embedder = get_embedding_function()
	q_emb = embedder([payload.query])[0]
	res = collection.query(query_embeddings=[q_emb], n_results=payload.top_k or 3)
	docs = res.get('documents', [[]])[0]
	sources = res.get('metadatas', [[]])[0]
	answers = []
	for i, text in enumerate(docs):
		source_meta = sources[i] if i < len(sources) and isinstance(sources[i], dict) else {}
		answers.append(QueryAnswer(text=text, source=source_meta.get('jobId') or source_meta.get('fileId')))
	return QueryResponse(query=payload.query, answers=answers[: (payload.top_k or 3)])


# 5. TESTING (OPTIONAL)
@router.post("/query/test", response_model=QuickTestResponse)
def quick_test(file: UploadFile = File(...), query: str = Form("What is in this document?")):
	# Save temp
	tmp_path = FILES_DIR / f"tmp_{uuid.uuid4().hex[:8]}_{file.filename or 'upload.pdf'}"
	with tmp_path.open("wb") as f:
		f.write(file.file.read())
	# Parse + chunk + embed ephemeral collection
	pages_text = parse_pdf_with_docling(str(tmp_path))
	chunks = hybrid_chunk_document(pages_text=pages_text, max_tokens=8000, overlap_tokens=200, metadata={})
	embedder = get_embedding_function()
	embs = embedder([c.text for c in chunks])
	client = _client()
	collection = client.get_or_create_collection(name=f"quicktest_{uuid.uuid4().hex[:6]}")
	ids = [c.id for c in chunks]
	collection.upsert(ids=ids, embeddings=embs, documents=[c.text for c in chunks])
	q_emb = embedder([query])[0]
	res = collection.query(query_embeddings=[q_emb], n_results=3)
	texts = res.get('documents', [[]])[0]
	answers = [QueryAnswer(text=t) for t in texts]
	try:
		tmp_path.unlink(missing_ok=True)
	except Exception:
		pass
	return QuickTestResponse(answers=answers)