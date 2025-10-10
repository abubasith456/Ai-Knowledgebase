from fastapi import APIRouter, UploadFile, File, BackgroundTasks

from app.models.schemas import ScrapRequest, ManualContentRequest
from app.models.response import StandardResponse
from app.services.job_service import job_service
from app.utils.logging import log_print

router = APIRouter()


@router.post("/{project_id}/upload")
async def upload_document(
    project_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    try:
        result = await job_service.upload_document(project_id, file)
        if result["success"]:
            background_tasks.add_task(
                job_service.process_document_background,
                result["temp_file_path"],
                result["data"].job_id,
            )
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Upload failed: {str(e)}")
        return StandardResponse.failed(error=f"Upload failed: {str(e)}")


@router.get("/jobs/{job_id}/content")
async def view_job_content(job_id: str):
    try:
        result = await job_service.view_job_content(job_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to view job content: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.get("/jobs/{job_id}/content/preview")
async def preview_job_content(job_id: str, lines: int = 50):
    try:
        result = await job_service.preview_job_content(job_id, lines)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to preview job content: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/scrap-url")
async def scrap_url(request: ScrapRequest, background_tasks: BackgroundTasks):
    try:
        result = await job_service.scrap_url(request)
        if result["success"]:
            background_tasks.add_task(
                job_service.scraping.process_scrap_to_markdown,
                result["url"],
                result["job_id"],
            )
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Scraping failed: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.post("/content")
async def add_manual_content(request: ManualContentRequest):
    try:
        result = await job_service.add_manual_content(request)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to add manual content: {str(e)}")
        return StandardResponse.failed(error=f"Failed to add manual content: {str(e)}")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    try:
        result = await job_service.get_job_status(job_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to get job status: {str(e)}")
        return StandardResponse.failed(error=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    try:
        result = await job_service.delete_job(job_id)
        if result["success"]:
            return StandardResponse.success(data=result["data"])
        else:
            return StandardResponse.failed(error=result["error"])
    except Exception as e:
        log_print(f"❌ Failed to delete job: {str(e)}")
        return StandardResponse.failed(error=str(e))
