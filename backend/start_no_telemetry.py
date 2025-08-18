#!/usr/bin/env python3
"""
Production startup script with aggressive telemetry disabling.
This script ensures ChromaDB telemetry is completely disabled before any imports.
"""

import os
import sys
from pathlib import Path

# Set environment variables immediately
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import our aggressive telemetry fix FIRST
import telemetry_fix

print("🚀 Starting Doc KB Backend Server (Zero Telemetry Mode)...")
print("📁 Using local ChromaDB storage")
print("🔇 ChromaDB telemetry completely disabled")
print("🤖 Using embedding model: jinaai/jina-embeddings-v3")
print("🛡️  Production-level telemetry bypass active")
print("=" * 60)

# Now import and start the server
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for production
        log_level="info"
    )