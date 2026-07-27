"""Parsing quality assessment using ResumeBlock objects."""

from app.parsers.schemas import ResumeBlock


def assess_quality(blocks: list[ResumeBlock]) -> dict:
    """Assess parsing quality based on block characteristics.

    Uses the architecture-defined formula:
    0.25 x text_density + 0.20 x readable_ratio + 0.20 x reading_order_confidence
    + 0.20 x section_confidence + 0.15 x line_merge_confidence
    """
    if not blocks:
        return {"score": 0.0, "warnings": ["NO_BLOCKS"]}

    total_chars = sum(len(b.text) for b in blocks)
    if total_chars == 0:
        return {"score": 0.0, "warnings": ["NO_TEXT_CONTENT"]}

    # Text density
    text_density = min(1.0, total_chars / 5000)

    # Readable character ratio
    all_text = "".join(b.text for b in blocks)
    readable = sum(1 for c in all_text if c.isalpha() or c.isspace())
    readable_ratio = readable / max(len(all_text), 1)

    # Section confidence — check if we have headings
    heading_count = sum(1 for b in blocks if b.block_type == "heading")
    section_confidence = min(1.0, heading_count / max(3, 1))

    # Reading order confidence — check bbox consistency
    reading_order_confidence = _reading_order_confidence(blocks)

    # Line merge confidence
    line_merge_confidence = 0.7  # default for text parsers
    if any(b.source_location.bbox for b in blocks):
        line_merge_confidence = 0.8

    score = (
        0.25 * text_density
        + 0.20 * readable_ratio
        + 0.20 * reading_order_confidence
        + 0.20 * section_confidence
        + 0.15 * line_merge_confidence
    )

    warnings = []
    if score < 0.6:
        warnings.append("PARSE_QUALITY_TOO_LOW")

    return {"score": round(min(1.0, score), 2), "warnings": warnings}


def _reading_order_confidence(blocks: list[ResumeBlock]) -> float:
    """Check if blocks with bbox data have consistent ordering."""
    bbox_blocks = [b for b in blocks if b.source_location.bbox is not None]
    if not bbox_blocks:
        return 0.5  # no bbox data, medium confidence
    if len(bbox_blocks) < 2:
        return 0.8

    # Check that y-coordinates are generally increasing
    y_vals = [b.source_location.bbox[1] for b in bbox_blocks]  # type: ignore
    increasing = sum(1 for i in range(1, len(y_vals)) if y_vals[i] >= y_vals[i-1])
    return min(1.0, increasing / max(len(y_vals) - 1, 1))
