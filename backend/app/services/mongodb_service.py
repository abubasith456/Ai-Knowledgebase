from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List, Optional, Dict
import asyncio

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
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client.knowledge_base
        log_print("✅ Async MongoDB service initialized")

    async def close(self):
        """Close the database connection"""
        self.client.close()

    # Project operations
    async def create_project(self, name: str, description: Optional[str] = None) -> str:
        project = ProjectDB(
            name=name,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        project_dict = project.model_dump()
        await self.db.projects.insert_one(project_dict)
        log_print(f"📁 Async created project: {project.id} - {name}")
        return project.id

    async def get_project(self, project_id: str) -> Optional[ProjectDB]:
        doc = await self.db.projects.find_one(
            {"id": project_id, "status": ProjectStatus.ACTIVE}
        )
        if doc:
            return ProjectDB(**doc)
        return None

    async def list_projects(self) -> List[ProjectDB]:
        cursor = self.db.projects.find({"status": ProjectStatus.ACTIVE})
        docs = await cursor.to_list(length=None)
        return [ProjectDB(**doc) for doc in docs]

    async def delete_project(self, project_id: str) -> bool:
        """ASYNC HARD DELETE PROJECT WITH CASCADE CLEANUP"""
        try:
            log_print(f"🗑️ Starting ASYNC CASCADE HARD DELETION for project: {project_id}")

            # Get all jobs for this project
            jobs = await self.get_jobs_by_project(project_id)
            log_print(f"📄 Found {len(jobs)} jobs to DELETE")

            # Get all indexes for this project
            indexes = await self.list_indexes_by_project(project_id)
            log_print(f"📊 Found {len(indexes)} indexes to DELETE")

            # 1. Delete all Qdrant collections for indexes (concurrent)
            qdrant_tasks = []
            for index in indexes:
                async def delete_qdrant_collection(idx):
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None, qdrant_service.delete_collection, idx.id
                        )
                        log_print(f"🗑️ Deleted Qdrant collection: {idx.id}")
                    except Exception as e:
                        log_print(f"⚠️ Failed to delete Qdrant collection {idx.id}: {str(e)}")
                
                qdrant_tasks.append(delete_qdrant_collection(index))
            
            if qdrant_tasks:
                await asyncio.gather(*qdrant_tasks, return_exceptions=True)

            # 2. Delete all MinIO files for jobs (concurrent)
            minio_tasks = []
            for job in jobs:
                async def delete_minio_file(j):
                    try:
                        await minio_service.delete_markdown(j.id)
                        log_print(f"🗑️ Deleted MinIO file: {j.id}")
                    except Exception as e:
                        log_print(f"⚠️ Failed to delete MinIO file {j.id}: {str(e)}")
                
                minio_tasks.append(delete_minio_file(job))
            
            if minio_tasks:
                await asyncio.gather(*minio_tasks, return_exceptions=True)

            # 3. HARD DELETE all indexes from MongoDB
            indexes_deleted = await self.db.indexes.delete_many({"project_id": project_id})
            log_print(f"🗑️ DELETED {indexes_deleted.deleted_count} indexes from MongoDB")

            # 4. HARD DELETE all jobs from MongoDB
            jobs_deleted = await self.db.jobs.delete_many({"project_id": project_id})
            log_print(f"🗑️ DELETED {jobs_deleted.deleted_count} jobs from MongoDB")

            # 5. HARD DELETE project from MongoDB
            result = await self.db.projects.delete_one({"id": project_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully ASYNC HARD DELETED project {project_id} with all related data")
                return True
            else:
                log_print(f"❌ Project {project_id} not found")
                return False

        except Exception as e:
            log_print(f"❌ Error during ASYNC project CASCADE HARD DELETION: {str(e)}")
            return False

    async def get_project_stats(self, project_id: str) -> dict:
        jobs_count = await self.db.jobs.count_documents({"project_id": project_id})
        indexes_count = await self.db.indexes.count_documents(
            {"project_id": project_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        return {"jobs_count": jobs_count, "indexes_count": indexes_count}

    # Job operations
    async def create_job(
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
        await self.db.jobs.insert_one(job_dict)
        return job.id

    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs):
        update_data = {"status": status, "updated_at": datetime.now()}
        update_data.update(kwargs)
        await self.db.jobs.update_one({"id": job_id}, {"$set": update_data})

    async def get_job(self, job_id: str) -> Optional[JobDB]:
        doc = await self.db.jobs.find_one({"id": job_id})
        if doc:
            return JobDB(**doc)
        return None

    async def get_jobs_by_project(self, project_id: str) -> List[JobDB]:
        cursor = self.db.jobs.find({"project_id": project_id})
        docs = await cursor.to_list(length=None)
        return [JobDB(**doc) for doc in docs]

    async def get_jobs_by_ids(self, job_ids: List[str]) -> List[JobDB]:
        cursor = self.db.jobs.find({"id": {"$in": job_ids}})
        docs = await cursor.to_list(length=None)
        return [JobDB(**doc) for doc in docs]

    async def delete_job(self, job_id: str) -> Dict[str, str]:
        """ASYNC HARD DELETE JOB WITH INDEX DEPENDENCY CHECK"""
        try:
            log_print(f"🗑️ Checking if job {job_id} can be ASYNC HARD DELETED")

            # Check if job is used in any active indexes
            cursor = self.db.indexes.find(
                {"job_ids": job_id, "status": {"$ne": IndexStatus.DELETED}}
            )
            indexes_using_job = await cursor.to_list(length=None)

            if indexes_using_job:
                index_names = [idx["name"] for idx in indexes_using_job]
                log_print(f"❌ Job {job_id} is used in indexes: {index_names}")
                return {
                    "status": "failed",
                    "message": f"Cannot delete job. It's used in indexes: {', '.join(index_names)}",
                }

            # Delete from MinIO
            try:
                await minio_service.delete_markdown(job_id)
                log_print(f"🗑️ Deleted MinIO file: {job_id}")
            except Exception as e:
                log_print(f"⚠️ Failed to delete MinIO file {job_id}: {str(e)}")

            # HARD DELETE job from MongoDB
            result = await self.db.jobs.delete_one({"id": job_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully ASYNC HARD DELETED job: {job_id}")
                return {"status": "success", "message": "Job deleted successfully"}
            else:
                return {"status": "failed", "message": "Job not found"}

        except Exception as e:
            log_print(f"❌ Error ASYNC HARD DELETING job {job_id}: {str(e)}")
            return {"status": "failed", "message": str(e)}

    # Index operations
    async def create_index(
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
        await self.db.indexes.insert_one(index_dict)
        return index.id

    async def update_index_status(self, index_id: str, status: IndexStatus, **kwargs):
        update_data = {"status": status, "updated_at": datetime.now()}
        update_data.update(kwargs)
        await self.db.indexes.update_one({"id": index_id}, {"$set": update_data})

    async def get_index(self, index_id: str) -> Optional[IndexDB]:
        doc = await self.db.indexes.find_one(
            {"id": index_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        if doc:
            return IndexDB(**doc)
        return None

    async def list_indexes_by_project(self, project_id: str) -> List[IndexDB]:
        cursor = self.db.indexes.find(
            {"project_id": project_id, "status": {"$ne": IndexStatus.DELETED}}
        )
        docs = await cursor.to_list(length=None)
        return [IndexDB(**doc) for doc in docs]

    async def delete_index(self, index_id: str) -> bool:
        """ASYNC HARD DELETE INDEX WITH QDRANT CLEANUP"""
        try:
            log_print(f"🗑️ ASYNC HARD DELETING index: {index_id}")

            # Delete Qdrant collection (run in executor to avoid blocking)
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, qdrant_service.delete_collection, index_id
                )
                log_print(f"🗑️ Deleted Qdrant collection: {index_id}")
            except Exception as e:
                log_print(f"⚠️ Failed to delete Qdrant collection {index_id}: {str(e)}")

            # HARD DELETE index from MongoDB
            result = await self.db.indexes.delete_one({"id": index_id})

            if result.deleted_count > 0:
                log_print(f"✅ Successfully ASYNC HARD DELETED index: {index_id}")
                return True
            else:
                log_print(f"❌ Index {index_id} not found")
                return False

        except Exception as e:
            log_print(f"❌ Error ASYNC HARD DELETING index {index_id}: {str(e)}")
            return False

mongodb_service = MongoDBService()
