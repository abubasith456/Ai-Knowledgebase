from typing import List
from loguru import logger

# Prefer Docling; fallback to pdfminer + Tesseract OCR
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
	"""Return list of page texts. Prefer Docling; fallback to text layer or OCR."""
	if _HAS_DOCLING:
		try:
			conv = DocumentConverter()
			result = conv.convert(file_path)
			doc_text = result.document.export_to_markdown() if hasattr(result.document, 'export_to_markdown') else str(result.document)
			if "\f" in doc_text:
				pages_text = [p.strip() for p in doc_text.split("\f")]
			else:
				pages_text = [doc_text[i:i+1500] for i in range(0, len(doc_text), 1500)]
			if any(t.strip() for t in pages_text):
				return [t.strip() for t in pages_text]
		except Exception as exc:
			logger.warning(f"Docling conversion failed, falling back: {exc}")

	# Fallback: extract text layer
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