from minio import Minio
import io, urllib3
from urllib3.util.retry import Retry

import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.config import settings
from app.utils.logging import log_print

# Fast retry configuration
retry_strategy = Retry(
    total=5,  # 5 quick retry attempts
    backoff_factor=0.3,  # Low backoff factor (0.3s base)
    status_forcelist=[500, 502, 503, 504, 408, 429],
    raise_on_status=False,
    respect_retry_after_header=False,  # Don't wait for server's retry-after
)

# Create HTTP client with aggressive timeouts
http_client = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=5.0, read=30.0),  # Shorter read timeout
    retries=retry_strategy,
    maxsize=10,
    block=False,
)


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            http_client=http_client,
        )

        # Create bucket if not exists
        if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
            self.client.make_bucket(settings.MINIO_BUCKET_NAME)

        # Thread pool executor for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="minio-")
        log_print("✅ Async MinIO service initialized")

    async def close(self):
        """Close the thread pool executor"""
        self.executor.shutdown(wait=True)

    async def upload_markdown(self, job_id: str, content: str) -> str:
        """Upload markdown content to MinIO - ASYNC VERSION"""

        def _sync_upload():
            md_filename = f"{job_id}.md"
            markdown_bytes = content.encode("utf-8")
            markdown_stream = io.BytesIO(markdown_bytes)

            self.client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=md_filename,
                data=markdown_stream,
                length=len(markdown_bytes),
                content_type="text/markdown",
            )

            log_print(
                f"📤 Async saved to MinIO: {md_filename} ({len(markdown_bytes)} bytes)"
            )
            return md_filename

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _sync_upload)

    async def download_markdown(self, job_id: str) -> str:
        """Download markdown content from MinIO - ASYNC VERSION"""

        def _sync_download():
            md_filename = f"{job_id}.md"
            response = self.client.get_object(settings.MINIO_BUCKET_NAME, md_filename)
            content = response.read().decode()
            response.close()
            response.release_conn()
            log_print(
                f"📥 Async downloaded from MinIO: {md_filename} ({len(content)} chars)"
            )
            return content

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _sync_download)

    async def delete_markdown(self, job_id: str) -> bool:
        """Delete markdown file from MinIO - ASYNC VERSION"""

        def _sync_delete():
            try:
                md_filename = f"{job_id}.md"
                self.client.remove_object(settings.MINIO_BUCKET_NAME, md_filename)
                log_print(f"🗑️ Async deleted from MinIO: {md_filename}")
                return True
            except Exception as e:
                log_print(f"❌ Failed to async delete from MinIO {job_id}: {str(e)}")
                return False

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _sync_delete)


minio_service = MinIOService()
