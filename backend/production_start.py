#!/usr/bin/env python3
"""
Production-level startup script for Doc KB backend server.
Completely disables ChromaDB telemetry before any imports.
"""

import os
import sys
from pathlib import Path

# Set environment variables first
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# MONKEY PATCH: Disable ChromaDB telemetry at the system level
class MockTelemetryClient:
    """Mock telemetry client that does nothing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Create mock telemetry module
mock_telemetry = type(sys)('chromadb.telemetry')
mock_telemetry.TelemetryClient = MockTelemetryClient
sys.modules['chromadb.telemetry'] = mock_telemetry

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Doc KB Backend Server (Production Mode)...")
    print("📁 Using local ChromaDB storage")
    print("🔇 ChromaDB telemetry completely disabled")
    print("🤖 Using embedding model: jinaai/jina-embeddings-v3")
    print("🛡️  Production-level telemetry bypass active")
    print("=" * 60)
    
    # Import app after telemetry is disabled
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for production
        log_level="info"
    )