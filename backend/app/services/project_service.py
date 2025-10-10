from typing import Dict, Any, List

from app.models.schemas import ProjectCreate, ProjectResponse
from app.services.mongodb_service import mongodb_service
from app.utils.logging import log_print


class ProjectService:
    def __init__(self):
        self.mongodb = mongodb_service

    async def create_project(self, request: ProjectCreate) -> Dict[str, Any]:
        try:
            project_id = await self.mongodb.create_project(
                request.name, request.description
            )
            print("Created project ID:", project_id)
            project = await self.mongodb.get_project(project_id)
            stats = await self.mongodb.get_project_stats(project_id)

            if not project:
                return {
                    "success": False,
                    "error": "Failed to retrieve project information",
                }

            response_data = ProjectResponse(
                project_id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                jobs_count=stats["jobs_count"],
                indexes_count=stats["indexes_count"],
            )

            return {"success": True, "data": response_data}

        except Exception as e:
            log_print(f"❌ Failed to create project: {str(e)}")
            return {"success": False, "error": f"Failed to create project: {str(e)}"}

    async def list_projects(self) -> Dict[str, Any]:
        try:
            projects = await self.mongodb.list_projects()
            result = []

            for project in projects:
                stats = await self.mongodb.get_project_stats(project.id)
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

            return {"success": True, "data": result}

        except Exception as e:
            log_print(f"❌ Failed to list projects: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        try:
            project = await self.mongodb.get_project(project_id)
            if not project:
                return {"success": False, "error": "Project not found"}

            stats = await self.mongodb.get_project_stats(project_id)

            response_data = ProjectResponse(
                project_id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                jobs_count=stats["jobs_count"],
                indexes_count=stats["indexes_count"],
            )

            return {"success": True, "data": response_data}

        except Exception as e:
            log_print(f"❌ Failed to get project: {str(e)}")
            return {"success": False, "error": str(e)}

    async def delete_project(self, project_id: str) -> Dict[str, Any]:
        try:
            project = await self.mongodb.get_project(project_id)
            if not project:
                return {"success": False, "error": "Project not found"}

            success = await self.mongodb.delete_project(project_id)

            if success:
                return {
                    "success": True,
                    "data": {
                        "message": f"Project {project_id} and all related data deleted successfully"
                    },
                }
            else:
                return {"success": False, "error": "Failed to delete project"}

        except Exception as e:
            log_print(f"❌ Failed to delete project: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_project_jobs(self, project_id: str) -> Dict[str, Any]:
        try:
            project = await self.mongodb.get_project(project_id)
            if not project:
                return {"success": False, "error": "Project not found"}

            jobs = await self.mongodb.get_jobs_by_project(project_id)
            jobs_data = [job.model_dump() for job in jobs]

            return {
                "success": True,
                "data": {"project_id": project_id, "jobs": jobs_data},
            }

        except Exception as e:
            log_print(f"❌ Failed to get project jobs: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_project_indexes(self, project_id: str) -> Dict[str, Any]:
        try:
            project = await self.mongodb.get_project(project_id)
            if not project:
                return {"success": False, "error": "Project not found"}

            indexes = await self.mongodb.list_indexes_by_project(project_id)
            indexes_data = [index.model_dump() for index in indexes]

            return {
                "success": True,
                "data": {"project_id": project_id, "indexes": indexes_data},
            }

        except Exception as e:
            log_print(f"❌ Failed to get project indexes: {str(e)}")
            return {"success": False, "error": str(e)}


project_service = ProjectService()
