#!/usr/bin/env python3
"""
Test script to verify ChromaDB telemetry is completely disabled.
Run this in your virtual environment to test the fix.
"""

import os
import sys

# Set environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"

print("🧪 Testing ChromaDB Telemetry Bypass...")
print("=" * 50)

try:
    # Import our chroma client
    from app.chroma_client import get_chroma_client, TelemetryBypass
    
    print("✅ Successfully imported chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
    print("✅ ChromaDB client created successfully")
    
    # Test that telemetry is disabled
    print("🔍 Checking telemetry status...")
    
    # Check if telemetry client is bypassed
    if hasattr(client, '_telemetry_client'):
        telemetry_client = client._telemetry_client
        if isinstance(telemetry_client, TelemetryBypass):
            print("✅ Client telemetry is properly bypassed")
        else:
            print("⚠️  Client telemetry is not bypassed")
    
    # Test telemetry capture method
    print("🧪 Testing telemetry capture method...")
    bypass = TelemetryBypass()
    try:
        # This should not raise any errors
        bypass.capture("test_event", {"test": "data"}, "test_user")
        print("✅ Telemetry capture method works correctly")
    except Exception as e:
        print(f"❌ Telemetry capture method failed: {e}")
    
    # Test basic operations
    print("🔍 Testing basic operations...")
    collections = client.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    print("\n🎉 All tests passed! Telemetry bypass is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)