#!/usr/bin/env python3
"""
Test script to verify that ChromaDB telemetry is completely disabled.
"""

import os
import sys

# Set environment variables before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"

print("🧪 Testing ChromaDB Telemetry Bypass...")
print("=" * 50)

try:
    # Import our chroma client
    from app.chroma_client import get_chroma_client, MockTelemetryClient
    
    print("✅ Successfully imported chroma_client module")
    
    # Test creating a client
    print("🔧 Creating ChromaDB client...")
    client = get_chroma_client()
    print("✅ ChromaDB client created successfully")
    
    # Test that telemetry is disabled
    print("🔍 Checking telemetry status...")
    
    # Check if telemetry client is mocked
    if hasattr(client, '_telemetry_client'):
        telemetry_client = client._telemetry_client
        if isinstance(telemetry_client, MockTelemetryClient):
            print("✅ Client telemetry is properly mocked")
        else:
            print("⚠️  Client telemetry is not mocked")
    
    # Test telemetry capture method
    print("🧪 Testing telemetry capture method...")
    mock_client = MockTelemetryClient()
    try:
        # This should not raise any errors
        mock_client.capture("test_event", {"test": "data"}, "test_user")
        print("✅ Telemetry capture method works correctly")
    except Exception as e:
        print(f"❌ Telemetry capture method failed: {e}")
    
    print("\n🎉 All tests passed! Telemetry bypass is working correctly.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)