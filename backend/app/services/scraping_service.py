import requests
import markdownify
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.models.schemas import JobStatus
from playwright.async_api import async_playwright
from app.services.minio_service import minio_service
from app.services.mongodb_service import mongodb_service
from datetime import datetime


class ScrapingService:
    def __init__(self):
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="scraping-"
        )

    async def close(self):
        """Close the thread pool executor"""
        self.executor.shutdown(wait=True)

    async def fetch_infinite(self, url):
        """Fetch infinite scroll content - ASYNC VERSION"""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)

            # scroll to bottom a few times
            for _ in range(10):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)

            html = await page.content()
            await browser.close()
            return html

    async def process_scrap_to_markdown(self, url: str, job_id: str):
        """Process scraping to markdown - ASYNC VERSION"""
        try:
            # 1. ASYNC: Download and convert
            html_content = await self.fetch_infinite(url)

            # Run markdownify in thread executor (blocking operation)
            def _sync_markdownify():
                return markdownify.markdownify(html_content, heading_style="ATX")

            loop = asyncio.get_event_loop()
            markdown_content = await loop.run_in_executor(
                self.executor, _sync_markdownify
            )

            if not markdown_content.strip():
                raise ValueError("No content scraped from webpage")

            # 2. ASYNC: Save to MinIO
            await minio_service.upload_markdown(job_id, markdown_content)

            # 3. ASYNC: Update job status
            await mongodb_service.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                markdown_size=len(markdown_content),
                file_size=len(html_content),
            )

        except Exception as e:
            await mongodb_service.update_job_status(
                job_id, JobStatus.FAILED, error=str(e)
            )


scraping_service = ScrapingService()
