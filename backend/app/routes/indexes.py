from fastapi import APIRouter, BackgroundTasks

from app.models.schemas import IndexCreate, IndexSync, QueryRequest, IndexUpdate
from app.models.response import StandardResponse
from app.services.index_service import index_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/{project_id}/create")
async def create_index(project_id: str, request: IndexCreate):
    try:
        result = await index_service.create_index(project_id, request)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to create index: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/sync")
async def sync_index(request: IndexSync, background_tasks: BackgroundTasks):
    try:
        result = await index_service.start_sync(request)
        if result["success"]:
            background_tasks.add_task(
                index_service.sync_background_task,
                request.index_id,
                request.embedding_model,
                request.chunk_ratio,
                request.overlap_ratio,
            )
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Sync failed: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/query")
async def query_index(request: QueryRequest):
    try:
        result = await index_service.query_index(request)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Query failed: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{project_id}/")
async def list_project_indexes(project_id: str):
    try:
        result = await index_service.list_project_indexes(project_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to list project indexes: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/{index_id}")
async def get_index_status(index_id: str):
    try:
        result = await index_service.get_index_status(index_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to get index status: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.put("/{index_id}")
async def update_index(index_id: str, request: IndexUpdate):
    try:
        result = await index_service.update_index(index_id, request)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to update index: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/{index_id}")
async def delete_index(index_id: str):
    try:
        result = await index_service.delete_index(index_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to delete index: {str(e)}")
        return StandardResponse.failed(error=str(e))
