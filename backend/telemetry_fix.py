"""
AGGRESSIVE ChromaDB Telemetry Disabler
This module must be imported BEFORE any other modules that might import chromadb.
It completely bypasses telemetry at the system level.
"""

import os
import sys
import types

# Set environment variables immediately
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"

# Create a completely mock telemetry client
class MockTelemetryClient:
    """Mock telemetry client that does absolutely nothing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None
    
    def __call__(self, *args, **kwargs):
        return self

# Create a mock telemetry module
mock_telemetry_module = types.ModuleType('chromadb.telemetry')
mock_telemetry_module.TelemetryClient = MockTelemetryClient
mock_telemetry_module.ProductTelemetryClient = MockTelemetryClient
mock_telemetry_module.ClientStartEvent = MockTelemetryClient()
mock_telemetry_module.CollectionGetEvent = MockTelemetryClient()
mock_telemetry_module.CollectionQueryEvent = MockTelemetryClient()
mock_telemetry_module.CollectionCreateEvent = MockTelemetryClient()
mock_telemetry_module.CollectionDeleteEvent = MockTelemetryClient()

# Create mock product module
mock_product_module = types.ModuleType('chromadb.telemetry.product')
mock_product_module.ProductTelemetryClient = MockTelemetryClient
mock_product_module.ClientStartEvent = MockTelemetryClient()

# Create mock events module
mock_events_module = types.ModuleType('chromadb.telemetry.product.events')
mock_events_module.ClientStartEvent = MockTelemetryClient()

# Create mock opentelemetry module
mock_opentelemetry_module = types.ModuleType('chromadb.telemetry.opentelemetry')
mock_opentelemetry_module.OpenTelemetryClient = MockTelemetryClient
mock_opentelemetry_module.OpenTelemetryGranularity = MockTelemetryClient()
mock_opentelemetry_module.trace_method = lambda *args, **kwargs: lambda func: func

# Insert our mock modules into sys.modules BEFORE any real imports
# Only mock the telemetry module, not the entire chromadb
sys.modules['chromadb.telemetry'] = mock_telemetry_module
sys.modules['chromadb.telemetry.product'] = mock_product_module
sys.modules['chromadb.telemetry.product.events'] = mock_events_module
sys.modules['chromadb.telemetry.opentelemetry'] = mock_opentelemetry_module

# Also mock any potential telemetry-related modules
sys.modules['chromadb.telemetry.telemetry'] = mock_telemetry_module
sys.modules['chromadb.telemetry.events'] = mock_telemetry_module
sys.modules['chromadb.telemetry.telemetry_client'] = mock_telemetry_module

print("🔇 ChromaDB telemetry completely disabled at system level")