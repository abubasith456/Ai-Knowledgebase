# app/services/parser_service.py
import asyncio
from pathlib import Path
from typing import Dict, Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from app.repository.db import documents_store
from app.services.dropbox_service import dropbox_client


class ParserQueue:
    def __init__(self, output_dir: str = "app/storage/parsed"):
        self.queue = asyncio.Queue()
        self.is_running = False
        self.documents_store: Dict[int, Any] = {}
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converter = self._build_converter()

    def _build_converter(self) -> DocumentConverter:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    async def add_task(self, file_path: str, doc_id: str, project_id: str):
        await self.queue.put((file_path, doc_id, project_id))
        if not self.is_running:
            asyncio.create_task(self.run())

    async def run(self):
        self.is_running = True
        try:
            while not self.queue.empty():
                file_path, doc_id, project_id = await self.queue.get()
                # set parsing
                await self._set_status(doc_id, "parsing")
                try:
                    await self.parse_document(file_path, doc_id, project_id)
                    await self._set_status(doc_id, "completed")
                except Exception as e:
                    await self._set_status(doc_id, "failed")
                    print(f"[ERROR] Parsing failed for doc {doc_id}: {e}")
                self.queue.task_done()
        finally:
            self.is_running = False

    async def _set_status(self, doc_id: int, status: str):
        docs = await documents_store.load()
        key = str(doc_id)
        if key in docs:
            docs[key]["status"] = status
            await documents_store.save(docs)

    async def parse_document(self, file_path: str, doc_id: int, project_id: int):
        source_path = Path(file_path)
        out_base = self.output_dir / f"{project_id}" / f"{doc_id}"
        out_base.parent.mkdir(parents=True, exist_ok=True)

        def _convert_and_export():
            print(
                f"[INFO] Starting conversion for {source_path} → {out_base.with_suffix('.md')}"
            )
            result = self.converter.convert(source=source_path)
            md = result.document.export_to_markdown()
            out_base.with_suffix(".md").write_text(md, encoding="utf-8")
            print(f"[INFO] Finished conversion for {source_path}")
            if dropbox_client.dbx:
                try:
                    dropbox_path = f"/projects/{project_id}/{doc_id}.md"
                    dropbox_client.upload_file(
                        str(out_base.with_suffix(".md")), dropbox_path, overwrite=True
                    )
                except Exception as e:
                    print(
                        f"[WARN] Failed to upload parsed doc {doc_id} to Dropbox: {e}"
                    )

        # Offload Docling conversion to a thread to avoid blocking
        await asyncio.to_thread(_convert_and_export)

        print(f"[DONE] Doc {doc_id} parsed with OCR → {out_base.with_suffix('.md')}")


parser_queue = ParserQueue()
