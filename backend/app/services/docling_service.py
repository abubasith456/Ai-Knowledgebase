import os
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
        log_print("✅ Docling service initialized (CPU-only mode)")

    def convert_to_markdown(self, file_path: str) -> str:
        """Convert PDF to markdown"""
        log_print(f"🔍 Converting {file_path} with Docling...")
        result = self.converter.convert(file_path)
        markdown = result.document.export_to_markdown()
        log_print(f"✅ Conversion successful: {len(markdown)} chars")
        return markdown


docling_service = DoclingService()
