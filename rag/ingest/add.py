"""Adiciona arquivos ao corpus: converte para .md e, se o usuário quiser, atualiza o índice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.config import Settings
from rag.ingest.markdown import ConvertResult, convert_path
from rag.ingest.pipeline import IngestResult, ingest


@dataclass
class AddResult:
    converted: ConvertResult
    ingested: IngestResult | None = None


def add_files(
    source: Path,
    settings: Settings,
    *,
    dest_dir: Path | None = None,
    overwrite: bool = False,
    update_index: bool = False,
) -> AddResult:
    dest = dest_dir or settings.documents_dir
    converted = convert_path(source, dest, overwrite=overwrite)
    ingested = None
    if update_index:
        ingested = ingest(settings.documents_dir, settings)
    return AddResult(converted=converted, ingested=ingested)
