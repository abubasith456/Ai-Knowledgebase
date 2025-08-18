from __future__ import annotations

from typing import Dict, Any, List
import tiktoken
from loguru import logger
from .schemas import Chunk
import uuid


def _tokenizer():
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return tiktoken.get_encoding("r50k_base")


def count_tokens(text: str) -> int:
    enc = _tokenizer()
    return len(enc.encode(text))


def hybrid_chunk_document(pages_text: List[str], max_tokens: int, overlap_tokens: int, metadata: Dict[str, Any]) -> List[Chunk]:
    """Hybrid structural + semantic chunking.

    Strategy:
    - First pass: structural split by pages and headings (simple heuristic on lines with TitleCase or all caps).
    - Second pass: enforce max_tokens per chunk; if a chunk exceeds limit, split by paragraphs/sentences.
    - Apply sliding-window overlap between consecutive chunks.
    """

    enc = _tokenizer()
    raw_sections: List[str] = []
    for page in pages_text:
        lines = [l.strip() for l in page.splitlines() if l.strip()]
        buffer: List[str] = []
        for line in lines:
            if _looks_like_heading(line) and buffer:
                raw_sections.append("\n".join(buffer))
                buffer = [line]
            else:
                buffer.append(line)
        if buffer:
            raw_sections.append("\n".join(buffer))

    # Now pack into <= max_tokens with overlap
    chunks: List[Chunk] = []
    overlap_text_tokens: List[int] = []
    carry_tokens: List[int] = []
    carry_texts: List[str] = []

    def flush_current(current_texts: List[str]):
        text = "\n".join(current_texts).strip()
        if not text:
            return
        # Avoid generating overlap-only chunks
        if len(text.split()) < 5:
            return
        chunk_id = str(uuid.uuid4())
        chunks.append(
            Chunk(
                id=chunk_id,
                text=text,
                metadata={**metadata, "num_tokens": count_tokens(text)},
            )
        )

    current_texts: List[str] = []
    current_tokens = 0

    for section in raw_sections:
        sec_tokens = len(enc.encode(section))
        if sec_tokens <= max_tokens - current_tokens:
            current_texts.append(section)
            current_tokens += sec_tokens
            continue

        # If the section alone is too large, split semantically by paragraphs
        if sec_tokens > max_tokens:
            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            for para in paragraphs:
                ptoks = len(enc.encode(para))
                if ptoks > max_tokens:
                    # sentence-level split if still too big
                    sentences = _split_sentences(para)
                    for sent in sentences:
                        stoks = len(enc.encode(sent))
                        if stoks > max_tokens:
                            # hard trim very long tokens (edge)
                            sent = enc.decode(enc.encode(sent)[:max_tokens])
                            stoks = max_tokens
                        if current_tokens + stoks > max_tokens:
                            flush_current(current_texts)
                            # start next with overlap from previous flushed chunk
                            if overlap_tokens and len(chunks) > 0:
                                overlap = _get_overlap_tail(chunks[-1].text, overlap_tokens, enc)
                                current_texts = [overlap] if overlap else []
                                current_tokens = len(enc.encode("\n".join(current_texts)))
                            else:
                                current_texts = []
                                current_tokens = 0
                        current_texts.append(sent)
                        current_tokens += stoks
                else:
                    if current_tokens + ptoks > max_tokens:
                        flush_current(current_texts)
                        if overlap_tokens and chunks:
                            overlap = _get_overlap_tail(chunks[-1].text, overlap_tokens, enc)
                            current_texts = [overlap] if overlap else []
                            current_tokens = len(enc.encode("\n".join(current_texts)))
                        else:
                            current_texts = []
                            current_tokens = 0
                    current_texts.append(para)
                    current_tokens += ptoks
        else:
            # flush current and start new with overlap
            flush_current(current_texts)
            if overlap_tokens and chunks:
                overlap = _get_overlap_tail(chunks[-1].text, overlap_tokens, enc)
                current_texts = [overlap] if overlap else []
                current_tokens = len(enc.encode("\n".join(current_texts)))
            else:
                current_texts = []
                current_tokens = 0
            current_texts.append(section)
            current_tokens += sec_tokens

    flush_current(current_texts)
    logger.info(f"Chunked into {len(chunks)} chunks")
    return chunks


def _looks_like_heading(line: str) -> bool:
    if len(line) <= 120 and (line.isupper() or line.istitle()) and not line.endswith(":"):
        return True
    return False


def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter to avoid heavyweight deps
    import re

    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _get_overlap_tail(text: str, overlap_tokens: int, enc) -> str:
    tokens = enc.encode(text)
    tail = tokens[-overlap_tokens:]
    return enc.decode(tail) if tail else ""

