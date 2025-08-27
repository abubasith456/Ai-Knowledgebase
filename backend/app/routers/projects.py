# app/routers/projects.py
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List
from pathlib import Path
import shutil

from app.models import ProjectCreate, Project, Document
from app.services.parser_service import parser_queue
from app.repository.db import projects_store, documents_store, project_docs_store
from app.utils import success_response, error_response


router = APIRouter()
UPLOAD_DIR = Path("app/storage/uploaded_docs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/")
async def list_projects():
    data = await projects_store.load()
    binds = await project_docs_store.load()
    projects = []
    for proj_uuid, proj in data.items():
        doc_ids = binds.get(proj_uuid, [])
        proj["documents"] = doc_ids
        projects.append(proj)
    return success_response(
        message="Projects retrieved",
        data={"projects": projects},
    )


@router.post("/", response_model=Project)
async def create_project(payload: ProjectCreate):
    # Exist check
    data = await projects_store.load()
    if any(proj["name"] == payload.name for proj in data.values()):
        return error_response(
            message="Project with this name already exists",
            error="Duplicate project name",
            data={"name": payload.name},
        )
    proj = Project(name=payload.name, documents=[])
    # Each call should be a single critical section without nested awaits under lock
    await projects_store.upsert(proj.proj_uuid, proj.dict())
    await project_docs_store.upsert(proj.proj_uuid, [])
    return success_response(
        message="Project created",
        data=proj.model_dump(),
    )


@router.get("/{proj_uuid}", response_model=Project)
async def get_project(proj_uuid: str):
    data = await projects_store.load()
    proj = data.get(proj_uuid)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    # hydrate documents from binding file
    binds = await project_docs_store.load()
    doc_ids = binds.get(proj_uuid, [])
    proj["documents"] = doc_ids
    return success_response(
        message="Project retrieved",
        data=proj,
    )


@router.delete("/{proj_uuid}")
async def delete_project(proj_uuid: str):
    await projects_store.delete(proj_uuid)
    await project_docs_store.delete(proj_uuid)
    return success_response(
        message="Project deleted",
        data={"proj_uuid": proj_uuid},
    )


@router.post("/{proj_uuid}/upload")
async def upload_to_project(
    proj_uuid: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    projs = await projects_store.load()
    if proj_uuid not in projs:
        return error_response(
            message="Project not found",
            error="Project not found",
            status_code=404,
            data={"proj_uuid": proj_uuid},
        )

    binds = await project_docs_store.load()
    project_list = binds.get(proj_uuid, [])

    docs = await documents_store.load()
    existing_filenames = {
        doc["filename"] for doc in docs.values() if doc.get("project_uuid") == proj_uuid
    }

    saved_docs = []
    for up in files:
        if up.filename in existing_filenames:
            return error_response(
                message=f"File '{up.filename}' already exists in this project.",
                error="Duplicate filename",
                status_code=400,
                data={"proj_uuid": proj_uuid, "filename": up.filename},
            )

        doc = Document(project_uuid=proj_uuid, filename=str(up.filename))
        file_path = UPLOAD_DIR / f"{doc.doc_uuid}_{up.filename}"
        with open(file_path, "wb") as out:
            shutil.copyfileobj(up.file, out)

        await documents_store.upsert(doc.doc_uuid, doc.dict())
        project_list.append(doc.doc_uuid)
        await project_docs_store.upsert(proj_uuid, project_list)

        background_tasks.add_task(
            parser_queue.add_task,
            str(file_path),
            doc.doc_uuid,
            proj_uuid,
        )

        saved_docs.append(
            {"doc_uuid": doc.doc_uuid, "filename": doc.filename, "status": doc.status}
        )

    return success_response(
        message="Upload successful",
        data={"proj_uuid": proj_uuid, "documents": saved_docs},
    )
