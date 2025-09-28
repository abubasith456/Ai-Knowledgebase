import requests
import markdownify
from app.models.schemas import JobStatus
from playwright.sync_api import sync_playwright
from app.services.minio_service import minio_service
from app.services.mongodb_service import mongodb_service
from datetime import datetime


class ScrapingService:

    def fetch_infinite(self, url):
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            # scroll to bottom a few times
            for _ in range(10):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
            return html

    def process_scrap_to_markdown(self, url: str, job_id: str):
        try:
            # 1. Download and convert
            html_content = self.fetch_infinite(url)
            markdown_content = markdownify.markdownify(
                html_content, heading_style="ATX"
            )
            if not markdown_content.strip():
                raise ValueError("No content scraped from webpage")
            # 2. Save to MinIO
            minio_service.upload_markdown(job_id, markdown_content)
            # 3. Update job status
            mongodb_service.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                markdown_size=len(markdown_content),
                file_size=len(html_content),
                updated_at=datetime.now(),
            )
        except Exception as e:
            mongodb_service.update_job_status(
                job_id, JobStatus.FAILED, error=str(e), updated_at=datetime.now()
            )


scraping_service = ScrapingService()
