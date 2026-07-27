"""Tests for file type detector."""

import pytest
from app.parsers.detector import detect_source_type


class TestDetector:
    def test_detect_pdf_by_magic(self):
        result = detect_source_type(b"%PDF-1.4\n...", None, ".pdf")
        assert result == "pdf"

    def test_detect_latex_by_backslash(self):
        result = detect_source_type(b"\\documentclass{article}", None, ".tex")
        assert result == "latex"

    def test_detect_latex_by_percent(self):
        result = detect_source_type(b"% This is a LaTeX comment", None, ".tex")
        assert result == "latex"

    def test_detect_by_mime_pdf(self):
        result = detect_source_type(b"dummy", "application/pdf", "")
        assert result == "pdf"

    def test_detect_by_mime_latex_explicit(self):
        result = detect_source_type(b"dummy", "text/x-tex", "")
        assert result == "latex"

    def test_detect_by_extension_pdf(self):
        result = detect_source_type(b"hello", None, ".pdf")
        assert result == "pdf"

    def test_detect_by_extension_tex(self):
        result = detect_source_type(b"hello", None, ".tex")
        assert result == "latex"

    def test_detect_by_extension_txt(self):
        result = detect_source_type(b"hello", None, ".txt")
        assert result == "text"

    def test_detect_by_extension_text(self):
        result = detect_source_type(b"hello", None, ".text")
        assert result == "text"

    def test_text_mime_does_not_match_latex(self):
        """Regression test: 'text/plain' should NOT be detected as LaTeX."""
        result = detect_source_type(b"John Doe\nSoftware Engineer", "text/plain", ".txt")
        assert result == "text"

    def test_default_fallback(self):
        result = detect_source_type(b"random content", None, ".unknown")
        assert result == "text"
