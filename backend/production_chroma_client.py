"""
Production-level ChromaDB client wrapper for version 0.4.15.
Comprehensive error handling, logging, and stability features.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import traceback

# Import chromadb
import chromadb
from chromadb.config import Settings

class ChromaDBManager:
    """Production-level ChromaDB manager with comprehensive error handling."""
    
    def __init__(self, data_dir: Optional[str] = None, host: Optional[str] = None, port: int = 8000):
        self.data_dir = Path(data_dir) if data_dir else Path(os.environ.get("CHROMA_DATA_DIR") or "./data/chroma")
        self.host = host or os.environ.get("CHROMA_HOST")
        self.port = int(os.environ.get("CHROMA_PORT", port))
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize ChromaDB client with retry logic."""
        for attempt in range(max_retries):
            try:
                if self.host:
                    # Remote client
                    logger.info(f"Connecting to remote ChromaDB at {self.host}:{self.port}")
                    self.client = chromadb.HttpClient(
                        host=self.host,
                        port=self.port
                    )
                else:
                    # Local persistent client
                    self._ensure_data_directory()
                    logger.info(f"Using local ChromaDB storage at: {self.data_dir}")
                    
                    # Create settings
                    settings = Settings(
                        allow_reset=True,
                        is_persistent=True
                    )
                    
                    # Create client
                    self.client = chromadb.PersistentClient(
                        path=str(self.data_dir),
                        settings=settings
                    )
                
                # Test the connection
                self._test_connection()
                logger.info("✅ ChromaDB client initialized successfully")
                return
                
            except Exception as e:
                logger.warning(f"ChromaDB initialization attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize ChromaDB after {max_retries} attempts")
                    raise
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists and is clean."""
        try:
            if self.data_dir.exists():
                # Check if directory is corrupted
                if self._is_directory_corrupted():
                    logger.warning("Detected corrupted ChromaDB data directory, clearing...")
                    self._clear_data_directory()
            
            # Create directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Data directory ready: {self.data_dir}")
            
        except Exception as e:
            logger.error(f"Error ensuring data directory: {e}")
            raise
    
    def _is_directory_corrupted(self) -> bool:
        """Check if the data directory is corrupted."""
        try:
            # Check for common corruption indicators
            db_files = list(self.data_dir.glob("*.db"))
            if not db_files:
                return False
            
            # Try to connect to test if database is accessible
            test_settings = Settings(allow_reset=True, is_persistent=True)
            test_client = chromadb.PersistentClient(path=str(self.data_dir), settings=test_settings)
            test_client.list_collections()
            return False
            
        except Exception:
            return True
    
    def _clear_data_directory(self):
        """Clear the data directory safely."""
        try:
            import shutil
            shutil.rmtree(self.data_dir)
            logger.info("Data directory cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing data directory: {e}")
            raise
    
    def _test_connection(self):
        """Test the ChromaDB connection."""
        try:
            # Simple test to ensure connection works
            collections = self.client.list_collections()
            logger.debug(f"Connection test successful, found {len(collections)} collections")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def get_client(self) -> chromadb.Client:
        """Get the ChromaDB client."""
        if self.client is None:
            self._initialize_client()
        return self.client
    
    def list_collections(self) -> List[Any]:
        """List collections with error handling."""
        try:
            return self.get_client().list_collections()
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def get_collection(self, name: str) -> Any:
        """Get a collection with error handling."""
        try:
            return self.get_client().get_collection(name=name)
        except Exception as e:
            logger.error(f"Error getting collection '{name}': {e}")
            raise
    
    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Create a collection with error handling."""
        try:
            return self.get_client().create_collection(name=name, metadata=metadata)
        except Exception as e:
            logger.error(f"Error creating collection '{name}': {e}")
            raise
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection with error handling."""
        try:
            self.get_client().delete_collection(name=name)
            logger.info(f"Collection '{name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{name}': {e}")
            return False
    
    def cleanup_incompatible_collections(self) -> int:
        """Clean up collections with incompatible embedding dimensions."""
        cleaned_count = 0
        try:
            collections = self.list_collections()
            
            for collection in collections:
                try:
                    # Test if collection is compatible
                    collection.get()
                    logger.debug(f"Collection {collection.name} is compatible")
                except Exception as e:
                    if "Embedding dimension" in str(e) or "no such column" in str(e):
                        logger.info(f"Deleting incompatible collection: {collection.name}")
                        if self.delete_collection(collection.name):
                            cleaned_count += 1
                    else:
                        logger.debug(f"Collection {collection.name} check: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} incompatible collections")
            
        except Exception as e:
            logger.warning(f"Collection cleanup error: {e}")
        
        return cleaned_count

# Global instance
_chroma_manager = None

def get_chroma_client() -> chromadb.Client:
    """
    Get a production-ready ChromaDB client.
    """
    global _chroma_manager
    
    if _chroma_manager is None:
        _chroma_manager = ChromaDBManager()
    
    return _chroma_manager.get_client()

def get_chroma_manager() -> ChromaDBManager:
    """
    Get the ChromaDB manager instance.
    """
    global _chroma_manager
    
    if _chroma_manager is None:
        _chroma_manager = ChromaDBManager()
    
    return _chroma_manager

def cleanup_incompatible_collections():
    """
    Clean up collections with incompatible embedding dimensions.
    """
    manager = get_chroma_manager()
    return manager.cleanup_incompatible_collections()

# Initialize on module import
try:
    cleanup_incompatible_collections()
except Exception as e:
    logger.warning(f"Initial cleanup failed: {e}")