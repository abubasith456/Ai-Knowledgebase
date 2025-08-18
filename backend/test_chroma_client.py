#!/usr/bin/env python3
"""
Simple test script to verify ChromaDB client works without telemetry.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing Clean ChromaDB Client...")
print("=" * 50)

try:
    # Import chroma_client directly without importing the full app
    import chromadb
    from chromadb.config import Settings
    from pathlib import Path
    from loguru import logger
    
    print("✅ Successfully imported ChromaDB")
    
    # Test creating a client directly
    print("🔧 Creating ChromaDB client...")
    
    # Create settings with telemetry disabled
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
    
    # Create client
    data_dir = Path("./data/chroma")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(data_dir),
        settings=settings
    )
    
    print("✅ ChromaDB client created successfully")
    
    # Test basic operations
    print("🔍 Testing basic operations...")
    
    # List collections
    collections = client.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    print("\n🎉 All tests passed! ChromaDB client is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)