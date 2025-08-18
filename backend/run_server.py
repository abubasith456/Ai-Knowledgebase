#!/usr/bin/env python3
"""
Simple startup script for Doc KB backend server.
"""

import os
import sys

# Set environment variables
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Doc KB Backend Server...")
    print("📁 Using local ChromaDB storage")
    print("🤖 Using embedding model: jinaai/jina-embeddings-v3")
    print("=" * 50)
    
    # Test ChromaDB client before starting server
    try:
        from app.chroma_client import get_chroma_client
        client = get_chroma_client()
        print("✅ ChromaDB client initialized successfully")
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