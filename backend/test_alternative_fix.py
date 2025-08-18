#!/usr/bin/env python3
"""
Test script for the alternative ChromaDB client implementation.
"""

import os
import sys

# Set environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "FALSE"

print("🧪 Testing Alternative ChromaDB Client...")
print("=" * 50)

try:
    # Import the alternative chroma client
    from app.chroma_client_no_telemetry import get_chroma_client
    
    print("✅ Successfully imported alternative chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
    print("✅ ChromaDB client created successfully")
    
    # Test basic operations
    print("🔍 Testing basic operations...")
    collections = client.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    print("\n🎉 All tests passed! Alternative client is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)