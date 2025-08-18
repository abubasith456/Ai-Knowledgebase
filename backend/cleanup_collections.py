#!/usr/bin/env python3
"""
Standalone script to clean up old ChromaDB collections with incompatible embedding dimensions.
Run this script to remove old collections before starting the server.
"""

import os
import chromadb
from chromadb.config import Settings
from pathlib import Path

# Set environment variables
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

def cleanup_old_collections():
    """Clean up old collections that have incompatible embedding dimensions."""
    try:
        # Get data directory
        data_dir = Path(os.environ.get("CHROMA_DATA_DIR") or "./data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create client
        client = chromadb.PersistentClient(
            path=str(data_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        collections = client.list_collections()
        print(f"Found {len(collections)} collections")
        
        cleaned_count = 0
        for collection in collections:
            try:
                # Try to get collection info to check if it's compatible
                collection.get()
                print(f"✓ Collection {collection.name} is compatible")
            except Exception as e:
                if "Embedding dimension" in str(e):
                    print(f"🗑️  Deleting incompatible collection: {collection.name}")
                    client.delete_collection(name=collection.name)
                    cleaned_count += 1
                else:
                    print(f"⚠️  Error checking collection {collection.name}: {e}")
        
        print(f"\nCleanup complete! Deleted {cleaned_count} incompatible collections.")
        
    except Exception as e:
        print(f"❌ Failed to cleanup old collections: {e}")

if __name__ == "__main__":
    print("Cleaning up old ChromaDB collections...")
    cleanup_old_collections()