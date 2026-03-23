"""CLI entry point for scholaragent."""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from scholaragent._endpoints import ENDPOINTS
from scholaragent.client import SemanticScholarClient


def _get_client() -> SemanticScholarClient:
    load_dotenv()
    api_key = os.environ.get("S2_API_KEY")
    if not api_key:
        print("Error: S2_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)
    return SemanticScholarClient(api_key=api_key)


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2))


# ── subcommand handlers ─────────────────────────────────────────────

def _cmd_api(args: argparse.Namespace) -> None:
    """Call any API endpoint by name."""
    client = _get_client()
    kwargs: dict = {}
    for pair in args.params:
        key, _, value = pair.partition("=")
        if not _:
            print(f"Error: params must be key=value, got '{pair}'", file=sys.stderr)
            sys.exit(1)
        # try to parse as int for offset/limit
        if value.isdigit():
            kwargs[key] = int(value)
        else:
            kwargs[key] = value
    if args.fields:
        kwargs["fields"] = args.fields
    _print_json(client.request(args.endpoint, **kwargs))


def _cmd_search(args: argparse.Namespace) -> None:
    """Search papers."""
    client = _get_client()
    kwargs: dict = dict(query=args.query, limit=args.limit)
    if args.year:
        kwargs["year"] = args.year
    if args.fields:
        kwargs["fields"] = args.fields
    _print_json(client.search_papers(**kwargs))


def _cmd_paper(args: argparse.Namespace) -> None:
    """Get a paper by ID."""
    client = _get_client()
    _print_json(client.get_paper(args.paper_id, fields=args.fields))


def _cmd_author(args: argparse.Namespace) -> None:
    """Get an author by ID."""
    client = _get_client()
    _print_json(client.get_author(args.author_id, fields=args.fields))


def _cmd_download(args: argparse.Namespace) -> None:
    """Download open-access PDF."""
    client = _get_client()
    path = client.download_open_access_paper(args.paper_id, base_folder=args.output)
    if path:
        print(path)
    else:
        print("No open-access PDF available for this paper.", file=sys.stderr)
        sys.exit(1)


def _cmd_agent(args: argparse.Namespace) -> None:
    """Run the research agent."""
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)

    # lazy import — agent deps (langgraph, langchain-openai) are heavy
    from scholaragent.agent import SYSTEM_PROMPT, build_agent, run_agent

    client = _get_client()
    graph = build_agent(client, model=args.model, temperature=args.temperature)

    year_clause = f" Focus on papers published in {args.years}." if args.years else ""
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Make a plan on how to research the topic '{args.topic}' and execute the plan.{year_clause} "
        f"If you find a relevant paper, also look at its references and citations. "
        f"After you have gathered enough information, provide a summary of the research "
        f"and the most relevant papers."
    )
    run_agent(graph, prompt)


def _cmd_endpoints(args: argparse.Namespace) -> None:
    """List available API endpoints."""
    for ep in ENDPOINTS:
        params = ", ".join(
            [*ep.path_params, *ep.query_params]
            + (["offset", "limit"] if ep.paginated else [])
            + list(ep.filters)
        )
        print(f"  {ep.name:<25} {ep.description}")
        if params:
            print(f"  {'':25} params: {params}")


# ── main parser ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="scholaragent",
        description="Semantic Scholar API client & research agent",
    )
    sub = parser.add_subparsers(dest="command")

    # scholaragent search <query>
    p_search = sub.add_parser("search", help="Search for papers")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    p_search.add_argument("--year", help="Year or range, e.g. '2023-2024'")
    p_search.add_argument("--fields", help="Comma-separated fields to return")

    # scholaragent paper <id>
    p_paper = sub.add_parser("paper", help="Get paper details")
    p_paper.add_argument("paper_id", help="Paper ID (S2 ID, DOI, ArXiv ID, etc.)")
    p_paper.add_argument("--fields", help="Comma-separated fields to return")

    # scholaragent author <id>
    p_author = sub.add_parser("author", help="Get author details")
    p_author.add_argument("author_id", help="Author ID")
    p_author.add_argument("--fields", help="Comma-separated fields to return")

    # scholaragent download <id>
    p_dl = sub.add_parser("download", help="Download open-access PDF")
    p_dl.add_argument("paper_id", help="Paper ID")
    p_dl.add_argument("-o", "--output", default="downloads", help="Output folder (default: downloads)")

    # scholaragent api <endpoint> [key=value ...]
    p_api = sub.add_parser("api", help="Call any API endpoint by name")
    p_api.add_argument("endpoint", help="Endpoint name (use 'endpoints' to list)")
    p_api.add_argument("params", nargs="*", help="Parameters as key=value pairs")
    p_api.add_argument("--fields", help="Comma-separated fields to return")

    # scholaragent agent <topic>
    p_agent = sub.add_parser("agent", help="Run the LLM research agent")
    p_agent.add_argument("topic", help="Research topic")
    p_agent.add_argument("--model", default="gpt-4o", help="LLM model (default: gpt-4o)")
    p_agent.add_argument("--years", help="Year range, e.g. '2023-2024'")
    p_agent.add_argument("--temperature", type=float, default=0, help="LLM temperature (default: 0)")

    # scholaragent endpoints
    sub.add_parser("endpoints", help="List all available API endpoints")

    args = parser.parse_args()

    handlers = {
        "search": _cmd_search,
        "paper": _cmd_paper,
        "author": _cmd_author,
        "download": _cmd_download,
        "api": _cmd_api,
        "agent": _cmd_agent,
        "endpoints": _cmd_endpoints,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
