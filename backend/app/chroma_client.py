"""
Custom ChromaDB client wrapper that completely disables telemetry.
"""

import os
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import Optional
from loguru import logger

# Force disable telemetry at the module level
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMA_TELEMETRY"] = "FALSE"

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
        
        # Force disable telemetry on the client
        try:
            if hasattr(client, '_client') and hasattr(client._client, 'telemetry_client'):
                client._client.telemetry_client = None
                logger.info("Telemetry disabled on ChromaDB client")
        except Exception as e:
            logger.warning(f"Could not disable telemetry: {e}")
        
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
                    client.delete_collection(name=collection.name)
                    cleaned_count += 1
                else:
                    logger.warning(f"Error checking collection {collection.name}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} incompatible collections")
        
    except Exception as e:
        logger.warning(f"Failed to cleanup collections: {e}")

# Run cleanup on module import
cleanup_incompatible_collections()