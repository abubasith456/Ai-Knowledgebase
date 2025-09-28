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
    DocumentType,
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
        project = ProjectDB(
            name=name,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

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
        """HARD DELETE PROJECT WITH CASCADE CLEANUP"""
        try:
            log_print(f"🗑️ Starting CASCADE HARD DELETION for project: {project_id}")

            # Get all jobs for this project
            jobs = self.get_jobs_by_project(project_id)
            log_print(f"📄 Found {len(jobs)} jobs to DELETE")

            # Get all indexes for this project
            indexes = self.list_indexes_by_project(project_id)
            log_print(f"📊 Found {len(indexes)} indexes to DELETE")

            # 1. Delete all Qdrant collections for indexes
            for index in indexes:
                try:
                    qdrant_service.delete_collection(index.id)
                    log_print(f"🗑️ Deleted Qdrant collection: {index.id}")
                except Exception as e:
                    log_print(f"⚠️ Failed to delete Qdrant collection {index.id}: {str(e)}")

            # 2. Delete all MinIO files for jobs
            for job in jobs:
                try:
                    minio_service.delete_markdown(job.id)
                    log_print(f"🗑️ Deleted MinIO file: {job.id}")
                except Exception as e:
                    log_print(f"⚠️ Failed to delete MinIO file {job.id}: {str(e)}")

            # 3. HARD DELETE all indexes from MongoDB
            indexes_deleted = self.db.indexes.delete_many({"project_id": project_id})
            log_print(f"🗑️ DELETED {indexes_deleted.deleted_count} indexes from MongoDB")

            # 4. HARD DELETE all jobs from MongoDB
            jobs_deleted = self.db.jobs.delete_many({"project_id": project_id})
            log_print(f"🗑️ DELETED {jobs_deleted.deleted_count} jobs from MongoDB")

            # 5. HARD DELETE project from MongoDB
            result = self.db.projects.delete_one({"id": project_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully HARD DELETED project {project_id} with all related data")
                return True
            else:
                log_print(f"❌ Project {project_id} not found")
                return False

        except Exception as e:
            log_print(f"❌ Error during project CASCADE HARD DELETION: {str(e)}")
            return False

    def get_project_stats(self, project_id: str) -> dict:
        jobs_count = self.db.jobs.count_documents({"project_id": project_id})
        indexes_count = self.db.indexes.count_documents(
            {"project_id": project_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        return {"jobs_count": jobs_count, "indexes_count": indexes_count}

    # Job operations
    def create_job(
        self, project_id: str, filename: str, type: DocumentType = DocumentType.FILE
    ) -> str:
        job = JobDB(
            project_id=project_id,
            filename=filename,
            status=JobStatus.PARSING,
            type=type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

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
        """HARD DELETE JOB WITH INDEX DEPENDENCY CHECK"""
        try:
            log_print(f"🗑️ Checking if job {job_id} can be HARD DELETED")

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

            # HARD DELETE job from MongoDB
            result = self.db.jobs.delete_one({"id": job_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully HARD DELETED job: {job_id}")
                return {"status": "success", "message": "Job deleted successfully"}
            else:
                return {"status": "failed", "message": "Job not found"}

        except Exception as e:
            log_print(f"❌ Error HARD DELETING job {job_id}: {str(e)}")
            return {"status": "failed", "message": str(e)}

    # Index operations
    def create_index(
        self,
        project_id: str,
        name: str,
        job_ids: List[str],
        description: Optional[str] = None,
    ) -> str:
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
        """HARD DELETE INDEX WITH QDRANT CLEANUP"""
        try:
            log_print(f"🗑️ HARD DELETING index: {index_id}")

            # Delete Qdrant collection
            try:
                qdrant_service.delete_collection(index_id)
                log_print(f"🗑️ Deleted Qdrant collection: {index_id}")
            except Exception as e:
                log_print(f"⚠️ Failed to delete Qdrant collection {index_id}: {str(e)}")

            # HARD DELETE index from MongoDB
            result = self.db.indexes.delete_one({"id": index_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully HARD DELETED index: {index_id}")
                return True
            else:
                log_print(f"❌ Index {index_id} not found")
                return False

        except Exception as e:
            log_print(f"❌ Error HARD DELETING index {index_id}: {str(e)}")
            return False

mongodb_service = MongoDBService()
