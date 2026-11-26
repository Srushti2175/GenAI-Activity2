"""
PDF Processing & Semantic Chunking Engine for Krishi Sakhi Knowledge Base
Extracts, cleans, and chunks multi-page agricultural PDFs with metadata preservation.
"""

import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from utils.shreedev_converter import shreedev_to_unicode


def is_shreedev_pdf(reader: PdfReader) -> bool:
    """Check if PDF uses Shree-Dev or similar legacy Devanagari font."""
    try:
        for p in reader.pages[:10]:
            fonts = p.get('/Resources', {}).get('/Font', {})
            for f_key in fonts:
                font_obj = fonts[f_key]
                base_font = str(font_obj.get('/BaseFont', '')).upper()
                if 'SHREE' in base_font or 'DEV' in base_font or 'KRUTI' in base_font:
                    return True
    except Exception:
        pass
    return False


def is_shreedev_encoded(text: str) -> bool:
    """Detect if text contains legacy Shree-Lipi / Shree-Dev font patterns."""
    markers = ["eoVr", "nÜXVr", "H$", "Am°", "g|Ðr", "nma§nm[aH$", "Amnbo", "Xwîn[aUm_", "~°[a`a", "H$éZ", "OmVo", "Agob", "{Z{_Îm", "Xoem"]
    count = sum(1 for m in markers if m in text)
    return count >= 1


def clean_text(raw_text: str, force_shreedev: bool = False) -> str:
    """Clean extra spaces and non-printable artifacts while preserving Devanagari Unicode."""
    if not raw_text:
        return ""
    
    # Auto-convert legacy Shree-Dev font encoding to modern Unicode Devanagari
    if force_shreedev or is_shreedev_encoded(raw_text):
        raw_text = shreedev_to_unicode(raw_text)

    # Normalize excessive spaces and linebreaks
    text = re.sub(r'[\r\f\v]', '\n', raw_text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def extract_pages_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text page by page from a given PDF file.
    Returns list of dicts: [{"page": 1, "text": "..."}, ...]
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    reader = PdfReader(pdf_path)
    shreedev_doc = is_shreedev_pdf(reader)
    pages_data = []

    for index, page in enumerate(reader.pages):
        page_num = index + 1
        page_raw = page.extract_text() or ""
        cleaned = clean_text(page_raw, force_shreedev=shreedev_doc)
        if cleaned:
            pages_data.append({
                "page": page_num,
                "text": cleaned
            })

    return pages_data


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """
    Split a block of text into semantic chunks respecting sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]

    # Split on sentence boundaries (Marathi purna-viram '।', '.', '!', '?', or double newlines)
    sentences = re.split(r'(?<=[.!?।\n])\s+', text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if not s_len:
            continue

        if current_len + s_len > chunk_size and current_chunk:
            chunk_str = " ".join(current_chunk).strip()
            chunks.append(chunk_str)

            # Build overlap from the end of the current chunk
            overlap_sentences = []
            overlap_len = 0
            for prev_s in reversed(current_chunk):
                if overlap_len + len(prev_s) <= overlap:
                    overlap_sentences.insert(0, prev_s)
                    overlap_len += len(prev_s)
                else:
                    break
            
            current_chunk = overlap_sentences + [sentence]
            current_len = sum(len(s) for s in current_chunk) + len(current_chunk)
        else:
            current_chunk.append(sentence)
            current_len += s_len + 1

    if current_chunk:
        chunk_str = " ".join(current_chunk).strip()
        if chunk_str and (not chunks or chunk_str != chunks[-1]):
            chunks.append(chunk_str)

    return chunks


def process_pdf(pdf_path: str, category: str = "general") -> List[Dict[str, Any]]:
    """
    Processes a complete PDF: extracts pages and produces tagged semantic chunks.
    """
    filename = os.path.basename(pdf_path)
    pages = extract_pages_from_pdf(pdf_path)
    processed_chunks = []

    doc_slug = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(filename)[0]).lower()

    for p in pages:
        page_num = p["page"]
        text = p["text"]
        chunks = chunk_text(text, chunk_size=600, overlap=100)

        for c_idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_slug}_p{page_num}_c{c_idx+1}"
            processed_chunks.append({
                "id": chunk_id,
                "source_file": filename,
                "file_path": pdf_path,
                "category": category,
                "page": page_num,
                "chunk_index": c_idx + 1,
                "char_count": len(chunk),
                "text": chunk
            })

    return processed_chunks
