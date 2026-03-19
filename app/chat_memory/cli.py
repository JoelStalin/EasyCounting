from __future__ import annotations

import argparse
import json
import os
import sys

from app.chat_memory.classify import build_session
from app.chat_memory.compliance import assess_chat_memory_compliance
from app.chat_memory.ingest import discover_local_conversation, load_conversation_from_file, load_conversation_from_text
from app.chat_memory.persist import persist_session
from app.chat_memory.policy import resolve_effective_roots


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Guarda y organiza historial de chat dentro del repo")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input-file", help="Ruta a un transcript .md, .txt o .json")
    source_group.add_argument("--stdin", action="store_true", help="Lee el transcript desde stdin")
    source_group.add_argument("--discover-local", action="store_true", help="Intenta descubrir transcripts locales")
    parser.add_argument("--title", help="Título de la conversación")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Raíz del repo donde se escribirá .ai_context")
    parser.add_argument("--docs-root", help="Ruta alternativa para docs/prompts")
    parser.add_argument(
        "--close-session",
        action="store_true",
        help="Marca el procesamiento como cierre de sesión para tu rutina operativa",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    effective_repo_root, effective_docs_root, policy = resolve_effective_roots(
        repo_root=args.repo_root,
        docs_root=args.docs_root,
        cwd=os.getcwd(),
    )
    source = _load_source(args, parser)
    close_session = args.close_session or policy is not None
    if close_session and "cierre de sesión" not in source.title.lower():
        source.title = f"{source.title} - cierre de sesión"
    session = build_session(source)
    outputs = persist_session(
        session,
        repo_root=effective_repo_root,
        docs_root=effective_docs_root,
        policy=policy,
    )
    compliance = assess_chat_memory_compliance(effective_repo_root) if policy is not None else None
    print(
        json.dumps(
            {
                "session_id": session.session_id,
                "title": session.title,
                "prompt_count": len(session.useful_prompts),
                "pending_tasks": session.pending_tasks,
                "policy_active": policy is not None,
                "close_session_enforced": close_session,
                "outputs": outputs,
                "compliance": compliance,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _load_source(args: argparse.Namespace, parser: argparse.ArgumentParser):
    if args.input_file:
        return load_conversation_from_file(args.input_file, title=args.title)
    if args.stdin:
        text = sys.stdin.read()
        if not text.strip():
            parser.error("No se recibió contenido por stdin")
        return load_conversation_from_text(text, title=args.title or "Conversación importada")
    discovered = discover_local_conversation(title=args.title, cwd=args.repo_root)
    if discovered is None:
        parser.error("No se encontró ningún transcript local; usa --input-file o --stdin")
    return discovered
