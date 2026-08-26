"""Quebra tabelas Markdown em fatos por linha ou célula."""

from __future__ import annotations

import re

from rag.text import normalize

_SEP = re.compile(r"^\s*\|?\s*:?-{2,}.*\|")
_MONTH = r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)"
_PERIOD_HEADER = re.compile(
    rf"^(fy\s*20\d{{2}}|q[1-4](?:\s*20\d{{2}})?|p[1-4](?:\s*20\d{{2}})?|"
    rf"r12\b.*|{_MONTH}\s*/\s*20\d{{2}}|20\d{{2}}|[δΔ]|delta)$",
    re.IGNORECASE,
)
_DATE_CELL = re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$")


def split_prose_and_tables(body: str) -> list[tuple[str, str]]:
    """Retorna blocos ('prose'|'table', texto). Preserva pipes e quebras da tabela."""
    lines = body.replace("\r\n", "\n").split("\n")
    blocks: list[tuple[str, str]] = []
    buf: list[str] = []
    mode = "prose"

    def flush() -> None:
        nonlocal buf, mode
        text = "\n".join(buf).strip() if mode == "table" else _collapse_prose("\n".join(buf))
        if text:
            blocks.append((mode, text))
        buf = []

    for line in lines:
        table_line = _is_table_line(line)
        if table_line and mode == "prose":
            flush()
            mode = "table"
            buf = [line]
        elif table_line and mode == "table":
            buf.append(line)
        elif not table_line and mode == "table":
            flush()
            mode = "prose"
            buf = [line]
        else:
            buf.append(line)
    flush()
    return blocks


def explode_table(markdown: str, *, heading: str = "") -> list[dict[str, str]]:
    """Uma entrada por linha ou, se as colunas forem períodos, por célula."""
    rows = _parse_rows(markdown)
    if len(rows) < 2:
        return []
    header, *data = rows
    header = [_clean(h) for h in header]
    data = [[_clean(c) for c in row] for row in data if any(_clean(c) for c in row)]
    if not data:
        return []
    width = len(header)
    data = [_pad(row, width) for row in data]
    facts: list[dict[str, str]] = []
    if _is_period_header(header):
        metric_h = header[0] or "indicador"
        for row in data:
            metric = row[0]
            if not metric:
                continue
            for i, period in enumerate(header[1:], start=1):
                value = row[i] if i < len(row) else ""
                if not value or value in {"---", "-"}:
                    continue
                facts.append(
                    _fact(
                        heading,
                        markdown=_mini_table([metric_h, period], [metric, value]),
                        prose=f"{metric} em {period}: {value}.",
                        period=period,
                        metric=metric,
                    )
                )
        return facts
    for row in data:
        pairs = [f"{h}: {c}" for h, c in zip(header, row) if h and c]
        if not pairs:
            continue
        row_period = row[0] if _DATE_CELL.match(row[0] or "") else ""
        facts.append(
            _fact(
                heading,
                markdown=_mini_table(header, row),
                prose="; ".join(pairs) + ".",
                period=row_period,
                metric=row[0],
            )
        )
    return facts


def _fact(heading: str, *, markdown: str, prose: str, period: str, metric: str) -> dict[str, str]:
    title = heading.strip()
    body = f"{title}\n\n{prose}\n\n{markdown}".strip() if title else f"{prose}\n\n{markdown}"
    return {"text": body, "period": period, "metric": metric, "kind": "table_fact"}


def _is_period_header(header: list[str]) -> bool:
    if len(header) < 2:
        return False
    cols = header[1:]
    timed = sum(1 for h in cols if _looks_like_period(h))
    need = max(1, (len(cols) + 1) // 2)
    return timed >= need


def _looks_like_period(label: str) -> bool:
    raw = label.strip()
    if not raw:
        return False
    if raw in {"Δ", "δ"}:
        return True
    n = normalize(raw).strip()
    return bool(_PERIOD_HEADER.match(n) or _PERIOD_HEADER.match(raw))


def _is_table_line(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    return s.count("|") >= 2


def _parse_rows(markdown: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown.split("\n"):
        if not _is_table_line(line) or _SEP.match(line.strip()):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if parts:
            rows.append(parts)
    return rows


def _mini_table(header: list[str], row: list[str]) -> str:
    width = max(len(header), len(row))
    header = _pad(header, width)
    row = _pad(row, width)
    sep = "| " + " | ".join("---" for _ in header) + " |"
    h = "| " + " | ".join(header) + " |"
    r = "| " + " | ".join(row) + " |"
    return f"{h}\n{sep}\n{r}"


def _pad(cells: list[str], width: int) -> list[str]:
    out = list(cells)
    while len(out) < width:
        out.append("")
    return out[:width]


def _clean(cell: str) -> str:
    return " ".join(cell.replace("**", "").split())


def _collapse_prose(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
