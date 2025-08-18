#!/usr/bin/env python3
"""
Startup script for the Doc KB backend server.
Sets environment variables before importing any modules to ensure proper configuration.
"""

import os
import sys

# Set environment variables before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Now import and run the server
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("Starting Doc KB backend server...")
    print("ChromaDB telemetry disabled")
    print("Using embedding model: jinaai/jina-embeddings-v3")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )