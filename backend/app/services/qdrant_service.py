from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from app.config import settings
from app.utils.logging import log_print


class QdrantService:
    def __init__(self):
        # Qdrant with Hugging Face Space configuration
        qdrant_url = settings.QDRANT_URL
        qdrant_api_key = settings.QDRANT_API_KEY

        log_print(f"🔧 Connecting to Async Qdrant at: {qdrant_url}")

        try:
            # Create sync client (Qdrant doesn't have native async client)
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=60,
                prefer_grpc=False,
                https=(True if qdrant_url.startswith("https") else False),
                port=None,
                verify=False,
            )

            # Thread pool for blocking operations
            self.executor = ThreadPoolExecutor(
                max_workers=5, thread_name_prefix="qdrant-"
            )

            # Test connection with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    log_print(
                        f"🔄 Async connection attempt {attempt + 1}/{max_retries}"
                    )
                    collections = self.client.get_collections()
                    log_print(
                        f"✅ Async Qdrant connected successfully! Found {len(collections.collections)} collections"
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    log_print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(5)

        except Exception as e:
            log_print(
                f"❌ Failed to connect to Async Qdrant after {max_retries} attempts: {str(e)}"
            )
            raise ConnectionError(f"Cannot connect to Qdrant: {str(e)}")

    async def close(self):
        """Close the thread pool executor"""
        self.executor.shutdown(wait=True)

    async def create_collection(self, collection_name: str, dimension: int):
        """Create collection if it doesn't exist - ASYNC VERSION"""

        def _sync_create():
            try:
                collections = self.client.get_collections()
                existing_collections = [col.name for col in collections.collections]
            except:
                existing_collections = []

            if collection_name not in existing_collections:
                log_print(
                    f"📝 [ASYNC] Creating new Qdrant collection: {collection_name}"
                )
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=dimension, distance=Distance.COSINE
                    ),
                )
                log_print(f"✅ [ASYNC] Collection created!")
            else:
                log_print(f"✅ [ASYNC] Collection already exists: {collection_name}")

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_create)

    async def upsert_points_with_metadata(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        job_ids: List[str],
    ):
        """Upsert points with enhanced metadata - ASYNC VERSION"""

        def _sync_upsert():
            log_print(f"🔧 [ASYNC] Upserting points to Qdrant...")

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
                    f"📤 [ASYNC] Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}"
                )

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_upsert)

    async def upsert_points(
        self, collection_name: str, chunks: List[str], embeddings: List[List[float]]
    ):
        """Legacy upsert method - ASYNC VERSION"""

        def _sync_upsert():
            log_print(f"🔧 [ASYNC] Upserting points to Qdrant...")
            points = [
                PointStruct(id=i, vector=emb, payload={"text": chunk, "chunk_id": i})
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
            ]

            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                self.client.upsert(collection_name=collection_name, points=batch)
                log_print(
                    f"📤 [ASYNC] Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}"
                )

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_upsert)

    async def search(self, collection_name: str, query_vector: List[float], limit: int):
        """Search for similar vectors - ASYNC VERSION"""

        def _sync_search():
            return self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _sync_search)

    async def delete_collection(self, collection_name: str):
        """Delete a collection - ASYNC VERSION"""

        def _sync_delete():
            try:
                self.client.delete_collection(collection_name)
                log_print(f"🗑️ Async deleted Qdrant collection: {collection_name}")
            except Exception as e:
                log_print(
                    f"⚠️ Failed to async delete collection {collection_name}: {str(e)}"
                )
                raise

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _sync_delete)


qdrant_service = QdrantService()
