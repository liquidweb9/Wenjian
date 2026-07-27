"""PDF parser using PyMuPDF - supports text-based PDFs only."""

import fitz  # PyMuPDF
import re
from app.parsers.base import ResumeParser
from app.parsers.schemas import ParseInput, ResumeDocument, ResumeBlock, SourceLocation
from app.parsers.quality import assess_quality
from app.core.enums import BlockType
from app.core.ids import new_id
from app.core.exceptions import AppError, PDF_ENCRYPTED, PDF_NO_TEXT


class PdfParser(ResumeParser):
    name = "pdf_parser"
    version = "0.1.0"

    async def parse(self, parse_input: ParseInput) -> ResumeDocument:
        try:
            doc = fitz.open(stream=parse_input.content, filetype="pdf")
        except Exception as e:
            raise AppError(PDF_ENCRYPTED, f"Cannot open PDF: {e}")

        if doc.is_encrypted:
            doc.close()
            raise AppError(PDF_ENCRYPTED, "PDF is encrypted")

        blocks: list[ResumeBlock] = []
        raw_text_parts: list[str] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_blocks = page.get_text("blocks")
            page_dict = page.get_text("dict")

            for b in page_blocks:
                x0, y0, x1, y1, text, block_no, block_type = b

                text = text.strip()
                if not text:
                    continue

                # Filter header/footer noise
                if self._is_header_footer(text, page.rect.height, y0):
                    continue

                block = ResumeBlock(
                    block_id=new_id("blk"),
                    text=text,
                    raw_text=text,
                    block_type=self._classify_block(text),
                    source_location=SourceLocation(
                        page_number=page_num + 1,
                        block_index=block_no,
                        bbox=(x0, y0, x1, y1),
                    ),
                    style_hints=self._extract_styles(page_dict, block_no),
                )
                blocks.append(block)
                raw_text_parts.append(text)

        doc.close()

        # Sort by reading order (per-page then concatenated)
        blocks = self._sort_reading_order(blocks)

        raw_text = "\n".join(raw_text_parts)
        normalized_text = self._normalize_text(raw_text)

        if not raw_text.strip() or len(raw_text.strip()) < 50:
            raise AppError(PDF_NO_TEXT, "No extractable text found in PDF")

        quality_result = assess_quality(blocks)
        warnings = list(quality_result.get("warnings", []))

        # Two-column layout detection (after quality assessment)
        if self._detect_two_column_layout(blocks):
            warnings.append("POSSIBLE_TWO_COLUMN_ORDER_ERROR")

        return ResumeDocument(
            resume_id="",
            source_id=parse_input.source_id,
            file_name=parse_input.file_name,
            source_type="pdf",
            raw_text=raw_text,
            normalized_text=normalized_text,
            blocks=blocks,
            extraction_method="pdf_text",
            extraction_quality=quality_result["score"],
            extraction_warnings=warnings,
            parser_name=self.name,
            parser_version=self.version,
        )

    def _sort_reading_order(self, blocks: list[ResumeBlock]) -> list[ResumeBlock]:
        """Sort blocks within each page by vertical then horizontal position,
        then concatenate pages in page order."""
        from collections import defaultdict

        # Group by page number
        pages: dict[int, list[ResumeBlock]] = defaultdict(list)
        for b in blocks:
            page_num = b.source_location.page_number or 1
            pages[page_num].append(b)

        # Sort each page's blocks and concatenate in page order
        result: list[ResumeBlock] = []
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            page_blocks.sort(key=lambda blk: (
                blk.source_location.bbox[1] if blk.source_location.bbox else 0,
                blk.source_location.bbox[0] if blk.source_location.bbox else 0,
            ))
            result.extend(page_blocks)

        return result

    def _detect_two_column_layout(self, blocks: list[ResumeBlock]) -> bool:
        """Detect if the document likely has a two-column layout.

        Collects x-coordinates of block centers from page 1.
        If blocks cluster into two distinct x-regions (more than 200px apart),
        returns True indicating a possible two-column layout.
        """
        page1_x_centers = []
        for b in blocks:
            loc = b.source_location
            if loc.page_number == 1 and loc.bbox:
                x0, _, x1, _ = loc.bbox
                center = (x0 + x1) / 2
                page1_x_centers.append(center)

        if len(page1_x_centers) < 4:
            return False

        page1_x_centers.sort()
        midpoint = len(page1_x_centers) // 2
        left_cluster = page1_x_centers[:midpoint]
        right_cluster = page1_x_centers[midpoint:]

        if len(left_cluster) < 2 or len(right_cluster) < 2:
            return False

        gap = right_cluster[0] - left_cluster[-1]
        return gap > 200

    def _is_header_footer(self, text: str, page_height: float, y0: float) -> bool:
        if len(text.strip()) < 5:
            return True
        # Check if in header/footer zone (top 8% or bottom 8% of page)
        if y0 < page_height * 0.08 or y0 > page_height * 0.92:
            if re.match(r"^\d+$", text.strip()):
                return True
        return False

    def _classify_block(self, text: str) -> str:
        if text.startswith(("• ", "- ", "* ", "· ")):
            return "bullet"
        if len(text) < 60 and text.isupper():
            return "heading"
        return "paragraph"

    def _extract_styles(self, page_dict: dict, block_no: int) -> dict:
        styles = {}
        for block in page_dict.get("blocks", []):
            if block.get("number") == block_no:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font = span.get("font", "")
                        size = span.get("size", 0)
                        if font:
                            styles["font"] = font
                            styles["size"] = size
                            styles["bold"] = "Bold" in font
                            break
        return styles

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
