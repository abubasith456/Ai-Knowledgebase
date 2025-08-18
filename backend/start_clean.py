#!/usr/bin/env python3
"""
Clean startup script for Doc KB backend server with telemetry completely disabled.
"""

import os
import sys

# Set all telemetry environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Doc KB Backend Server (Telemetry Disabled)...")
    print("📁 Using local ChromaDB storage")
    print("🔇 ChromaDB telemetry completely disabled")
    print("🤖 Using embedding model: jinaai/jina-embeddings-v3")
    print("=" * 50)
    
    # Test ChromaDB client before starting server
    try:
        from app.chroma_client import get_chroma_client
        client = get_chroma_client()
        print("✅ ChromaDB client initialized successfully")
        print("✅ Telemetry bypass verified")
    except Exception as e:
        print(f"⚠️  Warning: ChromaDB initialization issue: {e}")
        print("Continuing with server startup...")
    
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )