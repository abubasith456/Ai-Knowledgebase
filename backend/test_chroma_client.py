#!/usr/bin/env python3
"""
Simple test script to verify ChromaDB client works without telemetry.
"""

import os
import sys

print("🧪 Testing Clean ChromaDB Client...")
print("=" * 50)

try:
    # Import our chroma client
    from app.chroma_client import get_chroma_client
    
    print("✅ Successfully imported chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
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