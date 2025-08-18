"""
Clean ChromaDB client wrapper with complete telemetry disable.
Aggressively disables ChromaDB's internal telemetry system.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Completely disable telemetry at the system level
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"

# Aggressive telemetry bypass - patch before importing chromadb
class NoOpTelemetry:
    """Complete no-op telemetry replacement."""
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Patch all possible telemetry modules before importing chromadb
def disable_chroma_telemetry():
    """Completely disable ChromaDB telemetry."""
    # Create mock telemetry modules
    mock_telemetry = type(sys)('chromadb.telemetry')
    mock_telemetry.TelemetryClient = NoOpTelemetry
    mock_telemetry.telemetry_client = NoOpTelemetry()
    
    # Patch all possible telemetry paths
    telemetry_paths = [
        'chromadb.telemetry',
        'chromadb.telemetry.telemetry',
        'chromadb.telemetry.client',
        'chromadb.telemetry.events',
        'chromadb.telemetry.telemetry_client',
    ]
    
    for path in telemetry_paths:
        try:
            sys.modules[path] = mock_telemetry
        except:
            pass

# Disable telemetry before importing chromadb
disable_chroma_telemetry()

# Now import chromadb
import chromadb
from chromadb.config import Settings

def get_chroma_client() -> chromadb.Client:
    """
    Get a ChromaDB client with telemetry completely disabled.
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
        
        # Create settings with telemetry disabled
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
        
        # Additional telemetry disable on client
        try:
            # Disable telemetry on client instance
            if hasattr(client, '_telemetry_client'):
                client._telemetry_client = NoOpTelemetry()
            
            # Disable telemetry on internal client
            if hasattr(client, '_client') and hasattr(client._client, 'telemetry_client'):
                client._client.telemetry_client = NoOpTelemetry()
                
        except Exception as e:
            logger.debug(f"Telemetry disable completed: {e}")
        
        return client

def cleanup_incompatible_collections():
    """
    Clean up collections with incompatible embedding dimensions.
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