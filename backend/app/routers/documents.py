# app/routers/documents.py
from fastapi import APIRouter, HTTPException
from app.repository.db import documents_store

router = APIRouter()


@router.get("/{doc_id}/status")
async def check_document_status(doc_id: str):
    docs = await documents_store.load()
    doc = docs.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "status": doc.get("status", "pending")}
