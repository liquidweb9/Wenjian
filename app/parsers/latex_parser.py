"""Single-file LaTeX parser - static analysis only, no compilation."""

import re
from pylatexenc import latexwalker, latex2text
from pylatexenc.latexwalker import (
    LatexWalker,
    LatexEnvironmentNode,
    LatexMacroNode,
    LatexMathNode,
)
from app.parsers.base import ResumeParser
from app.parsers.schemas import ParseInput, ResumeDocument, ResumeBlock, SourceLocation
from app.parsers.quality import assess_quality
from app.core.ids import new_id
from app.core.exceptions import AppError, LATEX_PARSE_FAILED, LATEX_MULTI_FILE_NOT_SUPPORTED


# Custom macro definitions for resume-specific commands
CUSTOM_MACRO_RULES = {
    "datedsubsection": {
        "arg_names": ["title", "date"],
        "template": "{date}\n{title}",
        "block_type": "entry_header",
    },
    "resumeItem": {
        "arg_names": ["content"],
        "template": "• {content}",
        "block_type": "bullet",
    },
    "role": {
        "arg_names": ["organization", "department"],
        "template": "{organization} {department}",
        "block_type": "entry_header",
    },
}

DANGEROUS_COMMANDS = {"write18", "input", "include", "openin", "openout"}


class LatexParser(ResumeParser):
    name = "latex_parser"
    version = "0.1.0"

    async def parse(self, parse_input: ParseInput) -> ResumeDocument:
        source_text = parse_input.content.decode("utf-8", errors="replace")

        # Expand custom macros before parsing
        source_text = self._expand_macros(source_text)

        # Security check
        self._check_dangerous(source_text)

        # Two-stage parsing:
        # 1. Walk LaTeX AST
        walker = LatexWalker(source_text)
        try:
            ast, _, _ = walker.get_latex_nodes()
        except Exception as e:
            raise AppError(LATEX_PARSE_FAILED, f"LaTeX parse error: {e}")

        # 2. Extract blocks from AST
        blocks = self._extract_blocks(ast, source_text)

        # Convert to text
        l2t = latex2text.LatexNodes2Text()
        normalized_text = l2t.nodelist_to_text(ast) if ast else source_text

        quality_result = assess_quality(blocks)
        warnings = list(quality_result.get("warnings", []))

        return ResumeDocument(
            resume_id="",
            source_id=parse_input.source_id,
            file_name=parse_input.file_name,
            source_type="latex",
            raw_text=source_text,
            normalized_text=normalized_text.strip(),
            blocks=blocks,
            extraction_method="latex_static",
            extraction_quality=quality_result["score"],
            extraction_warnings=warnings,
            parser_name=self.name,
            parser_version=self.version,
        )

    def _expand_macros(self, content: str) -> str:
        """Expand custom resume macros to standard LaTeX before pylatexenc parsing.

        Handles:
          \\datedsubsection{title}{date}  ->  \\subsection{title}
          \\resumeItem{content}            ->  \\item content
          \\role{org}{dept}                ->  org | dept
        """
        # \datedsubsection{title}{date} -> \subsection{title}
        content = re.sub(
            r'\\datedsubsection\{([^}]*)\}\{([^}]*)\}',
            r'\\subsection{\1}',
            content,
        )
        # \resumeItem{content} -> \item content
        content = re.sub(
            r'\\resumeItem\{([^}]*)\}',
            r'\\item \1',
            content,
        )
        # \role{org}{dept} -> org | dept
        content = re.sub(
            r'\\role\{([^}]*)\}\{([^}]*)\}',
            r'\1 | \2',
            content,
        )
        return content

    def _check_dangerous(self, text: str):
        for cmd in DANGEROUS_COMMANDS:
            pattern = r"\\" + cmd + r"\b"
            if re.search(pattern, text):
                raise AppError(
                    LATEX_MULTI_FILE_NOT_SUPPORTED,
                    f"Unsupported LaTeX command: \\{cmd}",
                )

    def _extract_blocks(self, nodes_list: list, source_text: str) -> list[ResumeBlock]:
        blocks = []
        if not nodes_list:
            return blocks

        for node in nodes_list:
            if isinstance(node, LatexEnvironmentNode):
                env_name = node.environmentname if hasattr(node, 'environmentname') else ""
                env_text = self._node_text(node, source_text)
                btype = "bullet" if env_name in ("itemize", "enumerate") else "paragraph"
                blocks.append(ResumeBlock(
                    block_id=new_id("blk"),
                    text=env_text,
                    block_type=btype,  # type: ignore
                    source_location=SourceLocation(latex_node_type=f"env:{env_name}"),
                ))
            elif isinstance(node, LatexMacroNode):
                macro_name = node.macroname if hasattr(node, 'macroname') else ""
                macro_text = self._node_text(node, source_text)
                btype = "heading" if macro_name in ("section", "subsection") else "paragraph"
                blocks.append(ResumeBlock(
                    block_id=new_id("blk"),
                    text=macro_text,
                    block_type=btype,  # type: ignore
                    source_location=SourceLocation(latex_node_type=f"macro:{macro_name}"),
                ))
            elif isinstance(node, LatexMathNode):
                continue
            else:
                node_text = self._node_text(node, source_text)
                if node_text.strip():
                    blocks.append(ResumeBlock(
                        block_id=new_id("blk"),
                        text=node_text.strip(),
                        block_type="paragraph",
                        source_location=SourceLocation(latex_node_type=type(node).__name__),
                    ))

        return blocks

    def _node_text(self, node, source_text: str) -> str:
        """Extract text from a LaTeX node."""
        try:
            l2t = latex2text.LatexNodes2Text()
            if isinstance(node, LatexMacroNode):
                text = l2t.nodelist_to_text(node.nodeargd) if hasattr(node, 'nodeargd') and node.nodeargd else ""
            elif hasattr(node, 'nodelist') and node.nodelist:
                text = l2t.nodelist_to_text(node.nodelist)
            else:
                text = source_text[node.pos:node.pos+node.len] if hasattr(node, 'pos') and hasattr(node, 'len') else ""
            return text.strip()
        except Exception:
            return ""
