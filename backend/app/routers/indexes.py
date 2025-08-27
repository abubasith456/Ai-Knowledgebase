# app/routers/indexes.py
from fastapi import APIRouter, HTTPException
from app.models import Index, IndexCreate, QueryRequest
from app.repository.db import indexes_store

router = APIRouter()


async def _next_id(store) -> int:
    data = await store.load()
    return (max(map(int, data.keys())) + 1) if data else 1


@router.post("/")
async def create_index(payload: IndexCreate):
    idx = Index(
        name=payload.name,
        project_uuid=payload.project_uuid,
        document_ids=payload.document_ids,
    )
    await indexes_store.upsert(str(idx.index_uuid), idx.dict())
    return idx


@router.delete("/{index_id}")
async def delete_index(index_id: int):
    await indexes_store.delete(str(index_id))
    return {"message": "Index deleted"}
