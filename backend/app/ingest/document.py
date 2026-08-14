"""Document converters (PDF, DOCX) -> extracted text.

Scanned PDFs yield no text layer; those are flagged ocr_required and stored
as-is for downstream OCR. DOCX is parsed with stdlib zipfile+xml (no deps).
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .. import config

MIN_TEXT_CHARS_FOR_OCR_FLAG = 10


def _truncate(text: str) -> str:
    if len(text) <= config.MAX_EMBEDDED_TEXT_BYTES:
        return text
    return text[: config.MAX_EMBEDDED_TEXT_BYTES] + "\n...[truncated]"


def from_pdf(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    try:
        from pypdf import PdfReader
    except ImportError as e:  # pragma: no cover
        raise ValueError("pypdf not installed; cannot read .pdf") from e

    reader = PdfReader(path)
    pages = len(reader.pages)
    parts: list[str] = []
    for p in reader.pages:
        try:
            t = p.extract_text() or ""
        except Exception as e:
            warnings.append(f"page {len(parts) + 1} text extraction failed: {e}")
            t = ""
        parts.append(t)
    text = "\n\n".join(parts).strip()
    ocr_required = pages > 0 and len(text) < 10

    data = {
        "format": "pdf",
        "pages": pages,
        "text": _truncate(text),
        "ocr_required": ocr_required,
        "stored_file": str(path),
    }
    if ocr_required:
        warnings.append("no text layer detected (scanned PDF); OCR required")
    return {"data": data, "source_crs": src_crs, "warnings": warnings,
            "confidence": "medium" if not ocr_required else "low"}


def from_docx(path: Path, src_crs: Optional[str], warnings: list[str]) -> dict:
    try:
        with zipfile.ZipFile(path) as zf:
            xml_bytes = zf.read("word/document.xml")
    except KeyError:
        raise ValueError("not a valid DOCX (missing word/document.xml)")
    except zipfile.BadZipFile as e:
        raise ValueError("not a valid DOCX zip") from e

    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    text = "\n".join(paragraphs)

    tables = len(root.findall(".//w:tbl", ns))
    data = {
        "format": "docx",
        "paragraphs": len(paragraphs),
        "tables": tables,
        "text": _truncate(text),
        "stored_file": str(path),
    }
    if not text:
        warnings.append("no text extracted from DOCX")
    return {"data": data, "source_crs": src_crs, "warnings": warnings,
            "confidence": "medium" if text else "low"}
