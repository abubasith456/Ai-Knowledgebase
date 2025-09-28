import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from app.utils.logging import log_print

# Force CPU mode
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["PYTORCH_MPS_DISABLED"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


class DoclingService:
    def __init__(self):
        accelerator_opts = AcceleratorOptions(num_threads=4)
        pipeline_opts = PdfPipelineOptions(
            do_ocr=True,
            do_table_structure=True,
            accelerator_options=accelerator_opts,
        )

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)
            }
        )

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="docling-")
        log_print("✅ Async Docling service initialized (CPU-only mode)")

    async def close(self):
        """Close the thread pool executor"""
        self.executor.shutdown(wait=True)

    async def convert_to_markdown(self, file_path: str) -> str:
        """Convert PDF to markdown - ASYNC VERSION"""
        log_print(f"🔍 Async converting {file_path} with Docling...")

        def _sync_convert():
            result = self.converter.convert(file_path)
            markdown = result.document.export_to_markdown()
            log_print(f"✅ Async conversion successful: {len(markdown)} chars")
            return markdown

        # Run blocking operation in thread executor
        loop = asyncio.get_event_loop()
        markdown = await loop.run_in_executor(self.executor, _sync_convert)
        return markdown


docling_service = DoclingService()
