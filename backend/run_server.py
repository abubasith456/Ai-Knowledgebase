#!/usr/bin/env python3
"""
Simple startup script for Doc KB backend server.
Ensures proper environment setup and starts the server.
"""

import os
import sys

# Set environment variables before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Doc KB Backend Server...")
    print("📁 Using local ChromaDB storage")
    print("🔇 ChromaDB telemetry disabled")
    print("🤖 Using embedding model: jinaai/jina-embeddings-v3")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )