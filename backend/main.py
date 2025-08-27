import os
import uuid
import shutil
import time
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from services.settings import settings
from services.schemas import (
    ProjectCreate,
    ProjectOut,
    DocumentOut,
    IndexCreate,
    IndexOut,
    PaginatedDocs,
)
from services.storage import JSONStore
from services.parsing import parse_with_docling, build_embeddings_from_chunks
from services.chroma_store import add_documents
from services.dropbox_storage import upload_and_share_markdown

# Ensure directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STORE_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DIR, exist_ok=True)

# JSON stores
projects_store = JSONStore[dict](kv_path=f"{settings.STORE_DIR}/projects.json")
docs_store = JSONStore[dict](
    kv_path=f"{settings.STORE_DIR}/documents.json",
    list_path=f"{settings.STORE_DIR}/docs_by_project.json",
)
indexes_store = JSONStore[dict](
    kv_path=f"{settings.STORE_DIR}/indexes.json",
    list_path=f"{settings.STORE_DIR}/indexes_by_project.json",
)

app = FastAPI(title="KB Console Backend", version="0.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def project_collection_name(project_id: str) -> str:
    return f"proj_{project_id}_chunks"


def _proj_out(p: dict) -> ProjectOut:
    return ProjectOut(id=p["id"], name=p["name"], secret=p["secret"])


def _doc_out(d: dict) -> DocumentOut:
    return DocumentOut(
        id=d["id"],
        project_id=d["project_id"],
        filename=d["filename"],
        status=d["status"],
    )


def _idx_out(x: dict) -> IndexOut:
    return IndexOut(
        id=x["id"],
        project_id=x["project_id"],
        name=x["name"],
        status=x["status"],
        document_ids=x["document_ids"],
    )


def _file_path(doc_id: str, filename: str) -> str:
    path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return path


# Projects
@app.post("/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate):
    pid = f"prj_{uuid.uuid4().hex[:8]}"
    secret = f"sec_{uuid.uuid4().hex[:6]}"
    p = {"id": pid, "name": payload.name, "secret": secret}
    projects_store.set(pid, p)
    # Init lists
    if not docs_store.list_get(pid):
        docs_store.list_set(pid, [])
    if not indexes_store.list_get(pid):
        indexes_store.list_set(pid, [])
    return _proj_out(p)


@app.get("/projects", response_model=List[ProjectOut])
def list_projects():
    return [_proj_out(p) for p in projects_store.all_values()]


# Documents
@app.post("/projects/{project_id}/documents", response_model=DocumentOut)
async def upload_document(project_id: str, file: UploadFile = File(...)):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    filename = file.filename
    path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
    with open(path, "wb") as out:
        shutil.copyfileobj(file.file, out)
    d = {
        "id": doc_id,
        "project_id": project_id,
        "filename": filename,
        "status": "pending",
        "md_url": None,  # will be set after parsing/upload to Dropbox
    }
    docs_store.set(doc_id, d)
    docs_store.list_append_unique_front(project_id, doc_id)
    return _doc_out(d)


@app.get("/projects/{project_id}/documents", response_model=PaginatedDocs)
def list_documents(project_id: str, skip: int = 0, limit: int = 100):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    ids = docs_store.list_get(project_id)
    items = [docs_store.get(i) for i in ids if docs_store.get(i)]
    page = items[skip : skip + limit]
    return PaginatedDocs(items=[_doc_out(d) for d in page], total=len(items))


# Parsing queue controls one-at-a-time
@app.post("/projects/{project_id}/parse-next", response_model=Optional[DocumentOut])
def parse_next(project_id: str, background_tasks: BackgroundTasks):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    ids = docs_store.list_get(project_id)
    # If any parsing in progress, return it
    for did in ids:
        d = docs_store.get(did)
        if d and d["status"] == "parsing":
            return _doc_out(d)
    # Pick the first pending
    next_id = next(
        (did for did in ids if (docs_store.get(did) or {}).get("status") == "pending"),
        None,
    )
    if not next_id:
        return None
    cur = docs_store.get(next_id)
    if cur is None:
        return None
    cur["status"] = "parsing"
    docs_store.set(next_id, cur)
    background_tasks.add_task(_parse_and_store, next_id)
    return _doc_out(cur)


def _parse_and_store(doc_id: str):
    d = docs_store.get(doc_id)
    if not d:
        return
    try:
        path = _file_path(d["id"], d["filename"])
        full_text, chunks = parse_with_docling(path)
        # Upload parsed Markdown to Dropbox (from chunks -> combine)
        md_text = "\n\n".join(chunks)
        try:
            md_url = upload_and_share_markdown(d["project_id"], d["id"], md_text)
        except Exception:
            md_url = None  # Dropbox optional; backend continues
        # Embed chunks to Chroma
        embeddings = build_embeddings_from_chunks(chunks)
        add_documents(
            collection_name=project_collection_name(d["project_id"]),
            ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            metadatas=[
                {"project_id": d["project_id"], "doc_id": doc_id, "chunk_index": i}
                for i in range(len(chunks))
            ],
            documents=chunks,
        )
        d["status"] = "completed"
        d["md_url"] = md_url
        docs_store.set(doc_id, d)
    except Exception:
        # Reset to pending to allow retry
        d["status"] = "pending"
        docs_store.set(doc_id, d)


# Indexes
@app.post("/projects/{project_id}/indexes", response_model=IndexOut)
def create_index(project_id: str, payload: IndexCreate):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    # Validate chosen docs are completed
    for did in payload.document_ids:
        dd = docs_store.get(did)
        if not dd or dd["project_id"] != project_id:
            raise HTTPException(status_code=400, detail=f"Invalid document id {did}")
        if dd["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Document {did} not completed")
    idx_id = f"idx_{uuid.uuid4().hex[:8]}"
    idx = {
        "id": idx_id,
        "project_id": project_id,
        "name": payload.name,
        "status": "idle",
        "document_ids": payload.document_ids,
    }
    indexes_store.set(idx_id, idx)
    indexes_store.list_append_unique_front(project_id, idx_id)
    return _idx_out(idx)


@app.get("/projects/{project_id}/indexes", response_model=List[IndexOut])
def list_indexes(project_id: str):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    ids = indexes_store.list_get(project_id)
    out: List[IndexOut] = []
    for iid in ids:
        x = indexes_store.get(iid)
        if x:
            out.append(_idx_out(x))
    return out


@app.post("/projects/{project_id}/indexes/{index_id}/start", response_model=IndexOut)
def start_indexing(project_id: str, index_id: str, background_tasks: BackgroundTasks):
    idx = indexes_store.get(index_id)
    if not idx or idx["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Index not found")
    if idx["status"] == "completed":
        return _idx_out(idx)
    idx["status"] = "indexing"
    indexes_store.set(index_id, idx)
    background_tasks.add_task(_finalize_index, index_id)
    return _idx_out(idx)


def _finalize_index(index_id: str):
    time.sleep(1.2)  # simulate processing
    idx = indexes_store.get(index_id)
    if not idx:
        return
    idx["status"] = "completed"
    indexes_store.set(index_id, idx)
