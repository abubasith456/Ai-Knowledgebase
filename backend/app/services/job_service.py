from typing import Dict, Any
import os
import asyncio
import aiofiles
from fastapi import UploadFile

from app.models.schemas import (
    JobResponse,
    JobStatus,
    ScrapRequest,
    DocumentType,
    JobInfoResponse,
    JobContentResponse,
    ContentStatsResponse,
    JobContentPreviewResponse,
    JobContentPreviewStats,
    ManualContentRequest,
)
from app.services.mongodb_service import mongodb_service
from app.services.docling_service import docling_service
from app.services.minio_service import minio_service
from app.services.scraping_service import scraping_service
from app.utils.logging import log_print


class JobService:
    def __init__(self):
        self.mongodb = mongodb_service
        self.minio = minio_service
        self.docling = docling_service
        self.scraping = scraping_service

    async def upload_document(
        self, project_id: str, file: UploadFile
    ) -> Dict[str, Any]:
        project = await self.mongodb.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        if not file.filename or not file.filename.endswith(".pdf"):
            return {"success": False, "error": "Only PDF files supported"}

        job_id = await self.mongodb.create_job(project_id, file.filename)

        temp_file_path = f"/tmp/{job_id}_{file.filename}"

        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            await temp_file.write(content)

        log_print(f"📄 File saved: {temp_file_path} ({len(content)} bytes)")

        response_data = JobResponse(
            job_id=job_id,
            project_id=project_id,
            filename=file.filename,
            status=JobStatus.PARSING,
            message="File uploaded and processing started",
        )

        return {
            "success": True,
            "data": response_data,
            "temp_file_path": temp_file_path,
        }

    async def process_document_background(self, file_path: str, job_id: str):
        try:
            log_print(f"🔄 [DOC] Starting ASYNC processing for job: {job_id}")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_size = os.path.getsize(file_path)
            log_print(f"📊 [DOC] File size: {file_size / 1024 / 1024:.2f} MB")

            markdown_content = await self.docling.convert_to_markdown(file_path)

            if not markdown_content.strip():
                raise ValueError("No content extracted from document")

            await self.minio.upload_markdown(job_id, markdown_content)

            await self.mongodb.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                file_size=file_size,
                markdown_size=len(markdown_content),
            )

            log_print(f"✅ [DOC] ASYNC processing completed for job: {job_id}")

        except Exception as e:
            log_print(f"❌ [DOC] ASYNC processing failed for job {job_id}: {str(e)}")
            await self.mongodb.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        finally:
            if os.path.exists(file_path):
                await asyncio.get_event_loop().run_in_executor(
                    None, os.remove, file_path
                )
                log_print(f"🗑️ [DOC] Cleaned up temp file: {file_path}")

    async def view_job_content(self, job_id: str) -> Dict[str, Any]:
        job = await self.mongodb.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        if job.status != JobStatus.COMPLETED:
            return {
                "success": False,
                "error": f"Job not completed yet. Current status: {job.status}",
            }

        markdown_content = await self.minio.download_markdown(job_id)

        response_data = JobContentResponse(
            job_id=job_id,
            job_info=JobInfoResponse(
                filename=job.filename,
                type=job.type.value,
                status=job.status.value,
                created_at=job.created_at,
                file_size=job.file_size,
                markdown_size=job.markdown_size,
            ),
            content=markdown_content,
            content_stats=ContentStatsResponse(
                character_count=len(markdown_content),
                word_count=len(markdown_content.split()) if markdown_content else 0,
                line_count=len(markdown_content.split("\n")) if markdown_content else 0,
                size_kb=round(len(markdown_content.encode("utf-8")) / 1024, 2),
            ),
        )

        return {"success": True, "data": response_data}

    async def preview_job_content(self, job_id: str, lines: int = 50) -> Dict[str, Any]:
        job = await self.mongodb.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        if job.status != JobStatus.COMPLETED:
            return {
                "success": False,
                "error": f"Job not completed yet. Current status: {job.status}",
            }

        markdown_content = await self.minio.download_markdown(job_id)

        content_lines = markdown_content.split("\n")
        preview_lines = content_lines[:lines]
        preview_content = "\n".join(preview_lines)

        is_truncated = len(content_lines) > lines

        response_data = JobContentPreviewResponse(
            job_id=job_id,
            job_info=JobInfoResponse(
                filename=job.filename,
                type=job.type.value,
                status=job.status.value,
                created_at=job.created_at,
                file_size=job.file_size,
                markdown_size=job.markdown_size,
            ),
            preview=preview_content,
            preview_stats=JobContentPreviewStats(
                preview_lines=len(preview_lines),
                total_lines=len(content_lines),
                is_truncated=is_truncated,
                truncated_lines=(
                    max(0, len(content_lines) - lines) if is_truncated else 0
                ),
            ),
        )

        return {"success": True, "data": response_data}

    async def scrap_url(self, request: ScrapRequest) -> Dict[str, Any]:
        project = await self.mongodb.get_project(request.project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        if not request.url.startswith("http"):
            return {"success": False, "error": "Invalid URL"}

        job_id = await self.mongodb.create_job(
            request.project_id, request.url, type=DocumentType.WEB
        )

        response_data = JobResponse(
            job_id=job_id,
            project_id=request.project_id,
            filename=request.url,
            status=JobStatus.PARSING,
            message="Webpage scraping and processing started",
        )

        return {
            "success": True,
            "data": response_data,
            "job_id": job_id,
            "url": request.url,
        }

    async def add_manual_content(self, request: ManualContentRequest) -> Dict[str, Any]:
        log_print(
            f"📝 [MANUAL] Adding manual content for project: {request.project_id}"
        )

        project = await self.mongodb.get_project(request.project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        if not request.content.strip():
            return {"success": False, "error": "Content cannot be empty"}

        if len(request.content) < 10:
            return {
                "success": False,
                "error": "Content too short (minimum 10 characters)",
            }

        safe_title = "".join(
            c for c in request.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = f"{safe_title}.md" if safe_title else "manual_content.md"

        job_id = await self.mongodb.create_job(
            request.project_id,
            filename,
            type=DocumentType.WEB,
        )

        formatted_content = f"""# {request.title}"""

        if request.source_url:
            formatted_content += f"  \n**Source:** {request.source_url}"

        if request.description:
            formatted_content += f"  \n**Description:** {request.description}"

        formatted_content += f"\n\n---\n\n{request.content}"

        await self.minio.upload_markdown(job_id, formatted_content)

        await self.mongodb.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            file_size=len(request.content.encode("utf-8")),
            markdown_size=len(formatted_content),
            manual_content_added=True,
        )

        log_print(
            f"✅ [MANUAL] Manual content added successfully: {job_id} ({len(formatted_content)} chars)"
        )

        response_data = JobResponse(
            job_id=job_id,
            project_id=request.project_id,
            filename=filename,
            status=JobStatus.COMPLETED,
            message="Manual content added successfully",
        )

        return {"success": True, "data": response_data}

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        job = await self.mongodb.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        return {"success": True, "data": job.model_dump()}

    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        job = await self.mongodb.get_job(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        result = await self.mongodb.delete_job(job_id)

        if result["status"] == "success":
            return {"success": True, "data": {"message": result["message"]}}
        else:
            return {"success": False, "error": result["message"]}


job_service = JobService()
