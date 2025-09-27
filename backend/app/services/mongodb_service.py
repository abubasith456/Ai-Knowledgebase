from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional, Dict

from app.config import settings
from app.models.schemas import (
    ProjectDB,
    JobDB,
    IndexDB,
    ProjectStatus,
    JobStatus,
    IndexStatus,
)
from app.utils.logging import log_print
from app.services.minio_service import minio_service
from app.services.qdrant_service import qdrant_service


class MongoDBService:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client.knowledge_base
        log_print("✅ MongoDB service initialized")

    # Project operations
    def create_project(self, name: str, description: Optional[str] = None) -> str:
        # Create Pydantic model
        project = ProjectDB(
            name=name,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion
        project_dict = project.model_dump()
        self.db.projects.insert_one(project_dict)
        log_print(f"📁 Created project: {project.id} - {name}")
        return project.id

    def get_project(self, project_id: str) -> Optional[ProjectDB]:
        doc = self.db.projects.find_one(
            {"id": project_id, "status": ProjectStatus.ACTIVE}
        )
        if doc:
            return ProjectDB(**doc)
        return None

    def list_projects(self) -> List[ProjectDB]:
        docs = list(self.db.projects.find({"status": ProjectStatus.ACTIVE}))
        return [ProjectDB(**doc) for doc in docs]

    def delete_project(self, project_id: str) -> bool:
        """DELETE PROJECT WITH CASCADE CLEANUP"""
        try:
            log_print(f"🗑️ Starting cascade deletion for project: {project_id}")

            # Get all jobs for this project
            jobs = self.get_jobs_by_project(project_id)
            log_print(f"📄 Found {len(jobs)} jobs to cleanup")

            # Get all indexes for this project
            indexes = self.list_indexes_by_project(project_id)
            log_print(f"📊 Found {len(indexes)} indexes to cleanup")

            # 1. Delete all Qdrant collections for indexes
            for index in indexes:
                try:
                    qdrant_service.delete_collection(index.id)
                    log_print(f"🗑️ Deleted Qdrant collection: {index.id}")
                except Exception as e:
                    log_print(
                        f"⚠️ Failed to delete Qdrant collection {index.id}: {str(e)}"
                    )

            # 2. Delete all MinIO files for jobs
            for job in jobs:
                try:
                    minio_service.delete_markdown(job.id)
                    log_print(f"🗑️ Deleted MinIO file: {job.id}")
                except Exception as e:
                    log_print(f"⚠️ Failed to delete MinIO file {job.id}: {str(e)}")

            # 3. Soft delete all indexes
            self.db.indexes.update_many(
                {"project_id": project_id},
                {"$set": {"status": IndexStatus.DELETED, "updated_at": datetime.now()}},
            )

            # 4. Soft delete all jobs
            self.db.jobs.update_many(
                {"project_id": project_id},
                {"$set": {"status": JobStatus.FAILED, "updated_at": datetime.now()}},
            )

            # 5. Soft delete project
            result = self.db.projects.update_one(
                {"id": project_id},
                {
                    "$set": {
                        "status": ProjectStatus.DELETED,
                        "updated_at": datetime.now(),
                    }
                },
            )

            if result.modified_count > 0:
                log_print(
                    f"✅ Successfully deleted project {project_id} with all related data"
                )
                return True
            else:
                log_print(f"❌ Project {project_id} not found or already deleted")
                return False

        except Exception as e:
            log_print(f"❌ Error during project cascade deletion: {str(e)}")
            return False

    def get_project_stats(self, project_id: str) -> dict:
        jobs_count = self.db.jobs.count_documents({"project_id": project_id})
        indexes_count = self.db.indexes.count_documents(
            {"project_id": project_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        return {"jobs_count": jobs_count, "indexes_count": indexes_count}

    # Job operations
    def create_job(self, project_id: str, filename: str) -> str:
        # Create Pydantic model
        job = JobDB(
            project_id=project_id,
            filename=filename,
            status=JobStatus.PARSING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion
        job_dict = job.model_dump()
        self.db.jobs.insert_one(job_dict)
        return job.id

    def update_job_status(self, job_id: str, status: JobStatus, **kwargs):
        update_data = {"status": status, "updated_at": datetime.now()}
        update_data.update(kwargs)
        self.db.jobs.update_one({"id": job_id}, {"$set": update_data})

    def get_job(self, job_id: str) -> Optional[JobDB]:
        doc = self.db.jobs.find_one({"id": job_id})
        if doc:
            return JobDB(**doc)
        return None

    def get_jobs_by_project(self, project_id: str) -> List[JobDB]:
        docs = list(self.db.jobs.find({"project_id": project_id}))
        return [JobDB(**doc) for doc in docs]

    def get_jobs_by_ids(self, job_ids: List[str]) -> List[JobDB]:
        docs = list(self.db.jobs.find({"id": {"$in": job_ids}}))
        return [JobDB(**doc) for doc in docs]

    def delete_job(self, job_id: str) -> Dict[str, str]:
        """DELETE JOB WITH INDEX DEPENDENCY CHECK"""
        try:
            log_print(f"🗑️ Checking if job {job_id} can be deleted")

            # Check if job is used in any active indexes
            indexes_using_job = list(
                self.db.indexes.find(
                    {"job_ids": job_id, "status": {"$ne": IndexStatus.DELETED}}
                )
            )

            if indexes_using_job:
                index_names = [idx["name"] for idx in indexes_using_job]
                log_print(f"❌ Job {job_id} is used in indexes: {index_names}")
                return {
                    "status": "failed",
                    "message": f"Cannot delete job. It's used in indexes: {', '.join(index_names)}",
                }

            # Delete from MinIO
            try:
                minio_service.delete_markdown(job_id)
                log_print(f"🗑️ Deleted MinIO file: {job_id}")
            except Exception as e:
                log_print(f"⚠️ Failed to delete MinIO file {job_id}: {str(e)}")

            # Soft delete job
            result = self.db.jobs.update_one(
                {"id": job_id},
                {"$set": {"status": JobStatus.FAILED, "updated_at": datetime.now()}},
            )

            if result.modified_count > 0:
                log_print(f"✅ Successfully deleted job: {job_id}")
                return {"status": "success", "message": "Job deleted successfully"}
            else:
                return {"status": "failed", "message": "Job not found"}

        except Exception as e:
            log_print(f"❌ Error deleting job {job_id}: {str(e)}")
            return {"status": "failed", "message": str(e)}

    # Index operations
    def create_index(
        self,
        project_id: str,
        name: str,
        job_ids: List[str],
        description: Optional[str] = None,
    ) -> str:

        # Create Pydantic model
        index = IndexDB(
            project_id=project_id,
            name=name,
            description=description,
            job_ids=job_ids,
            status=IndexStatus.CREATED,
            synced=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Convert to dict for MongoDB insertion
        index_dict = index.model_dump()
        self.db.indexes.insert_one(index_dict)
        return index.id

    def update_index_status(self, index_id: str, status: IndexStatus, **kwargs):
        update_data = {"status": status, "updated_at": datetime.now()}
        update_data.update(kwargs)
        self.db.indexes.update_one({"id": index_id}, {"$set": update_data})

    def get_index(self, index_id: str) -> Optional[IndexDB]:
        doc = self.db.indexes.find_one(
            {"id": index_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        if doc:
            return IndexDB(**doc)
        return None

    def list_indexes_by_project(self, project_id: str) -> List[IndexDB]:
        docs = list(
            self.db.indexes.find(
                {"project_id": project_id, "status": {"$ne": IndexStatus.DELETED}}
            )
        )
        return [IndexDB(**doc) for doc in docs]

    def delete_index(self, index_id: str) -> bool:
        """DELETE INDEX WITH QDRANT CLEANUP"""
        try:
            log_print(f"🗑️ Deleting index: {index_id}")
            
            # Delete Qdrant collection
            try:
                qdrant_service.delete_collection(index_id)
                log_print(f"🗑️ Deleted Qdrant collection: {index_id}")
            except Exception as e:
                log_print(f"⚠️ Failed to delete Qdrant collection {index_id}: {str(e)}")
            
            # Soft delete index
            result = self.db.indexes.update_one(
                {"id": index_id},
                {"$set": {"status": IndexStatus.DELETED, "updated_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                log_print(f"✅ Successfully deleted index: {index_id}")
                return True
            else:
                log_print(f"❌ Index {index_id} not found")
                return False
                
        except Exception as e:
            log_print(f"❌ Error deleting index {index_id}: {str(e)}")
            return False


mongodb_service = MongoDBService()
