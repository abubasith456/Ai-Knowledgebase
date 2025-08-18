from typing import List
from loguru import logger

from pdf2image import convert_from_path
import pytesseract
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

try:
	from docling.document_converter import DocumentConverter
	_HAS_DOCLING = True
except Exception:
	_HAS_DOCLING = False


def parse_pdf_with_docling(file_path: str) -> List[str]:
	"""Parse a PDF into page-like texts.

	Order of operations:
	1) Use Docling's DocumentConverter when available (preferred).
	2) Fallback to text-layer extraction via pdfminer.
	3) Fallback to OCR using Tesseract.
	"""
	if _HAS_DOCLING:
		try:
			converter = DocumentConverter()
			result = converter.convert(file_path)
			doc = result.document
			# Export as markdown (rich, structure-aware) if available
			text = doc.export_to_markdown() if hasattr(doc, "export_to_markdown") else str(doc)
			# Some converters separate pages with form-feed \f. If not, chunk to page-like windows
			if "\f" in text:
				pages = [p.strip() for p in text.split("\f")]
			else:
				pages = [text[i:i+2000] for i in range(0, len(text), 2000)]
			pages = [p for p in pages if p.strip()]
			if pages:
				return pages
		except Exception as exc:
			logger.warning(f"Docling conversion failed, falling back: {exc}")

	# Fallback: text layer via pdfminer
	pages_text: List[str] = []
	try:
		for page_layout in extract_pages(file_path):
			texts = []
			for element in page_layout:
				if isinstance(element, LTTextContainer):
					texts.append(element.get_text())
			page_text = "\n".join(texts).strip()
			pages_text.append(page_text)
	except Exception as exc:
		logger.warning(f"PDF text extraction failed, falling back to OCR: {exc}")
		pages_text = []

	if not any(t.strip() for t in pages_text):
		logger.info("No text layer found; performing OCR via Tesseract")
		images = convert_from_path(file_path, dpi=300)
		pages_text = [pytesseract.image_to_string(img) for img in images]

	return [t.strip() for t in pages_text]