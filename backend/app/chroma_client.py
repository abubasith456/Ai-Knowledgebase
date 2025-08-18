"""
ChromaDB client wrapper with complete telemetry disable for version 0.5.5.
Aggressively prevents ChromaDB from loading its telemetry system.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Set all possible telemetry environment variables BEFORE any imports
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"
os.environ["CHROMA_SERVER_TELEMETRY"] = "FALSE"
os.environ["CHROMA_CLIENT_TELEMETRY"] = "FALSE"
os.environ["CHROMA_DISABLE_TELEMETRY"] = "TRUE"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "FALSE"

# Create a complete telemetry bypass
class CompleteTelemetryBypass:
    """Complete telemetry bypass that handles all possible telemetry calls."""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def capture(self, *args, **kwargs):
        """Handle any telemetry capture calls."""
        pass
    
    def __getattr__(self, name):
        """Handle any other telemetry methods."""
        return lambda *args, **kwargs: None

# Create a mock telemetry module that completely bypasses telemetry
def create_mock_telemetry_module():
    """Create a complete mock telemetry module."""
    mock_module = type(sys)('chromadb.telemetry')
    
    # Add all possible telemetry classes and functions
    mock_module.TelemetryClient = CompleteTelemetryBypass
    mock_module.telemetry_client = CompleteTelemetryBypass()
    mock_module.Telemetry = CompleteTelemetryBypass
    mock_module.telemetry = CompleteTelemetryBypass()
    
    # Add any other telemetry-related attributes
    mock_module.__all__ = ['TelemetryClient', 'telemetry_client', 'Telemetry', 'telemetry']
    
    return mock_module

# Aggressive module patching - patch BEFORE any ChromaDB imports
def disable_chromadb_telemetry_completely():
    """Completely disable ChromaDB telemetry at the module level."""
    
    # Create mock telemetry module
    mock_telemetry = create_mock_telemetry_module()
    
    # Patch all possible telemetry module paths
    telemetry_modules = [
        'chromadb.telemetry',
        'chromadb.telemetry.telemetry',
        'chromadb.telemetry.client',
        'chromadb.telemetry.events',
        'chromadb.telemetry.telemetry_client',
        'chromadb.telemetry.telemetry_client',
        'chromadb.telemetry.telemetry_client',
    ]
    
    # Patch each module
    for module_name in telemetry_modules:
        try:
            sys.modules[module_name] = mock_telemetry
        except:
            pass
    
    # Also patch any existing modules that might already be loaded
    for module_name in list(sys.modules.keys()):
        if 'chromadb' in module_name and 'telemetry' in module_name:
            try:
                sys.modules[module_name] = mock_telemetry
            except:
                pass

# Apply telemetry bypass BEFORE any ChromaDB imports
disable_chromadb_telemetry_completely()

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
                client._telemetry_client = CompleteTelemetryBypass()
            
            # Also check for internal client telemetry
            if hasattr(client, '_client') and hasattr(client._client, 'telemetry_client'):
                client._client.telemetry_client = CompleteTelemetryBypass()
            
            # Disable telemetry on any other attributes
            for attr_name in dir(client):
                attr = getattr(client, attr_name, None)
                if hasattr(attr, 'telemetry_client'):
                    setattr(attr, 'telemetry_client', CompleteTelemetryBypass())
                    
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