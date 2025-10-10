from typing import Any, Optional, Dict
from datetime import datetime
import asyncio

from app.models.schemas import (
    IndexDB,
    IndexCreate,
    IndexUpdate,
    IndexSync,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    JobStatus,
    IndexStatus,
)
from app.services.mongodb_service import mongodb_service
from app.services.minio_service import minio_service
from app.services.nvidia_service import nvidia_service
from app.services.qdrant_service import qdrant_service
from app.utils.chunking import create_chunks
from app.utils.logging import log_print


class IndexService:
    def __init__(self):
        self.mongodb = mongodb_service
        self.minio = minio_service
        self.nvidia = nvidia_service
        self.qdrant = qdrant_service

    async def create_index(
        self, project_id: str, request: IndexCreate
    ) -> Dict[str, Any]:
        project = await self.mongodb.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        if len(request.job_ids) == 0:
            return {"success": False, "error": "At least one job_id is required"}
        if len(request.job_ids) > 5:
            return {"success": False, "error": "Maximum 5 jobs allowed per index"}

        jobs = await self.mongodb.get_jobs_by_ids(request.job_ids)

        if len(jobs) != len(request.job_ids):
            return {"success": False, "error": "One or more jobs not found"}

        incomplete_jobs = [job for job in jobs if job.status != JobStatus.COMPLETED]
        if incomplete_jobs:
            return {
                "success": False,
                "error": f"Jobs not completed: {[job.id for job in incomplete_jobs]}",
            }

        wrong_project_jobs = [job for job in jobs if job.project_id != project_id]
        if wrong_project_jobs:
            return {
                "success": False,
                "error": f"Jobs belong to different project: {[job.id for job in wrong_project_jobs]}",
            }

        index_id = await self.mongodb.create_index(
            project_id, request.name, request.job_ids, request.description
        )

        jobs_info = [
            {"job_id": job.id, "filename": job.filename, "status": job.status}
            for job in jobs
        ]

        response_data = IndexResponse(
            index_id=index_id,
            project_id=project_id,
            name=request.name,
            description=request.description,
            job_ids=request.job_ids,
            status=IndexStatus.CREATED,
            jobs_info=jobs_info,
        )

        return {"success": True, "data": response_data}

    async def update_index(self, index_id: str, request: IndexUpdate) -> Dict[str, Any]:
        index_doc = await self.mongodb.get_index(index_id)
        if not index_doc:
            return {"success": False, "error": "Index not found"}

        update_data = {}
        requires_resync = False

        if request.name is not None:
            update_data["name"] = request.name

        if request.description is not None:
            update_data["description"] = request.description

        if request.job_ids is not None:
            if len(request.job_ids) == 0:
                return {"success": False, "error": "At least one job_id is required"}
            if len(request.job_ids) > 5:
                return {"success": False, "error": "Maximum 5 jobs allowed per index"}

            jobs = await self.mongodb.get_jobs_by_ids(request.job_ids)

            if len(jobs) != len(request.job_ids):
                return {"success": False, "error": "One or more jobs not found"}

            incomplete_jobs = [job for job in jobs if job.status != JobStatus.COMPLETED]
            if incomplete_jobs:
                return {
                    "success": False,
                    "error": f"Jobs not completed: {[job.id for job in incomplete_jobs]}",
                }

            wrong_project_jobs = [
                job for job in jobs if job.project_id != index_doc.project_id
            ]
            if wrong_project_jobs:
                return {
                    "success": False,
                    "error": f"Jobs belong to different project: {[job.id for job in wrong_project_jobs]}",
                }

            if set(request.job_ids) != set(index_doc.job_ids):
                update_data["job_ids"] = request.job_ids
                requires_resync = True

                update_data["synced"] = False
                update_data["status"] = IndexStatus.CREATED
                update_data["chunks_count"] = None
                update_data["embedding_dimension"] = None
                update_data["sync_completed_at"] = None

        if not update_data:
            return {"success": False, "error": "No fields to update"}

        success = await self.mongodb.update_index(index_id, update_data)

        if not success:
            return {"success": False, "error": "Failed to update index"}

        updated_index = await self.mongodb.get_index(index_id)

        if not updated_index:
            return {"success": False, "error": "Failed to fetch updated index"}

        jobs = await self.mongodb.get_jobs_by_ids(updated_index.job_ids)

        jobs_info = [
            {"job_id": job.id, "filename": job.filename, "status": job.status}
            for job in jobs
        ]

        response_data = IndexResponse(
            index_id=index_id,
            project_id=updated_index.project_id,
            name=updated_index.name,
            description=updated_index.description,
            job_ids=updated_index.job_ids,
            status=updated_index.status,
            jobs_info=jobs_info,
        )

        return {"success": True, "data": response_data}

    async def start_sync(self, request: IndexSync) -> Dict[str, Any]:
        log_print(f"🚀 Starting sync request for index: {request.index_id}")

        index_doc = await self.mongodb.get_index(request.index_id)
        if not index_doc:
            return {"success": False, "error": "Index not found"}

        if index_doc.status == IndexStatus.SYNCING:
            return {
                "success": True,
                "data": {
                    "index_id": request.index_id,
                    "status": "syncing",
                    "message": "Sync already in progress",
                },
            }

        if index_doc.synced and index_doc.status == IndexStatus.SYNCED:
            return {
                "success": True,
                "data": {
                    "index_id": request.index_id,
                    "status": "synced",
                    "message": "Index already synced",
                    "chunks_count": index_doc.chunks_count or 0,
                },
            }

        await self.mongodb.update_index_status(
            request.index_id,
            IndexStatus.SYNCING,
            sync_started_at=datetime.now(),
            embedding_model=request.embedding_model,
        )

        log_print(f"📋 Sync task prepared for: {request.index_id}")

        return {
            "success": True,
            "data": {
                "index_id": request.index_id,
                "status": "syncing",
                "embedding_model": request.embedding_model,
                "job_count": len(index_doc.job_ids),
            },
        }

    async def sync_background_task(
        self,
        index_id: str,
        embedding_model: str,
        chunk_ratio: float,
        overlap_ratio: float,
    ):
        try:
            log_print(f"🔄 [SYNC] Starting background sync for index: {index_id}")

            index_doc = await self.mongodb.get_index(index_id)
            if not index_doc:
                raise Exception("Index not found during background sync")

            log_print(
                f"✅ [SYNC] Index found: {index_doc.name} (jobs: {len(index_doc.job_ids)})"
            )
            log_print(f"📊 [SYNC] Processing {len(index_doc.job_ids)} documents")

            all_documents = {}
            for job_id in index_doc.job_ids:
                try:
                    content = await self.minio.download_markdown(job_id)
                    all_documents[job_id] = content
                    log_print(f"📥 [SYNC] Downloaded content for job: {job_id}")
                except Exception as e:
                    log_print(f"⚠️ [SYNC] Failed to download job {job_id}: {str(e)}")
                    continue

            if not all_documents:
                raise Exception("No content downloaded from any job")

            all_chunks = []
            chunk_to_job_mapping = []

            for job_id, content in all_documents.items():
                log_print(f"🔪 [SYNC] Creating chunks for document: {job_id}")
                doc_chunks = create_chunks(content, chunk_ratio, overlap_ratio)

                if doc_chunks:
                    all_chunks.extend(doc_chunks)
                    chunk_to_job_mapping.extend([job_id] * len(doc_chunks))
                    log_print(
                        f"✅ [SYNC] Created {len(doc_chunks)} chunks for job: {job_id}"
                    )

            if not all_chunks:
                raise Exception("No chunks created")

            log_print(
                f"✅ [SYNC] Created {len(all_chunks)} chunks from {len(all_documents)} documents"
            )

            log_print(
                f"🤖 [SYNC] Getting embeddings from NVIDIA model: {embedding_model}"
            )
            log_print(
                f"📊 [SYNC] About to call NVIDIA API with {len(all_chunks)} texts"
            )

            embeddings = await self.nvidia.get_embeddings(all_chunks, embedding_model)
            log_print(
                f"✅ [SYNC] Got embeddings: {len(embeddings)} vectors, dimension: {len(embeddings[0])}"
            )

            collection_name = index_id
            log_print(
                f"🔧 [SYNC] Creating/checking Qdrant collection: {collection_name}"
            )
            await self.qdrant.create_collection(collection_name, len(embeddings[0]))

            await self.qdrant.upsert_points_with_metadata(
                collection_name, all_chunks, embeddings, chunk_to_job_mapping
            )

            await self.mongodb.update_index_status(
                index_id,
                IndexStatus.SYNCED,
                synced=True,
                chunks_count=len(all_chunks),
                embedding_dimension=len(embeddings[0]),
                sync_completed_at=datetime.now(),
            )

            log_print(
                f"✅ [SYNC] Background sync completed successfully for index: {index_id} with {len(index_doc.job_ids)} documents"
            )

        except Exception as e:
            log_print(
                f"❌ [SYNC] Background sync failed for index {index_id}: {str(e)}"
            )
            await self.mongodb.update_index_status(
                index_id,
                IndexStatus.SYNC_FAILED,
                sync_error=str(e),
                sync_failed_at=datetime.now(),
            )

    async def query_index(self, request: QueryRequest) -> Dict[str, Any]:
        log_print(f"🔍 Querying collection: {request.index_id}")

        index_doc = await self.mongodb.get_index(request.index_id)
        if not index_doc:
            return {"success": False, "error": "Index not found"}

        if not index_doc.synced or index_doc.status != IndexStatus.SYNCED:
            return {
                "success": False,
                "error": f"Index not ready for querying. Status: {index_doc.status}",
            }

        query_embedding = await self.nvidia.get_embeddings(
            [request.query],
            index_doc.embedding_model or "nvidia/llama-3.2-nv-embedqa-1b-v2",
        )

        results = await self.qdrant.search(
            request.index_id, query_embedding[0], request.top_k
        )

        log_print(f"✅ Query completed: {len(results)} results")

        response_data = QueryResponse(
            query=request.query,
            results=[
                {
                    "score": result.score,
                    "text": result.payload["text"] if result.payload else "",
                    "document_source": (
                        result.payload.get("document_source", "unknown")
                        if result.payload
                        else "unknown"
                    ),
                }
                for result in results
            ],
            index_info={
                "index_id": request.index_id,
                "name": index_doc.name,
                "documents_count": len(index_doc.job_ids),
                "chunks_count": index_doc.chunks_count or 0,
            },
        )

        return {"success": True, "data": response_data}

    async def list_project_indexes(self, project_id: str) -> Dict[str, Any]:
        project = await self.mongodb.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        indexes = await self.mongodb.list_indexes_by_project(project_id)

        indexes_data = []
        for index in indexes:
            jobs = await self.mongodb.get_jobs_by_ids(index.job_ids)
            index_data = index.model_dump()
            index_data["jobs_info"] = [
                {"job_id": job.id, "filename": job.filename, "status": job.status}
                for job in jobs
            ]
            indexes_data.append(index_data)

        return {
            "success": True,
            "data": {"project_id": project_id, "indexes": indexes_data},
        }

    async def get_index_status(self, index_id: str) -> Dict[str, Any]:
        index_doc = await self.mongodb.get_index(index_id)
        if not index_doc:
            return {"success": False, "error": "Index not found"}

        jobs = await self.mongodb.get_jobs_by_ids(index_doc.job_ids)
        jobs_info = [
            {
                "job_id": job.id,
                "filename": job.filename,
                "status": job.status,
                "file_size": job.file_size,
                "created_at": job.created_at,
            }
            for job in jobs
        ]

        index_data = index_doc.model_dump()
        index_data["jobs_info"] = jobs_info

        return {"success": True, "data": index_data}

    async def delete_index(self, index_id: str) -> Dict[str, Any]:
        index_doc = await self.mongodb.get_index(index_id)
        if not index_doc:
            return {"success": False, "error": "Index not found"}

        success = await self.mongodb.delete_index(index_id)

        if success:
            return {
                "success": True,
                "data": {
                    "message": f"Index {index_id} and vector DB collection deleted successfully"
                },
            }
        else:
            return {"success": False, "error": "Failed to delete index"}


index_service = IndexService()
