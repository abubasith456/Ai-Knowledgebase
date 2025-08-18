#!/usr/bin/env python3
"""
Test script for clean ChromaDB client (version 0.4.22).
"""

import os
import sys

print("🧪 Testing Clean ChromaDB Client (v0.4.22)...")
print("=" * 50)

try:
    # Import the clean chroma client
    from app.chroma_client_clean import get_chroma_client
    
    print("✅ Successfully imported clean chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
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