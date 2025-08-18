"""
Production-level ChromaDB client wrapper that completely bypasses telemetry.
Monkey-patches the telemetry system before any ChromaDB imports.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Force disable telemetry at the module level
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"

# MONKEY PATCH: Disable telemetry before importing chromadb
class MockTelemetryClient:
    """Mock telemetry client that does nothing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Patch the telemetry module before importing chromadb
sys.modules['chromadb.telemetry'] = type(sys)('chromadb.telemetry')
sys.modules['chromadb.telemetry'].TelemetryClient = MockTelemetryClient

# Now import chromadb after patching
import chromadb
from chromadb.config import Settings

def get_chroma_client() -> chromadb.Client:
    """
    Get a ChromaDB client with telemetry completely disabled.
    Production-level fix that bypasses telemetry entirely.
    """
    host = os.environ.get("CHROMA_HOST")
    
    if host:
        # Remote client
        return chromadb.HttpClient(
            host=host, 
            port=int(os.environ.get("CHROMA_PORT", "8000"))
        )
    else:
        # Local persistent client
        data_dir = Path(os.environ.get("CHROMA_DATA_DIR") or "./data/chroma")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using local ChromaDB storage at: {data_dir}")
        
        # Create settings with telemetry completely disabled
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
        
        # Create client
        client = chromadb.PersistentClient(
            path=str(data_dir),
            settings=settings
        )
        
        # Additional telemetry bypass for production
        try:
            # Disable telemetry on the client instance
            if hasattr(client, '_client') and hasattr(client._client, 'telemetry_client'):
                client._client.telemetry_client = MockTelemetryClient()
            
            # Disable telemetry on collection instances
            if hasattr(client, '_telemetry_client'):
                client._telemetry_client = MockTelemetryClient()
                
        except Exception as e:
            logger.debug(f"Telemetry bypass completed: {e}")
        
        return client

def cleanup_incompatible_collections():
    """
    Clean up collections with incompatible embedding dimensions.
    Production-level cleanup with proper error handling.
    """
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        
        cleaned_count = 0
        for collection in collections:
            try:
                # Test if collection is compatible
                collection.get()
                logger.debug(f"Collection {collection.name} is compatible")
            except Exception as e:
                if "Embedding dimension" in str(e):
                    logger.info(f"Deleting incompatible collection: {collection.name}")
                    try:
                        client.delete_collection(name=collection.name)
                        cleaned_count += 1
                    except Exception as delete_error:
                        logger.warning(f"Failed to delete collection {collection.name}: {delete_error}")
                else:
                    logger.debug(f"Collection {collection.name} check: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} incompatible collections")
        
    except Exception as e:
        logger.warning(f"Collection cleanup error: {e}")

# Run cleanup on module import
cleanup_incompatible_collections()