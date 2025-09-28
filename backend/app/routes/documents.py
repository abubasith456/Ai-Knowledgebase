from fastapi import APIRouter, UploadFile, File, BackgroundTasks
import os
import asyncio
import aiofiles

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
from app.models.response import StandardResponse
from app.services.mongodb_service import mongodb_service
from app.services.docling_service import docling_service
from app.services.minio_service import minio_service
from app.services.scraping_service import scraping_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/{project_id}/upload", response_model=StandardResponse[JobResponse])
async def upload_document(
    project_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """Upload and process PDF document to a project"""
    try:
        project = await mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        if not file.filename or not file.filename.endswith(".pdf"):
            return StandardResponse.failed(error="Only PDF files supported")

        job_id = await mongodb_service.create_job(project_id, file.filename)

        # Save file temporarily
        temp_file_path = f"/tmp/{job_id}_{file.filename}"

        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            await temp_file.write(content)

        log_print(f"📄 File saved: {temp_file_path} ({len(content)} bytes)")

        # Process in background
        background_tasks.add_task(process_document_background, temp_file_path, job_id)

        response_data = JobResponse(
            job_id=job_id,
            project_id=project_id,
            filename=file.filename,
            status=JobStatus.PARSING,
            message="File uploaded and processing started",
        )

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Upload failed: {str(e)}")
        return StandardResponse.failed(error=f"Upload failed: {str(e)}")


@router.get(
    "/jobs/{job_id}/content", response_model=StandardResponse[JobContentResponse]
)
async def view_job_content(job_id: str):
    """View the processed markdown content from MinIO storage"""
    try:
        # Check if job exists
        job = await mongodb_service.get_job(job_id)
        if not job:
            return StandardResponse.failed(error="Job not found")

        # Check if job is completed
        if job.status != JobStatus.COMPLETED:
            return StandardResponse.failed(
                error=f"Job not completed yet. Current status: {job.status}"
            )

        # Download content from MinIO
        markdown_content = await minio_service.download_markdown(job_id)

        # Create response using Pydantic models
        response_data = JobContentResponse(
            job_id=job_id,
            job_info=JobInfoResponse(
                filename=job.filename,
                type=job.type.value,  # Convert enum to string
                status=job.status.value,  # Convert enum to string
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

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Failed to view job content: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get(
    "/jobs/{job_id}/content/preview",
    response_model=StandardResponse[JobContentPreviewResponse],
)
async def preview_job_content(job_id: str, lines: int = 50):
    """Preview the first N lines of processed markdown content"""
    try:
        job = await mongodb_service.get_job(job_id)
        if not job:
            return StandardResponse.failed(error="Job not found")

        if job.status != JobStatus.COMPLETED:
            return StandardResponse.failed(
                error=f"Job not completed yet. Current status: {job.status}"
            )

        # Download content from MinIO
        markdown_content = await minio_service.download_markdown(job_id)

        # Get preview (first N lines)
        content_lines = markdown_content.split("\n")
        preview_lines = content_lines[:lines]
        preview_content = "\n".join(preview_lines)

        # Check if content was truncated
        is_truncated = len(content_lines) > lines

        # Create response using Pydantic models
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

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ Failed to preview job content: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/scrap-url", response_model=StandardResponse[JobResponse])
async def scrap_url(req: ScrapRequest, background_tasks: BackgroundTasks):

    project = await mongodb_service.get_project(req.project_id)
    if not project:
        return StandardResponse.failed(error="Project not found")
    # 2. Validate/clean URL
    if not req.url.startswith("http"):
        return StandardResponse.failed(error="Invalid URL")

    job_id = await mongodb_service.create_job(
        req.project_id, req.url, type=DocumentType.WEB
    )
    # 4. Add background task to process_url_scraping
    background_tasks.add_task(
        scraping_service.process_scrap_to_markdown, req.url, job_id
    )
    return StandardResponse.success(
        data=JobResponse(
            job_id=job_id,
            project_id=req.project_id,
            filename=req.url,
            status=JobStatus.PARSING,
            message="Webpage scraping and processing started",
        )
    )


@router.post("/content", response_model=StandardResponse[JobResponse])
async def add_manual_content(request: ManualContentRequest):
    """Add content manually - perfect for when scraping fails or for direct content input"""
    try:
        log_print(
            f"📝 [MANUAL] Adding manual content for project: {request.project_id}"
        )

        # Verify project exists
        project = await mongodb_service.get_project(request.project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        # Validate content
        if not request.content.strip():
            return StandardResponse.failed(error="Content cannot be empty")

        if len(request.content) < 10:
            return StandardResponse.failed(
                error="Content too short (minimum 10 characters)"
            )

        # Create filename from title
        safe_title = "".join(
            c for c in request.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = f"{safe_title}.md" if safe_title else "manual_content.md"

        # Create job with type='manual'
        job_id = await mongodb_service.create_job(
            request.project_id,
            filename,
            type=DocumentType.WEB,  # Using WEB type for manual content
        )

        # Format content with metadata
        formatted_content = f"""# {request.title}"""

        # Add source URL if provided
        if request.source_url:
            formatted_content += f"  \n**Source:** {request.source_url}"

        # Add description if provided
        if request.description:
            formatted_content += f"  \n**Description:** {request.description}"

        formatted_content += f"\n\n---\n\n{request.content}"

        # Save directly to MinIO (no background processing needed)
        await minio_service.upload_markdown(job_id, formatted_content)

        # Update job status to completed immediately
        await mongodb_service.update_job_status(
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

        return StandardResponse.success(data=response_data)

    except Exception as e:
        log_print(f"❌ [MANUAL] Failed to add manual content: {str(e)}")
        return StandardResponse.failed(error=f"Failed to add manual content: {str(e)}")


async def process_document_background(file_path: str, job_id: str):
    """Background task to process document - ASYNC VERSION"""
    try:
        log_print(f"🔄 [DOC] Starting ASYNC processing for job: {job_id}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        log_print(f"📊 [DOC] File size: {file_size / 1024 / 1024:.2f} MB")

        markdown_content = await docling_service.convert_to_markdown(file_path)

        if not markdown_content.strip():
            raise ValueError("No content extracted from document")

        await minio_service.upload_markdown(job_id, markdown_content)

        await mongodb_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            file_size=file_size,
            markdown_size=len(markdown_content),
        )

        log_print(f"✅ [DOC] ASYNC processing completed for job: {job_id}")

    except Exception as e:
        log_print(f"❌ [DOC] ASYNC processing failed for job {job_id}: {str(e)}")

        await mongodb_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
    finally:
        # Cleanup
        if os.path.exists(file_path):
            # FIXED: Use async file removal
            await asyncio.get_event_loop().run_in_executor(None, os.remove, file_path)
            log_print(f"🗑️ [DOC] Cleaned up temp file: {file_path}")


@router.get("/jobs/{job_id}", response_model=StandardResponse)
async def get_job_status(job_id: str):
    """Get job processing status"""
    try:
        job = await mongodb_service.get_job(job_id)
        if not job:
            return StandardResponse.failed(error="Job not found")

        return StandardResponse.success(data=job.model_dump())

    except Exception as e:
        log_print(f"❌ Failed to get job status: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/jobs/{job_id}", response_model=StandardResponse)
async def delete_job(job_id: str):
    """Delete a job (checks if used in indexes)"""
    try:
        job = await mongodb_service.get_job(job_id)
        if not job:
            return StandardResponse.failed(error="Job not found")

        result = await mongodb_service.delete_job(job_id)

        if result["status"] == "success":
            return StandardResponse.success(data={"message": result["message"]})
        else:
            return StandardResponse.failed(error=result["message"])

    except Exception as e:
        log_print(f"❌ Failed to delete job: {str(e)}")
        return StandardResponse.failed(error=str(e))
