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
    QueryRequest,
    QueryResponse,
)
from services.storage import JSONStore
from services.parsing import parse_with_docling
from services.chroma_store import query_documents
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
        md_url=d.get("md_url"),
        chunk_count=d.get("chunk_count"),
        total_characters=d.get("total_characters"),
        uploaded_at=d.get("uploaded_at"),
        processing_started=d.get("processing_started"),
        processing_started_at=d.get("processing_started_at"),
        completed_at=d.get("completed_at"),
        processing_duration=d.get("processing_duration"),
        error_message=d.get("error_message"),
        last_error_at=d.get("last_error_at"),
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


@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    project = projects_store.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Delete all documents in the project
        doc_ids = docs_store.list_get(project_id) or []
        for doc_id in doc_ids:
            doc = docs_store.get(doc_id)
            if doc:
                # Remove from ChromaDB
                try:
                    from services.chroma_store import delete_documents
                    delete_documents(
                        collection_name=project_collection_name(project_id),
                        filter_metadata={"project_id": project_id}
                    )
                except Exception as e:
                    print(f"ChromaDB deletion failed for project {project_id}: {e}")
                
                # Remove file
                try:
                    file_path = _file_path(doc_id, doc["filename"])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"File deletion failed: {e}")
                
                # Remove from storage
                docs_store.delete(doc_id)
        
        # Delete all indexes in the project
        index_ids = indexes_store.list_get(project_id) or []
        for index_id in index_ids:
            indexes_store.delete(index_id)
        
        # Remove project lists
        docs_store.list_remove_all(project_id)
        indexes_store.list_remove_all(project_id)
        
        # Delete the project
        projects_store.delete(project_id)
        
        return {"message": "Project deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


# Documents
@app.post("/projects/{project_id}/documents", response_model=DocumentOut)
async def upload_document(project_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    filename = file.filename
    path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
    
    # Save the uploaded file
    with open(path, "wb") as out:
        shutil.copyfileobj(file.file, out)
    
    # Create document record
    d = {
        "id": doc_id,
        "project_id": project_id,
        "filename": filename,
        "status": "pending",
        "md_url": None,  # will be set after parsing/upload to Dropbox
        "uploaded_at": time.time(),
        "processing_started": False,
    }
    docs_store.set(doc_id, d)
    docs_store.list_append_unique_front(project_id, doc_id)
    
    # Start background parsing task immediately in separate thread
    background_tasks.add_task(_parse_and_store, doc_id)
    
    print(f"Document {doc_id} uploaded and background parsing task started")
    return _doc_out(d)


@app.get("/projects/{project_id}/documents", response_model=PaginatedDocs)
def list_documents(project_id: str, skip: int = 0, limit: int = 100):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    ids = docs_store.list_get(project_id)
    items = [docs_store.get(i) for i in ids if docs_store.get(i)]
    page = items[skip : skip + limit]
    return PaginatedDocs(items=[_doc_out(d) for d in page], total=len(items))


@app.delete("/projects/{project_id}/documents/{document_id}")
def delete_document(project_id: str, document_id: str):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    
    doc = docs_store.get(document_id)
    if not doc or doc["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Remove from ChromaDB collection
        try:
            from services.chroma_store import delete_documents
            delete_documents(
                collection_name=project_collection_name(project_id),
                filter_metadata={"doc_id": document_id}
            )
        except Exception as e:
            print(f"ChromaDB deletion failed: {e}")
            # Continue with local deletion even if ChromaDB fails
        
        # Remove from local storage
        docs_store.delete(document_id)
        docs_store.list_remove(project_id, document_id)
        
        # Remove file from uploads directory
        try:
            file_path = _file_path(document_id, doc["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"File deletion failed: {e}")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")





def _parse_and_store(doc_id: str):
    """
    Background task to parse and store a document.
    This runs in a separate thread for each uploaded document.
    """
    d = docs_store.get(doc_id)
    if not d:
        print(f"Document {doc_id} not found in store")
        return
    
    try:
        # Update status to parsing and mark processing started
        d["status"] = "parsing"
        d["processing_started"] = True
        d["processing_started_at"] = time.time()
        docs_store.set(doc_id, d)
        
        print(f"[{doc_id}] 🚀 Starting background parsing task for: {d['filename']}")
        
        path = _file_path(d["id"], d["filename"])
        print(f"[{doc_id}] 📁 File path: {path}")
        
                  # Parse document using our simple parser (no chunking)
          full_text, _ = parse_with_docling(path)
          print(f"[{doc_id}] ✅ Document parsed successfully")
        
        # Upload parsed Markdown to Dropbox
        md_url = None
        try:
            print(f"[{doc_id}] ☁️ Uploading markdown to Dropbox...")
            md_url = upload_and_share_markdown(d["project_id"], d["id"], full_text)
            print(f"[{doc_id}] ✅ Markdown uploaded to Dropbox: {md_url}")
        except Exception as e:
            print(f"[{doc_id}] ❌ Dropbox upload failed: {e}")
            # Dropbox optional; backend continues
        
                  # Upload parsed Markdown to Dropbox
          md_url = None
          try:
              print(f"[{doc_id}] ☁️ Uploading markdown to Dropbox...")
              md_url = upload_and_share_markdown(d["project_id"], d["id"], full_text)
              print(f"[{doc_id}] ✅ Markdown uploaded to Dropbox: {md_url}")
          except Exception as e:
              print(f"[{doc_id}] ❌ Dropbox upload failed: {e}")
              # Dropbox optional; backend continues
        
                  # Update document status to completed with all metadata
          d["status"] = "completed"
          d["md_url"] = md_url
          d["completed_at"] = time.time()
          d["processing_duration"] = d["completed_at"] - d["processing_started_at"]
          docs_store.set(doc_id, d)
        
        print(f"[{doc_id}] 🎉 Document processing completed successfully in {d['processing_duration']:.2f}s")
        
    except Exception as e:
        print(f"[{doc_id}] ❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Reset to pending to allow retry
        d["status"] = "pending"
        d["processing_started"] = False
        d["error_message"] = str(e)
        d["last_error_at"] = time.time()
        docs_store.set(doc_id, d)
        
        print(f"[{doc_id}] 🔄 Document reset to pending status for retry")


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


@app.delete("/projects/{project_id}/indexes/{index_id}")
def delete_index(project_id: str, index_id: str):
    idx = indexes_store.get(index_id)
    if not idx or idx["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Index not found")
    
    try:
        # Remove from storage
        indexes_store.delete(index_id)
        indexes_store.list_remove(project_id, index_id)
        
        return {"message": "Index deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete index: {str(e)}")


def _finalize_index(index_id: str):
    time.sleep(1.2)  # simulate processing
    idx = indexes_store.get(index_id)
    if not idx:
        return
    idx["status"] = "completed"
    indexes_store.set(index_id, idx)


# Query endpoint
@app.post("/query", response_model=QueryResponse)
def query_index(project_id: str, payload: QueryRequest):
    if not projects_store.get(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the index
    idx = indexes_store.get(payload.index_id)
    if not idx or idx["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Index not found")
    
    if idx["status"] != "completed":
        raise HTTPException(status_code=400, detail="Index not ready for querying")
    
    # Query the ChromaDB collection
    collection_name = project_collection_name(project_id)
    results = query_documents(collection_name, payload.query, payload.n_results or 5)
    
    return QueryResponse(
        query=payload.query,
        results=results,
        total_results=len(results)
    )
