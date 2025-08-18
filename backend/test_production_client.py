#!/usr/bin/env python3
"""
Test script for production ChromaDB client.
"""

import os
import sys

print("🧪 Testing Production ChromaDB Client...")
print("=" * 50)

try:
    # Import the production chroma client
    from production_chroma_client import get_chroma_client, get_chroma_manager
    
    print("✅ Successfully imported production chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
    print("✅ ChromaDB client created successfully")
    
    # Test manager
    print("🔧 Testing ChromaDB manager...")
    manager = get_chroma_manager()
    print("✅ ChromaDB manager created successfully")
    
    # Test basic operations
    print("🔍 Testing basic operations...")
    collections = manager.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    # Test cleanup
    print("🧹 Testing cleanup function...")
    cleaned = manager.cleanup_incompatible_collections()
    print(f"✅ Cleanup completed, removed {cleaned} incompatible collections")
    
    print("\n🎉 All tests passed! Production client is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)