"""CLI: ingest, conversão para Markdown e chat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from rag.config import load_settings
from rag.ingest.add import add_files
from rag.ingest.markdown import CONVERTIBLE
from rag.ingest.pipeline import ingest
from rag.mcp_ready.adapter import tools_to_mcp

console = Console()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag", description="RAG — ingestão e agente de chat")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Lê o corpus (Markdown e outros) e grava o índice")
    p_ing.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Arquivo ou pasta (padrão: DOCUMENTS_DIR)",
    )

    p_add = sub.add_parser(
        "add",
        help="Converte .docx/.txt/.pdf/… em .md e pergunta se inclui no RAG",
    )
    p_add.add_argument("source", help="Arquivo ou pasta de origem")
    p_add.add_argument(
        "--out",
        default=None,
        help="Pasta destino dos .md (padrão: DOCUMENTS_DIR)",
    )
    p_add.add_argument("--force", action="store_true", help="Sobrescreve .md já existente")
    p_add.add_argument(
        "--ingest",
        action="store_true",
        help="Atualiza o índice RAG sem perguntar",
    )
    p_add.add_argument(
        "--no-ingest",
        action="store_true",
        help="Só gera os .md, sem mexer no índice",
    )

    p_chat = sub.add_parser("chat", help="Abre o agente de chat sobre o índice")
    p_chat.add_argument("--trace", action="store_true", help="Mostra o loop do agente")

    p_ask = sub.add_parser("ask", help="Uma pergunta só (útil para teste)")
    p_ask.add_argument("question")
    p_ask.add_argument("--trace", action="store_true")

    sub.add_parser("tools", help="Lista tools no formato MCP")

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        return cmd_ingest(args.source)
    if args.cmd == "add":
        return cmd_add(
            args.source,
            dest=args.out,
            overwrite=args.force,
            ingest_flag=args.ingest,
            no_ingest=args.no_ingest,
        )
    if args.cmd == "chat":
        return cmd_chat(show_trace=args.trace)
    if args.cmd == "ask":
        return cmd_ask(args.question, show_trace=args.trace)
    if args.cmd == "tools":
        return cmd_tools()
    return 1


def cmd_ingest(source: str | None) -> int:
    settings = load_settings()
    path = Path(source) if source else settings.documents_dir
    console.print(f"[bold]Ingerindo[/bold] {path}")
    result = ingest(path, settings)
    _print_ingest(result)
    return 0


def cmd_add(
    source: str,
    *,
    dest: str | None,
    overwrite: bool,
    ingest_flag: bool,
    no_ingest: bool,
) -> int:
    settings = load_settings()
    dest_dir = Path(dest) if dest else settings.documents_dir
    try:
        result = add_files(
            Path(source),
            settings,
            dest_dir=dest_dir,
            overwrite=overwrite,
            update_index=False,
        )
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    _print_convert(result.converted)
    if not result.converted.written and not result.converted.skipped:
        return 1
    if no_ingest:
        console.print("[dim]Índice não foi alterado (--no-ingest).[/dim]")
        return 0
    if ingest_flag:
        update = True
    elif sys.stdin.isatty():
        update = _confirm_ingest(len(result.converted.written))
    else:
        console.print(
            "[yellow]Conversão ok. Passe --ingest para incluir no RAG "
            "ou rode: python -m rag ingest[/yellow]"
        )
        return 0
    if not update:
        console.print("[dim]Ok. Os .md ficaram no corpus; o índice permanece como está.[/dim]")
        return 0
    ingested = ingest(settings.documents_dir, settings)
    _print_ingest(ingested)
    return 0


def cmd_chat(*, show_trace: bool) -> int:
    from rag.app import build_app

    try:
        app = build_app()
    except FileNotFoundError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        console.print("Dica: python -m rag add <arquivo>  ou  python -m rag ingest")
        return 1
    console.print(
        Panel(
            "Agente RAG.\n"
            "[bold]/sair[/bold] encerra · [bold]/trace[/bold] rastro das tools · "
            f"[bold]/add caminho[/bold] converte para .md e pergunta se inclui no RAG.\n"
            f"Formatos: {', '.join(sorted(CONVERTIBLE))}",
            title=app.agent.name,
        )
    )
    while True:
        try:
            user = console.input("[bold cyan]você>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nAté logo.")
            return 0
        if not user:
            continue
        if user.lower() in {"/sair", "/exit", "/quit"}:
            return 0
        if user.lower() == "/trace":
            show_trace = not show_trace
            console.print(f"trace={'ligado' if show_trace else 'desligado'}")
            continue
        if user.lower().startswith("/add"):
            app = _chat_add(app, user)
            continue
        result = app.agent.run(user)
        style = "green" if result.answer_ok and result.quality_ok else "yellow"
        console.print(Panel(Markdown(result.text), title="agente", border_style=style))
        if result.citations:
            cites = Table(title="fontes")
            cites.add_column("#", style="dim")
            cites.add_column("arquivo")
            cites.add_column("trecho")
            for i, c in enumerate(result.citations, start=1):
                cites.add_row(str(i), str(c["source"]), str(c["preview"]))
            console.print(cites)
        if show_trace:
            console.print("[dim]" + "\n".join(result.tool_trace) + "[/dim]")
    return 0


def _chat_add(app: object, command: str) -> object:
    from rag.app import build_app

    parts = command.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        console.print("[yellow]Uso: /add caminho/do/arquivo.docx[/yellow]")
        return app
    source = Path(parts[1].strip().strip('"').strip("'"))
    settings = load_settings()
    try:
        result = add_files(source, settings, update_index=False)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        return app
    _print_convert(result.converted)
    if not result.converted.written:
        return app
    if not _confirm_ingest(len(result.converted.written)):
        console.print("[dim]Convertido. Índice inalterado.[/dim]")
        return app
    ingested = ingest(settings.documents_dir, settings)
    _print_ingest(ingested)
    console.print("[green]Índice atualizado. Pode perguntar sobre o material novo.[/green]")
    return build_app()


def cmd_ask(question: str, *, show_trace: bool) -> int:
    from rag.app import build_app

    app = build_app()
    result = app.agent.run(question)
    console.print(Panel(Markdown(result.text), title="agente"))
    if show_trace:
        console.print("[dim]" + "\n".join(result.tool_trace) + "[/dim]")
    return 0 if result.answer_ok and result.quality_ok else 2


def cmd_tools() -> int:
    from rag.app import build_app

    app = build_app()
    for spec in tools_to_mcp(app.agent):
        console.print(f"[bold]{spec['name']}[/bold] — {spec['description']}")
    return 0


def _confirm_ingest(n_files: int) -> bool:
    label = "arquivo" if n_files == 1 else "arquivos"
    answer = console.input(
        f"[bold]Incluir {n_files} {label} no índice RAG agora?[/bold] [s/N] "
    ).strip().lower()
    return answer in {"s", "sim", "y", "yes"}


def _print_convert(converted) -> None:
    table = Table(title="Conversão para Markdown")
    table.add_column("origem")
    table.add_column("markdown")
    table.add_column("status")
    for item in converted.written:
        table.add_row(str(item.source), str(item.markdown_path), "[green]gravado[/green]")
    for item in converted.skipped:
        table.add_row(str(item.source), str(item.markdown_path), f"[yellow]{item.reason}[/yellow]")
    console.print(table)
    if not converted.written and converted.skipped:
        console.print("[yellow]Nada novo gravado.[/yellow]")


def _print_ingest(result) -> None:
    table = Table(title="Índice RAG")
    table.add_column("campo")
    table.add_column("valor")
    table.add_row("documentos", str(result.documents))
    table.add_row("chunks", str(result.chunks))
    table.add_row("duplicatas descartadas", str(result.dropped_duplicates))
    table.add_row("índice", str(result.index_dir))
    table.add_row("fontes", "\n".join(result.sources) or "—")
    console.print(table)
