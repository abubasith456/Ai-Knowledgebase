from minio import Minio
import io
from app.config import settings
from app.utils.logging import log_print


class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        # Create bucket if not exists
        if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
            self.client.make_bucket(settings.MINIO_BUCKET_NAME)

        log_print("✅ MinIO service initialized")

    def upload_markdown(self, job_id: str, content: str) -> str:
        """Upload markdown content to MinIO"""
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

        log_print(f"📤 Saved to MinIO: {md_filename} ({len(markdown_bytes)} bytes)")
        return md_filename

    def download_markdown(self, job_id: str) -> str:
        """Download markdown content from MinIO"""
        md_filename = f"{job_id}.md"
        response = self.client.get_object(settings.MINIO_BUCKET_NAME, md_filename)
        content = response.read().decode()
        log_print(f"📥 Downloaded from MinIO: {md_filename} ({len(content)} chars)")
        return content

    def delete_markdown(self, job_id: str) -> bool:
        """Delete markdown file from MinIO"""
        try:
            md_filename = f"{job_id}.md"
            self.client.remove_object(settings.MINIO_BUCKET_NAME, md_filename)
            log_print(f"🗑️ Deleted from MinIO: {md_filename}")
            return True
        except Exception as e:
            log_print(f"❌ Failed to delete from MinIO {job_id}: {str(e)}")
            return False


minio_service = MinIOService()
