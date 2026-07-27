"""File type detection using magic bytes, MIME, and extension."""

from typing import TYPE_CHECKING

from app.core.exceptions import AppError, RESUME_TYPE_MISMATCH

if TYPE_CHECKING:
    from app.parsers.base import ResumeParser


def detect_source_type(head_bytes: bytes, mime_type: str | None, extension: str) -> str:
    """Detect source type from content, MIME, and extension (loose detection)."""
    if head_bytes.startswith(b"%PDF-"):
        return "pdf"
    if head_bytes.startswith(b"\\") or head_bytes.startswith(b"%") or head_bytes.startswith(b"\x5c"):
        return "latex"

    if mime_type:
        if "pdf" in mime_type:
            return "pdf"
        if "latex" in mime_type:
            return "latex"
        if mime_type in ("text/x-tex", "application/x-tex", "application/x-latex"):
            return "latex"

    ext = extension.lower()
    if ext in (".pdf",):
        return "pdf"
    if ext in (".tex", ".ltx", ".latex"):
        return "latex"
    if ext in (".txt", ".text", ""):
        return "text"

    # Loose fallback: treat unknown extensions as plain text
    return "text"


def _get_signals(head_bytes: bytes, mime_type: str | None, extension: str) -> dict[str, set[str]]:
    """Evaluate each detection signal independently.

    Returns a dict keyed by signal name ('magic', 'mime', 'extension')
    containing the set of types each signal indicates.
    """
    signals: dict[str, set[str]] = {"magic": set(), "mime": set(), "extension": set()}

    # Magic bytes
    if head_bytes.startswith(b"%PDF-"):
        signals["magic"].add("pdf")
    if head_bytes.startswith(b"\\") or head_bytes.startswith(b"%") or head_bytes.startswith(b"\x5c"):
        signals["magic"].add("latex")

    # MIME type
    if mime_type:
        if "pdf" in mime_type:
            signals["mime"].add("pdf")
        if "latex" in mime_type:
            signals["mime"].add("latex")
        if mime_type in ("text/x-tex", "application/x-tex", "application/x-latex"):
            signals["mime"].add("latex")

    # Extension
    ext = extension.lower()
    if ext in (".pdf",):
        signals["extension"].add("pdf")
    if ext in (".tex", ".ltx", ".latex"):
        signals["extension"].add("latex")
    if ext in (".txt", ".text", ""):
        signals["extension"].add("text")

    return signals


def strict_detect(head_bytes: bytes, mime_type: str | None, extension: str) -> str:
    """Detect source type requiring at least 2 of 3 signals (magic, MIME, extension).

    Raises AppError with RESUME_TYPE_MISMATCH if fewer than 2 signals agree.
    """
    signals = _get_signals(head_bytes, mime_type, extension)

    # Count votes per type across all signals
    votes: dict[str, int] = {}
    for signal_set in signals.values():
        for t in signal_set:
            votes[t] = votes.get(t, 0) + 1

    if not votes:
        raise AppError(RESUME_TYPE_MISMATCH, "No type signals detected")

    # Find the type with the most votes
    best_type = max(votes, key=votes.get)
    if votes[best_type] >= 2:
        return best_type

    raise AppError(
        RESUME_TYPE_MISMATCH,
        f"Insufficient signals to determine type confidently "
        f"(best: {best_type} with {votes[best_type]}/3 signals)",
    )
