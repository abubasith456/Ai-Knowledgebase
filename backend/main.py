from fastapi import FastAPI
from app.routers import projects, documents, indexes

# Initialize FastAPI
app = FastAPI(
    title="Project & Index Management API",
    description="API for managing projects, documents (with async parsing), and indexes",
    version="1.0.0",
)

# --- Routers ---
# Project Routes
app.include_router(projects.router, prefix="/project", tags=["Projects"])

# Document Routes (with upload + status polling)
app.include_router(documents.router, prefix="/document", tags=["Documents"])

# Index Routes
app.include_router(indexes.router, prefix="/index", tags=["Indexes"])


# --- Root Health Check ---
@app.get("/")
def root():
    return {
        "message": "✅ Project-Index API Running",
        "routes": ["/project", "/document", "/index"],
    }
