import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os

class ChromaStore:
    def __init__(self, persist_directory: str = "backend/chroma"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def add_documents(self, collection_name: str, ids: List[str], 
                     embeddings: List[List[float]], metadatas: List[Dict[str, Any]], 
                     documents: List[str]) -> None:
        """Add documents to a collection"""
        try:
            # Get or create collection
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Add documents
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            raise

    def query_documents(self, collection_name: str, query_text: str, 
                       n_results: int = 5) -> List[Dict[str, Any]]:
        """Query documents in a collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Generate query embedding (placeholder - should use same model as documents)
            query_embedding = [float(len(query_text) % 7)] * 8
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            return {
                'name': collection_name,
                'count': count
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None

    def delete_documents(self, collection_name: str, filter_metadata: Dict[str, Any]) -> bool:
        """Delete documents by metadata filter"""
        try:
            collection = self.client.get_collection(name=collection_name)
            # Delete documents matching the filter
            collection.delete(where=filter_metadata)
            return True
        except Exception as e:
            print(f"Error deleting documents from ChromaDB: {e}")
            return False

# Global instance
chroma_store = ChromaStore()

def add_documents(collection_name: str, ids: List[str], 
                 embeddings: List[List[float]], metadatas: List[Dict[str, Any]], 
                 documents: List[str]) -> None:
    """Convenience function to add documents"""
    chroma_store.add_documents(collection_name, ids, embeddings, metadatas, documents)

def query_documents(collection_name: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Convenience function to query documents"""
    return chroma_store.query_documents(collection_name, query_text, n_results)

def delete_documents(collection_name: str, filter_metadata: Dict[str, Any]) -> bool:
    """Convenience function to delete documents by metadata filter"""
    return chroma_store.delete_documents(collection_name, filter_metadata)
