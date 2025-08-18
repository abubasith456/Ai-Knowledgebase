"""
ChromaDB client wrapper with aggressive telemetry bypass for version 0.5.5.
Completely disables ChromaDB's internal telemetry system.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Set all possible telemetry environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"

# Create a complete telemetry bypass
class TelemetryBypass:
    """Complete telemetry bypass for ChromaDB 0.5.5."""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        """Handle any telemetry capture calls."""
        pass
    
    def __getattr__(self, name):
        """Handle any other telemetry methods."""
        return lambda *args, **kwargs: None

# Aggressive module patching before importing chromadb
def disable_chromadb_telemetry():
    """Completely disable ChromaDB telemetry at the module level."""
    
    # Create a mock telemetry module
    mock_telemetry = type(sys)('chromadb.telemetry')
    mock_telemetry.TelemetryClient = TelemetryBypass
    mock_telemetry.telemetry_client = TelemetryBypass()
    mock_telemetry.Telemetry = TelemetryBypass
    
    # Patch all possible telemetry module paths
    telemetry_modules = [
        'chromadb.telemetry',
        'chromadb.telemetry.telemetry',
        'chromadb.telemetry.client',
        'chromadb.telemetry.events',
        'chromadb.telemetry.telemetry_client',
        'chromadb.telemetry.telemetry_client',
    ]
    
    for module_name in telemetry_modules:
        try:
            sys.modules[module_name] = mock_telemetry
        except:
            pass

# Apply telemetry bypass before any ChromaDB imports
disable_chromadb_telemetry()

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
        
        # Apply telemetry bypass to the client instance
        try:
            # Replace telemetry client with our bypass
            if hasattr(client, '_telemetry_client'):
                client._telemetry_client = TelemetryBypass()
            
            # Also check for internal client telemetry
            if hasattr(client, '_client') and hasattr(client._client, 'telemetry_client'):
                client._client.telemetry_client = TelemetryBypass()
            
            # Disable telemetry on any other attributes
            for attr_name in dir(client):
                attr = getattr(client, attr_name, None)
                if hasattr(attr, 'telemetry_client'):
                    setattr(attr, 'telemetry_client', TelemetryBypass())
                    
        except Exception as e:
            logger.debug(f"Telemetry bypass applied: {e}")
        
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