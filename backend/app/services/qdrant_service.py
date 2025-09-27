from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List
import time
from app.config import settings
from app.utils.logging import log_print


class QdrantService:
    def __init__(self):
        # Qdrant with Hugging Face Space configuration (exactly like your working code)
        qdrant_url = settings.QDRANT_URL
        qdrant_api_key = settings.QDRANT_API_KEY

        log_print(f"🔧 Connecting to Qdrant at: {qdrant_url}")

        try:
            # Add version compatibility check bypass (exactly like your working code)
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60,
                prefer_grpc=False,
                https=(True if qdrant_url.startswith("https") else False),
                port=None,
                # Bypass version check to avoid warnings
                verify=False,
            )

            # Test connection with retry (exactly like your working code)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    log_print(f"🔄 Connection attempt {attempt + 1}/{max_retries}")
                    collections = self.client.get_collections()
                    log_print(
                        f"✅ Qdrant connected successfully! Found {len(collections.collections)} collections"
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    log_print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(5)

        except Exception as e:
            log_print(
                f"❌ Failed to connect to Qdrant after {max_retries} attempts: {str(e)}"
            )
            raise ConnectionError(f"Cannot connect to Qdrant: {str(e)}")

    def create_collection(self, collection_name: str, dimension: int):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
        except:
            existing_collections = []

        if collection_name not in existing_collections:
            log_print(f"📝 [SYNC] Creating new Qdrant collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            log_print(f"✅ [SYNC] Collection created!")
        else:
            log_print(f"✅ [SYNC] Collection already exists: {collection_name}")

    def upsert_points_with_metadata(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        job_ids: List[str],
    ):
        """Upsert points with enhanced metadata for multi-document indexing"""
        log_print(f"🔧 [SYNC] Upserting points to Qdrant...")

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Try to determine document source
            doc_source = "unknown"
            for job_id in job_ids:
                if f"Document: {job_id}" in chunk:
                    doc_source = job_id
                    break

            points.append(
                PointStruct(
                    id=i,
                    vector=emb,
                    payload={
                        "text": chunk,
                        "chunk_id": i,
                        "document_source": doc_source,
                        "job_ids": job_ids,
                    },
                )
            )

        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=collection_name, points=batch)
            log_print(
                f"📤 [SYNC] Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}"
            )

    def upsert_points(
        self, collection_name: str, chunks: List[str], embeddings: List[List[float]]
    ):
        """Legacy upsert method"""
        log_print(f"🔧 [SYNC] Upserting points to Qdrant...")
        points = [
            PointStruct(id=i, vector=emb, payload={"text": chunk, "chunk_id": i})
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=collection_name, points=batch)
            log_print(
                f"📤 [SYNC] Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}"
            )

    def search(self, collection_name: str, query_vector: List[float], limit: int):
        """Search for similar vectors"""
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            log_print(f"🗑️ Deleted Qdrant collection: {collection_name}")
        except Exception as e:
            log_print(f"⚠️ Failed to delete collection {collection_name}: {str(e)}")
            raise


qdrant_service = QdrantService()
