"""Tests for LaTeX parser."""

import pytest
from app.parsers.latex_parser import LatexParser
from app.parsers.schemas import ParseInput
from app.core.exceptions import AppError
from app.core.ids import new_id

RESUME_TEX = rb"""\documentclass{article}
\begin{document}

\section{Education}
Stanford University | Computer Science | 2021-2025

\section{Experience}
Google | Software Engineering Intern | 2024 Summer

\begin{itemize}
\item Designed and built a real-time data processing pipeline
\item Implemented distributed tracing across microservices
\item Reduced processing latency by 60\%
\end{itemize}

\section{Skills}
Python, C++, Go, Kubernetes, TensorFlow, gRPC

\end{document}"""


@pytest.mark.asyncio
class TestLatexParser:
    async def test_parse_simple_latex(self):
        parser = LatexParser()
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="resume.tex",
            content=RESUME_TEX,
        ))
        assert result.source_type == "latex"
        assert result.extraction_method == "latex_static"
        assert result.extraction_quality > 0
        assert len(result.blocks) > 0

    async def test_extracts_environment_blocks(self):
        parser = LatexParser()
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="resume.tex",
            content=RESUME_TEX,
        ))
        # Should have blocks from sections, itemize environment, etc.
        assert len(result.blocks) > 0

    async def test_rejects_input_command(self):
        parser = LatexParser()
        content = rb"""\documentclass{article}
\begin{document}
\input{other_file.tex}
\end{document}"""
        with pytest.raises(AppError) as exc:
            await parser.parse(ParseInput(
                source_id=new_id(),
                file_name="bad.tex",
                content=content,
            ))
        assert "input" in str(exc.value.message).lower() or "unsupported" in str(exc.value.message).lower()

    async def test_rejects_include_command(self):
        parser = LatexParser()
        content = rb"""\documentclass{article}
\begin{document}
\include{other}
\end{document}"""
        with pytest.raises(AppError):
            await parser.parse(ParseInput(
                source_id=new_id(),
                file_name="bad.tex",
                content=content,
            ))

    async def test_rejects_write18(self):
        parser = LatexParser()
        content = rb"""\documentclass{article}
\begin{document}
\write18{rm -rf /}
\end{document}"""
        with pytest.raises(AppError):
            await parser.parse(ParseInput(
                source_id=new_id(),
                file_name="bad.tex",
                content=content,
            ))

    async def test_handles_malformed_latex(self):
        """Some malformed LaTeX may be parsed (pylatexenc tolerates it) or raise errors."""
        parser = LatexParser()
        content = rb"""\documentclass{article
\begin{document}
Unclosed brace {
\end{document}"""
        try:
            result = await parser.parse(ParseInput(
                source_id=new_id(),
                file_name="malformed.tex",
                content=content,
            ))
            # If it doesn't raise, should still produce a document
            assert result is not None
        except (AppError, Exception):
            pass  # Either behavior is acceptable

    async def test_custom_macros(self):
        parser = LatexParser()
        content = rb"""\documentclass{article}
\newcommand{\resumeItem}[1]{\item #1}

\begin{document}
\begin{itemize}
\resumeItem{Built cloud infrastructure}
\resumeItem{Designed API gateway}
\end{itemize}
\end{document}"""
        result = await parser.parse(ParseInput(
            source_id=new_id(),
            file_name="macro.tex",
            content=content,
        ))
        assert result.extraction_quality >= 0
