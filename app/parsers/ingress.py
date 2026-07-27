"""File ingress validation."""

import hashlib
import chardet
from app.core.exceptions import (
    AppError, RESUME_EMPTY, RESUME_TOO_LARGE, RESUME_UNSUPPORTED_TYPE,
    PDF_ENCRYPTED, PDF_NO_TEXT, PDF_TOO_MANY_PAGES, TEXT_ENCODING_FAILED,
    RESUME_TYPE_MISMATCH,
)
from app.core.config import settings


class FileIngressValidator:
    def __init__(self):
        self.max_size = settings.max_upload_size_mb * 1024 * 1024
        self.max_pdf_pages = settings.max_pdf_pages

    async def validate(self, content: bytes, filename: str, declared_mime: str | None = None) -> str:
        """Validate file content. Returns SHA-256 hash."""
        if not content or len(content.strip()) == 0:
            raise AppError(RESUME_EMPTY, "File is empty")

        if len(content) > self.max_size:
            raise AppError(
                RESUME_TOO_LARGE,
                f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
            )

        sha256 = hashlib.sha256(content).hexdigest()

        # Extension check
        ext = self._get_extension(filename)
        if ext not in (".pdf", ".txt", ".tex", ".ltx", ".latex", ".text", ""):
            raise AppError(RESUME_UNSUPPORTED_TYPE, f"Unsupported file type: {ext}")

        # PDF-specific checks
        if content.startswith(b"%PDF-"):
            if b"/Encrypt" in content[:4096]:
                raise AppError(PDF_ENCRYPTED, "PDF is encrypted and cannot be processed")
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            if page_count > self.max_pdf_pages:
                raise AppError(
                    PDF_TOO_MANY_PAGES,
                    f"PDF has {page_count} pages, max is {self.max_pdf_pages}",
                )

        # Text encoding check for non-PDF files
        if not content.startswith(b"%PDF-"):
            result = chardet.detect(content[:8192])
            if result.get("encoding") is None and ext in (".txt", ".text", ""):
                raise AppError(TEXT_ENCODING_FAILED, "Cannot detect text encoding")

        return sha256

    def _get_extension(self, filename: str) -> str:
        idx = filename.rfind(".")
        if idx == -1:
            return ""
        return filename[idx:].lower()
