from fastapi import APIRouter

from app.models.schemas import ProjectCreate
from app.models.response import StandardResponse
from app.services.project_service import project_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/")
async def create_project(request: ProjectCreate):
    try:
        result = await project_service.create_project(request)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to create project: {str(e)}")
        return StandardResponse.failed(error=f"Failed to create project: {str(e)}")


@router.get("/")
async def list_projects():
    try:
        result = await project_service.list_projects()
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to list projects: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str):
    try:
        result = await project_service.get_project(project_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to get project: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    try:
        result = await project_service.delete_project(project_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to delete project: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/jobs")
async def get_project_jobs(project_id: str):
    try:
        result = await project_service.get_project_jobs(project_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to get project jobs: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/indexes")
async def get_project_indexes(project_id: str):
    try:
        result = await project_service.get_project_indexes(project_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to get project indexes: {str(e)}")
        return StandardResponse.failed(error=str(e))
