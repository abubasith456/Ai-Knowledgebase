from fastapi import APIRouter, UploadFile, File, BackgroundTasks
import os

from app.models.schemas import JobResponse, JobStatus
from app.models.response import StandardResponse
from app.services.mongodb_service import mongodb_service
from app.services.docling_service import docling_service
from app.services.minio_service import minio_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/{project_id}/upload", response_model=StandardResponse[JobResponse])
async def upload_document(
    project_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """Upload and process PDF document to a project"""
    try:
        # Verify project exists
        project = mongodb_service.get_project(project_id)
        if not project:
            return StandardResponse.failed(error="Project not found")

        if not file.filename or not file.filename.endswith(".pdf"):
            return StandardResponse.failed(error="Only PDF files supported")

        # Create job
        job_id = mongodb_service.create_job(project_id, file.filename)

        # Save file temporarily
        temp_file_path = f"/tmp/{job_id}_{file.filename}"

        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

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


def process_document_background(file_path: str, job_id: str):
    """Background task to process document"""
    try:
        log_print(f"🔄 [DOC] Starting processing for job: {job_id}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        log_print(f"📊 [DOC] File size: {file_size / 1024 / 1024:.2f} MB")

        # Convert with Docling
        markdown_content = docling_service.convert_to_markdown(file_path)

        if not markdown_content.strip():
            raise ValueError("No content extracted from document")

        # Save to MinIO
        minio_service.upload_markdown(job_id, markdown_content)

        # Update job status
        mongodb_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            file_size=file_size,
            markdown_size=len(markdown_content),
        )

        log_print(f"✅ [DOC] Processing completed for job: {job_id}")

    except Exception as e:
        log_print(f"❌ [DOC] Processing failed for job {job_id}: {str(e)}")
        mongodb_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            log_print(f"🗑️ [DOC] Cleaned up temp file: {file_path}")


@router.get("/jobs/{job_id}", response_model=StandardResponse)
async def get_job_status(job_id: str):
    """Get job processing status"""
    try:
        job = mongodb_service.get_job(job_id)
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
        job = mongodb_service.get_job(job_id)
        if not job:
            return StandardResponse.failed(error="Job not found")

        result = mongodb_service.delete_job(job_id)

        if result["status"] == "success":
            return StandardResponse.success(data={"message": result["message"]})
        else:
            return StandardResponse.failed(error=result["message"])

    except Exception as e:
        log_print(f"❌ Failed to delete job: {str(e)}")
        return StandardResponse.failed(error=str(e))
