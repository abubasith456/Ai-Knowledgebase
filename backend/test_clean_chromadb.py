#!/usr/bin/env python3
"""
Test script for clean ChromaDB client (version 0.4.22).
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing Clean ChromaDB Client (v0.4.22)...")
print("=" * 50)

try:
    # Import chromadb directly
    import chromadb
    from chromadb.config import Settings
    from pathlib import Path
    from loguru import logger
    
    print("✅ Successfully imported ChromaDB 0.4.22")
    
    # Test creating a client directly
    print("🔧 Creating ChromaDB client...")
    
    # Create settings
    settings = Settings(
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
    collections = client.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    print("\n🎉 All tests passed! Clean client is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)