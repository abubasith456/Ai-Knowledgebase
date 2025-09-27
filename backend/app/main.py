from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import documents, indexes, health, projects
from app.utils.logging import setup_logging
from app.config import settings

# Setup logging
setup_logging()

app = FastAPI(
    title="Knowledge Base API",
    description="Production Knowledge Base with Projects, Multi-Document Indexing, Docling, Qdrant, and NVIDIA",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(indexes.router, prefix="/api/indexes", tags=["Indexes"])


@app.get("/")
async def root():
    return {
        "message": "Knowledge Base API v2.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "features": [
            "Project Management",
            "Multi-Document Indexing (max 5 docs)",
            "Docling OCR Processing",
            "Qdrant Vector Storage",
            "NVIDIA Embeddings",
            "Delete Operations",
        ],
    }
