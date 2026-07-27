from typing import Literal
from pydantic import BaseModel, Field


class ParseInput(BaseModel):
    source_id: str
    file_name: str
    declared_mime_type: str | None = None
    content: bytes


class SourceLocation(BaseModel):
    page_number: int | None = None
    block_index: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    char_start: int | None = None
    char_end: int | None = None
    latex_node_type: str | None = None


class ResumeBlock(BaseModel):
    block_id: str
    text: str
    raw_text: str | None = None

    block_type: Literal[
        "heading", "entry_header", "paragraph", "bullet", "contact", "unknown",
    ] = "unknown"

    source_location: SourceLocation = Field(default_factory=SourceLocation)
    style_hints: dict[str, str | float | bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ResumeDocument(BaseModel):
    resume_id: str
    source_id: str
    file_name: str
    source_type: Literal["pdf", "text", "latex"]

    raw_text: str
    normalized_text: str
    blocks: list[ResumeBlock]

    extraction_method: Literal["pdf_text", "plain_text", "latex_static"]

    extraction_quality: float = Field(ge=0, le=1)
    extraction_warnings: list[str] = Field(default_factory=list)

    parser_name: str
    parser_version: str
    revision_id: str = ""
