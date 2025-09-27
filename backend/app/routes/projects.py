from fastapi import APIRouter
from typing import List

from app.models.schemas import ProjectCreate, ProjectResponse
from app.models.response import StandardResponse
from app.services.mongodb_service import mongodb_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/", response_model=StandardResponse[ProjectResponse])
async def create_project(request: ProjectCreate):
    """Create a new project"""
    try:
        project_id = mongodb_service.create_project(request.name, request.description)
        print("Created project ID:", project_id)
        project = mongodb_service.get_project(project_id)
        stats = mongodb_service.get_project_stats(project_id)

        if not project:
            return StandardResponse.failed(
                error="Failed to retrieve project information"
            )

        response_data = ProjectResponse(
            project_id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            jobs_count=stats["jobs_count"],
            indexes_count=stats["indexes_count"],
        )

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Failed to create project: {str(e)}")
        return StandardResponse.failed(error=f"Failed to create project: {str(e)}")


@router.get("/", response_model=StandardResponse[List[ProjectResponse]])
async def list_projects():
    """List all projects"""
    try:
        projects = mongodb_service.list_projects()
        result = []

        for project in projects:
            stats = mongodb_service.get_project_stats(project.id)
            result.append(
                ProjectResponse(
                    project_id=project.id,
                    name=project.name,
                    description=project.description,
                    status=project.status,
                    created_at=project.created_at,
                    jobs_count=stats["jobs_count"],
                    indexes_count=stats["indexes_count"],
                )
            )

        return StandardResponse.success(data=result)

    except Exception as e:
        log_print(f"❌ Failed to list projects: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}", response_model=StandardResponse[ProjectResponse])
async def get_project(project_id: str):
    """Get project details"""
    try:
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        stats = mongodb_service.get_project_stats(project_id)

        response_data = ProjectResponse(
            project_id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            jobs_count=stats["jobs_count"],
            indexes_count=stats["indexes_count"],
        )

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Failed to get project: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/{project_id}", response_model=StandardResponse)
async def delete_project(project_id: str):
    """Delete a project with cascade cleanup (jobs, indexes, vector DB, MinIO files)"""
    try:
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        success = mongodb_service.delete_project(project_id)

        if success:
            return StandardResponse.success(
                data={
                    "message": f"Project {project_id} and all related data deleted successfully"
                }
            )
        else:
            return StandardResponse.failed(error="Failed to delete project")

    except Exception as e:
        log_print(f"❌ Failed to delete project: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/jobs", response_model=StandardResponse)
async def get_project_jobs(project_id: str):
    """Get all jobs for a project"""
    try:
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        jobs = mongodb_service.get_jobs_by_project(project_id)
        jobs_data = [job.model_dump() for job in jobs]

        return StandardResponse.success(
            data={"project_id": project_id, "jobs": jobs_data}
        )

    except Exception as e:
        log_print(f"❌ Failed to get project jobs: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/indexes", response_model=StandardResponse)
async def get_project_indexes(project_id: str):
    """Get all indexes for a project"""
    try:
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        indexes = mongodb_service.list_indexes_by_project(project_id)
        indexes_data = [index.model_dump() for index in indexes]

        return StandardResponse.success(
            data={"project_id": project_id, "indexes": indexes_data}
        )

    except Exception as e:
        log_print(f"❌ Failed to get project indexes: {str(e)}")
        return StandardResponse.failed(error=str(e))
