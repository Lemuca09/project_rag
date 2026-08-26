"""Converte arquivos (.docx, .txt, .pdf, …) em Markdown para o corpus do RAG."""

from __future__ import annotations

import csv
import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

CONVERTIBLE = {".txt", ".md", ".pdf", ".docx", ".html", ".htm", ".csv"}


@dataclass
class ConvertedFile:
    source: Path
    markdown_path: Path
    skipped: bool = False
    reason: str = ""


@dataclass
class ConvertResult:
    written: list[ConvertedFile] = field(default_factory=list)
    skipped: list[ConvertedFile] = field(default_factory=list)

    @property
    def markdown_paths(self) -> list[Path]:
        return [item.markdown_path for item in self.written]


def convert_path(
    source: Path,
    dest_dir: Path,
    *,
    overwrite: bool = False,
) -> ConvertResult:
    source = source.resolve()
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    result = ConvertResult()
    files = _collect_files(source)
    if not files:
        raise ValueError(f"Nenhum arquivo conversível em {source}")
    root = source if source.is_dir() else source.parent
    for file in files:
        relative = _relative_stem(file, root)
        target = dest_dir / f"{relative}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            result.skipped.append(
                ConvertedFile(file, target, skipped=True, reason="já existe (use --force)")
            )
            continue
        markdown = file_to_markdown(file)
        if not markdown.strip():
            result.skipped.append(
                ConvertedFile(file, target, skipped=True, reason="arquivo vazio")
            )
            continue
        target.write_text(markdown, encoding="utf-8")
        result.written.append(ConvertedFile(file, target))
    return result


def file_to_markdown(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".txt":
        return _txt_to_markdown(path)
    if suffix == ".docx":
        return _docx_to_markdown(path)
    if suffix == ".pdf":
        return _pdf_to_markdown(path)
    if suffix in {".html", ".htm"}:
        return _html_to_markdown(path)
    if suffix == ".csv":
        return _csv_to_markdown(path)
    raise ValueError(f"Extensão não suportada: {suffix}")


def _collect_files(source: Path) -> list[Path]:
    if source.is_file():
        if source.suffix.lower() not in CONVERTIBLE:
            raise ValueError(
                f"Extensão não suportada: {source.suffix}. Use: {', '.join(sorted(CONVERTIBLE))}"
            )
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(f"Caminho inexistente: {source}")
    return sorted(
        p
        for p in source.rglob("*")
        if p.is_file() and p.suffix.lower() in CONVERTIBLE
    )


def _relative_stem(file: Path, root: Path) -> str:
    try:
        rel = file.relative_to(root)
    except ValueError:
        rel = Path(file.name)
    return str(rel.with_suffix("")).replace("\\", "/")


def _title_block(path: Path, body: str) -> str:
    title = path.stem.replace("_", " ").strip()
    body = body.strip()
    if body.lstrip().startswith("#"):
        return body + "\n"
    return f"# {title}\n\n{body}\n"


def _txt_to_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    paragraphs = re.split(r"\n\s*\n", text.strip())
    cleaned = "\n\n".join(p.strip() for p in paragraphs if p.strip())
    return _title_block(path, cleaned)


def _docx_to_markdown(path: Path) -> str:
    import docx
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(str(path))
    blocks: list[str] = []
    for child in document.element.body:
        if child.tag == qn("w:p"):
            para = Paragraph(child, document)
            md = _docx_paragraph(para)
            if md:
                blocks.append(md)
        elif child.tag == qn("w:tbl"):
            table = Table(child, document)
            md = _docx_table(table)
            if md:
                blocks.append(md)
    return _title_block(path, "\n\n".join(blocks))


def _docx_paragraph(para: object) -> str:
    style = ""
    raw_style = getattr(getattr(para, "style", None), "name", "") or ""
    style = raw_style.lower()
    text = _docx_runs(para)
    if not text.strip():
        return ""
    level = _heading_level(style)
    if level:
        return f"{'#' * level} {text}"
    if "list" in style or "lista" in style or "listagem" in style:
        marker = "1." if any(k in style for k in ("number", "numer", "decimal")) else "-"
        return f"{marker} {text}"
    return text


def _docx_runs(para: object) -> str:
    parts: list[str] = []
    for run in getattr(para, "runs", []):
        piece = (run.text or "").replace("\n", " ")
        if not piece:
            continue
        if getattr(run, "bold", False) and getattr(run, "italic", False):
            piece = f"***{piece}***"
        elif getattr(run, "bold", False):
            piece = f"**{piece}**"
        elif getattr(run, "italic", False):
            piece = f"*{piece}*"
        parts.append(piece)
    joined = "".join(parts).strip()
    return joined or (getattr(para, "text", "") or "").strip()


def _docx_table(table: object) -> str:
    rows: list[list[str]] = []
    for row in getattr(table, "rows", []):
        cells = [" ".join((cell.text or "").split()) for cell in row.cells]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    for row in rows:
        while len(row) < width:
            row.append("")
    header, *rest = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rest:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _heading_level(style: str) -> int | None:
    match = re.search(r"(?:heading|t[íi]tulo|titulo)\s*(\d+)", style)
    if match:
        return min(max(int(match.group(1)), 1), 6)
    if style in {"title", "título", "titulo"}:
        return 1
    if style in {"subtitle", "subtítulo", "subtitulo"}:
        return 2
    return None


def _pdf_to_markdown(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts: list[str] = [f"# {path.stem.replace('_', ' ').strip()}"]
    for i, page in enumerate(reader.pages, start=1):
        content = (page.extract_text() or "").strip()
        if not content:
            continue
        parts.append(f"## Página {i}")
        parts.append(content)
    return "\n\n".join(parts) + "\n"


def _html_to_markdown(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parser = _SimpleHtml()
    parser.feed(raw)
    body = parser.result().strip()
    return _title_block(path, body)


def _csv_to_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(StringIO(text), dialect)
    rows = [[cell.strip() for cell in row] for row in reader if any(c.strip() for c in row)]
    if not rows:
        return _title_block(path, "")
    width = max(len(r) for r in rows)
    for row in rows:
        while len(row) < width:
            row.append("")
    header, *rest = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rest:
        lines.append("| " + " | ".join(row) + " |")
    return _title_block(path, "\n".join(lines))


class _SimpleHtml(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False
        self._href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip = True
            return
        if tag in {"p", "div", "br", "tr"}:
            self._chunks.append("\n\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in {"li"}:
            self._chunks.append("\n- ")
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._chunks.append("[")
        elif tag in {"b", "strong"}:
            self._chunks.append("**")
        elif tag in {"i", "em"}:
            self._chunks.append("*")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip = False
            return
        if tag in {"b", "strong", "i", "em"}:
            self._chunks.append("*" if tag in {"i", "em"} else "**")
        if tag == "a":
            if self._href:
                self._chunks.append(f"]({self._href})")
            else:
                self._chunks.append("]")
            self._href = None
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = html.unescape(data)
        if not text.strip():
            return
        self._chunks.append(re.sub(r"\s+", " ", text))

    def result(self) -> str:
        text = "".join(self._chunks)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
