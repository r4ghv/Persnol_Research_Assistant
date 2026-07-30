import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

SECTION_HEADERS = [
    "abstract", "introduction", "background", "related work",
    "methods", "methodology", "approach", "framework",
    "experiments", "experimental setup", "results",
    "discussion", "conclusion", "conclusions", "future work",
    "references", "bibliography", "appendix",
]

SECTION_PATTERN = re.compile(
    r"^(\d+\.?\s*)?(" + "|".join(SECTION_HEADERS) + r")(?:[.:\s]|$)",
    re.IGNORECASE,
)


def clean_pdf_text(raw: str) -> str:
    """Remove common PDF artifacts from extracted text."""
    if not raw:
        return ""

    text = raw

    # Remove page numbers (isolated digits or "Page X of Y")
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?i)page\s+\d+\s+of\s+\d+", "", text)

    # Remove arXiv identifiers
    text = re.sub(r"(?i)arXiv:\d{4}\.\d{4,5}(v\d+)?", "", text)

    # Remove LaTeX citation/ref markers
    text = re.sub(r"\\cite\{[^}]*\}", "", text)
    text = re.sub(r"\\ref\{[^}]*\}", "", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)

    # Remove LaTeX math environments (keep inline text roughly)
    text = re.sub(r"\\begin\{equation\}.*?\\end\{equation\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\begin\{align\}.*?\\end\{align\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\\[.*?\\\]", "", text, flags=re.DOTALL)
    text = re.sub(r"\$[^\$]+\$", "", text)

    # Remove LaTeX commands like \textit{}, \textbf{}, etc. but keep inner text
    text = re.sub(r"\\[a-zA-Z]+(\{[^}]*\})?", r"\1", text)

    # Remove common running headers (short lines that appear repeatedly at same position)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Drop very short lines that are likely artifacts
        if len(stripped) < 3 and stripped:
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim reference/bibliography section
    ref_match = re.search(
        r"(?i)^(references|bibliography)\s*\n",
        text,
        re.MULTILINE,
    )
    if ref_match:
        text = text[: ref_match.start()]

    return text.strip()


def detect_sections(text: str) -> List[Tuple[str, str]]:
    """Split text into labeled sections.
    Returns list of (section_name, section_text).
    """
    lines = text.split("\n")
    sections = []
    current_label = "general"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        match = SECTION_PATTERN.match(stripped)
        if match:
            if current_lines:
                sections.append((current_label, "\n".join(current_lines).strip()))
            title = match.group(2).strip().lower()
            # Remove the header itself from the content
            body = stripped[match.end():].strip()
            current_label = title
            current_lines = [body] if body else []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_label, "\n".join(current_lines).strip()))

    return sections


def chunk_sections(
    sections: List[Tuple[str, str]],
    chunk_size: int = 3000,
    overlap: int = 200,
) -> List[str]:
    """Split labeled sections into overlapping text chunks."""
    chunks: List[str] = []

    for label, section_text in sections:
        if not section_text:
            continue

        # Short sections stay whole
        if len(section_text) <= chunk_size:
            prefix = f"[{label.title()}]\n" if label != "general" else ""
            chunks.append(prefix + section_text)
            continue

        # Long sections are split on paragraphs
        paragraphs = re.split(r"\n\n+", section_text)
        buffer = ""

        for para in paragraphs:
            if not para.strip():
                continue
            prefix = f"[{label.title()}]\n" if label != "general" else ""
            candidate = prefix + para.strip()

            if not buffer:
                buffer = candidate
            elif len(buffer) + len(candidate) + 1 <= chunk_size:
                buffer += "\n\n" + candidate
            else:
                chunks.append(buffer)
                # Add overlap: last `overlap` chars from previous chunk
                overlap_text = buffer[-overlap:] if len(buffer) > overlap else buffer
                buffer = overlap_text + "\n\n" + candidate

        if buffer:
            chunks.append(buffer)

    return chunks


def preprocess_and_chunk(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
    """Full pipeline: clean → detect sections → chunk."""
    cleaned = clean_pdf_text(text)
    sections = detect_sections(cleaned)
    return chunk_sections(sections, chunk_size, overlap)


def build_chunked_prompt(
    title: str,
    abstract: str,
    chunks: List[str],
    include_all: bool = True,
    max_chunks: int = 5,
) -> str:
    """Build a prompt string from chunks, including as many as fit."""
    header = f"Title: {title}\nAbstract: {abstract}\n\nPaper Contents:\n"
    base = len(header) + 100  # buffer

    selected = []
    for chunk in chunks[:max_chunks]:
        delta = len(chunk) + 2
        if base + delta > 8000 and selected:
            if not include_all:
                break
        selected.append(chunk)
        base += delta

    body = "\n\n".join(f"--- {s}" for s in selected)
    return header + body
