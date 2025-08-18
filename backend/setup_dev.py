#!/usr/bin/env python3
"""
Development setup script for Doc KB backend.
Creates necessary directories and sets up the development environment.
"""

import os
from pathlib import Path

def setup_dev_environment():
    """Set up the development environment."""
    print("Setting up Doc KB development environment...")
    
    # Create necessary directories
    directories = [
        "./data/indices",
        "./data/uploads", 
        "./data/chroma"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # Set environment variables for development
    os.environ.setdefault("INDICES_DIR", "./data/indices")
    os.environ.setdefault("CHROMA_DATA_DIR", "./data/chroma")
    os.environ.setdefault("API_KEY_SECRET", "dev-secret-key-change-in-production")
    os.environ.setdefault("MODEL_NAME", "jinaai/jina-embeddings-v3-small")
    os.environ.setdefault("COLLECTION_PREFIX", "kb_")
    os.environ.setdefault("LOG_LEVEL", "info")
    
    print("✓ Environment variables set for development")
    print("✓ Development environment setup complete!")
    print("\nYou can now run:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    setup_dev_environment()