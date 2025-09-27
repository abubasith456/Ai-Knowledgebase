from fastapi import APIRouter, BackgroundTasks
from typing import List
from datetime import datetime

from app.models.schemas import (
    IndexCreate,
    IndexSync,
    QueryRequest,
    IndexResponse,
    QueryResponse,
    JobStatus,
    IndexStatus,
)
from app.models.response import StandardResponse
from app.services.mongodb_service import mongodb_service
from app.services.minio_service import minio_service
from app.services.nvidia_service import nvidia_service
from app.services.qdrant_service import qdrant_service
from app.utils.chunking import create_chunks
from app.utils.logging import log_print

router = APIRouter()


@router.post("/{project_id}/create", response_model=StandardResponse[IndexResponse])
async def create_index(project_id: str, request: IndexCreate):
    """Create a new index from completed jobs (max 5 jobs)"""
    try:
        # Verify project exists
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        # Validate job_ids count
        if len(request.job_ids) == 0:
            return StandardResponse.failed(error="At least one job_id is required")
        if len(request.job_ids) > 5:
            return StandardResponse.failed(error="Maximum 5 jobs allowed per index")

        # Verify all jobs exist and are completed
        jobs = mongodb_service.get_jobs_by_ids(request.job_ids)

        if len(jobs) != len(request.job_ids):
            return StandardResponse.failed(error="One or more jobs not found")

        incomplete_jobs = [job for job in jobs if job.status != JobStatus.COMPLETED]
        if incomplete_jobs:
            return StandardResponse.failed(
                error=f"Jobs not completed: {[job.id for job in incomplete_jobs]}"
            )

        # Verify all jobs belong to the same project
        wrong_project_jobs = [job for job in jobs if job.project_id != project_id]
        if wrong_project_jobs:
            return StandardResponse.failed(
                error=f"Jobs belong to different project: {[job.id for job in wrong_project_jobs]}"
            )

        # Create index
        index_id = mongodb_service.create_index(
            project_id, request.name, request.job_ids, request.description
        )

        # Get job info for response
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

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Failed to create index: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/sync", response_model=StandardResponse)
async def sync_index(request: IndexSync, background_tasks: BackgroundTasks):
    """Start background sync process for index"""
    try:
        log_print(f"🚀 Starting sync request for index: {request.index_id}")

        index_doc = mongodb_service.get_index(request.index_id)
        if not index_doc:
            return StandardResponse.failed(error="Index not found")

        if index_doc.status == IndexStatus.SYNCING:
            return StandardResponse.success(
                data={
                    "index_id": request.index_id,
                    "status": "syncing",
                    "message": "Sync already in progress",
                }
            )

        if index_doc.synced and index_doc.status == IndexStatus.SYNCED:
            return StandardResponse.success(
                data={
                    "index_id": request.index_id,
                    "status": "synced",
                    "message": "Index already synced",
                    "chunks_count": index_doc.chunks_count or 0,
                }
            )

        # Update status immediately
        mongodb_service.update_index_status(
            request.index_id,
            IndexStatus.SYNCING,
            sync_started_at=datetime.now(),
            embedding_model=request.embedding_model,
        )

        log_print(f"📋 Added background task for sync: {request.index_id}")

        # Start background sync
        background_tasks.add_task(
            sync_background_task,
            request.index_id,
            request.embedding_model,
            request.chunk_ratio,
            request.overlap_ratio,
        )

        return StandardResponse.success(
            data={
                "index_id": request.index_id,
                "status": "syncing",
                "message": "Background sync started",
                "embedding_model": request.embedding_model,
                "job_count": len(index_doc.job_ids),
            }
        )

    except Exception as e:
        log_print(f"❌ Sync failed: {str(e)}")
        return StandardResponse.failed(error=str(e))


def sync_background_task(
    index_id: str, embedding_model: str, chunk_ratio: float, overlap_ratio: float
):
    """Background sync task for multiple documents"""
    try:
        log_print(f"🔄 [SYNC] Starting background sync for index: {index_id}")

        index_doc = mongodb_service.get_index(index_id)
        if not index_doc:
            raise Exception("Index not found during background sync")

        log_print(
            f"✅ [SYNC] Index found: {index_doc.name} (jobs: {len(index_doc.job_ids)})"
        )
        log_print(f"📊 [SYNC] Processing {len(index_doc.job_ids)} documents")

        # Download and combine content from all jobs
        all_content = []
        for job_id in index_doc.job_ids:
            try:
                content = minio_service.download_markdown(job_id)
                all_content.append(f"# Document: {job_id}\n\n{content}")
                log_print(f"📥 [SYNC] Downloaded content for job: {job_id}")
            except Exception as e:
                log_print(f"⚠️ [SYNC] Failed to download job {job_id}: {str(e)}")
                continue

        if not all_content:
            raise Exception("No content downloaded from any job")

        # Combine all documents
        combined_content = "\n\n---\n\n".join(all_content)
        log_print(f"📝 [SYNC] Combined content: {len(combined_content)} chars")

        # Create chunks from combined content
        log_print(
            f"🔪 [SYNC] Creating chunks with ratio {chunk_ratio}, overlap {overlap_ratio}"
        )
        chunks = create_chunks(combined_content, chunk_ratio, overlap_ratio)
        if not chunks:
            raise Exception("No chunks created")

        log_print(
            f"✅ [SYNC] Created {len(chunks)} chunks from {len(all_content)} documents"
        )

        # NVIDIA API Call
        log_print(f"🤖 [SYNC] Getting embeddings from NVIDIA model: {embedding_model}")
        log_print(f"📊 [SYNC] About to call NVIDIA API with {len(chunks)} texts")

        # Get embeddings
        embeddings = nvidia_service.get_embeddings(chunks, embedding_model)
        log_print(
            f"✅ [SYNC] Got embeddings: {len(embeddings)} vectors, dimension: {len(embeddings[0])}"
        )

        # Create Qdrant collection
        collection_name = index_id
        log_print(f"🔧 [SYNC] Creating/checking Qdrant collection: {collection_name}")
        qdrant_service.create_collection(collection_name, len(embeddings[0]))

        # Upsert points with document source information
        enhanced_chunks = []
        enhanced_embeddings = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Try to identify which document this chunk came from
            doc_source = "unknown"
            for j, job_id in enumerate(index_doc.job_ids):
                if f"Document: {job_id}" in chunk:
                    doc_source = job_id
                    break

            enhanced_chunks.append(chunk)
            enhanced_embeddings.append(embedding)

        qdrant_service.upsert_points_with_metadata(
            collection_name, enhanced_chunks, enhanced_embeddings, index_doc.job_ids
        )

        # Update completion status
        mongodb_service.update_index_status(
            index_id,
            IndexStatus.SYNCED,
            synced=True,
            chunks_count=len(chunks),
            embedding_dimension=len(embeddings[0]),
            sync_completed_at=datetime.now(),
        )

        log_print(
            f"✅ [SYNC] Background sync completed successfully for index: {index_id} with {len(index_doc.job_ids)} documents"
        )

    except Exception as e:
        log_print(f"❌ [SYNC] Background sync failed for index {index_id}: {str(e)}")
        mongodb_service.update_index_status(
            index_id,
            IndexStatus.SYNC_FAILED,
            sync_error=str(e),
            sync_failed_at=datetime.now(),
        )


@router.post("/query", response_model=StandardResponse[QueryResponse])
async def query_index(request: QueryRequest):
    """Query index for similar content"""
    try:
        log_print(f"🔍 Querying collection: {request.index_id}")

        index_doc = mongodb_service.get_index(request.index_id)
        if not index_doc:
            return StandardResponse.failed(error="Index not found")

        if not index_doc.synced or index_doc.status != IndexStatus.SYNCED:
            return StandardResponse.failed(
                error=f"Index not ready for querying. Status: {index_doc.status}"
            )

        # Get query embedding
        query_embedding = nvidia_service.get_embeddings(
            [request.query],
            index_doc.embedding_model or "nvidia/llama-3.2-nv-embedqa-1b-v2",
        )[0]

        # Search in Qdrant
        results = qdrant_service.search(
            request.index_id, query_embedding, request.top_k
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

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Query failed: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/", response_model=StandardResponse)
async def list_project_indexes(project_id: str):
    """List all indexes for a project"""
    try:
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        indexes = mongodb_service.list_indexes_by_project(project_id)

        # Add job info to each index
        indexes_data = []
        for index in indexes:
            jobs = mongodb_service.get_jobs_by_ids(index.job_ids)
            index_data = index.model_dump()
            index_data["jobs_info"] = [
                {"job_id": job.id, "filename": job.filename, "status": job.status}
                for job in jobs
            ]
            indexes_data.append(index_data)

        return StandardResponse.success(
            data={"project_id": project_id, "indexes": indexes_data}
        )

    except Exception as e:
        log_print(f"❌ Failed to list project indexes: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{index_id}", response_model=StandardResponse)
async def get_index_status(index_id: str):
    """Get index status with job details"""
    try:
        index_doc = mongodb_service.get_index(index_id)
        if not index_doc:
            return StandardResponse.failed(error="Index not found")

        # Get job details
        jobs = mongodb_service.get_jobs_by_ids(index_doc.job_ids)
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

        return StandardResponse.success(data=index_data)

    except Exception as e:
        log_print(f"❌ Failed to get index status: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/{index_id}", response_model=StandardResponse)
async def delete_index(index_id: str):
    """Delete an index with Qdrant cleanup"""
    try:
        index_doc = mongodb_service.get_index(index_id)
        if not index_doc:
            return StandardResponse.failed(error="Index not found")

        success = mongodb_service.delete_index(index_id)

        if success:
            return StandardResponse.success(
                data={
                    "message": f"Index {index_id} and vector DB collection deleted successfully"
                }
            )
        else:
            return StandardResponse.failed(error="Failed to delete index")

    except Exception as e:
        log_print(f"❌ Failed to delete index: {str(e)}")
        return StandardResponse.failed(error=str(e))
