"""LangChain tool wrappers generated from the endpoint registry."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from scholaragent._endpoints import DEFAULT_FIELDS, ENDPOINTS, Endpoint
from scholaragent.client import SemanticScholarClient


def _build_schema(ep: Endpoint) -> type[BaseModel]:
    """Dynamically build a Pydantic input schema for an endpoint."""
    fields: dict[str, Any] = {}

    for p in ep.path_params:
        fields[p] = (str, Field(description=f"The {p.replace('_', ' ')}."))

    for qp in ep.query_params:
        if qp == "query":
            fields["query"] = (str, Field(description="The search query string."))
        elif qp == "token":
            fields["token"] = (
                Optional[str],
                Field(default=None, description="Continuation token for pagination."),
            )
        elif qp == "sort":
            fields["sort"] = (
                Optional[str],
                Field(default=None, description="Sort order (e.g. 'citationCount:desc')."),
            )

    if ep.paginated:
        fields["offset"] = (
            Optional[int],
            Field(default=0, description="Result offset for pagination."),
        )
        fields["limit"] = (
            Optional[int],
            Field(
                default=ep.default_limit,
                description=(
                    f"Number of results to return (default {ep.default_limit}, "
                    f"max {ep.max_limit}). Use small limits unless you truly need more."
                ),
            ),
        )

    available = DEFAULT_FIELDS[ep.field_category]
    fields["fields"] = (
        Optional[str],
        Field(
            default=None,
            description=f"Comma-separated list of fields to include. Choose from: {available}",
        ),
    )

    for f in ep.filters:
        fields[f] = (
            Optional[str],
            Field(default=None, description=f"Filter by {f}."),
        )

    return create_model(f"{ep.name}_input", **fields)


def create_tools(client: SemanticScholarClient) -> list[StructuredTool]:
    """Create LangChain tools for every registered endpoint."""
    tools: list[StructuredTool] = []

    for ep in ENDPOINTS:
        schema = _build_schema(ep)

        def _make_fn(endpoint: Endpoint):
            def fn(**kwargs: Any) -> dict[str, Any]:
                return client.request(endpoint.name, **kwargs)
            fn.__name__ = endpoint.name
            fn.__doc__ = endpoint.description
            return fn

        tools.append(
            StructuredTool.from_function(
                func=_make_fn(ep),
                name=ep.name,
                description=ep.description,
                args_schema=schema,
            )
        )

    # download tool (special case — wraps get_paper + PDF download)
    class DownloadPaperInput(BaseModel):
        paper_id: str = Field(description="The paper id.")
        base_folder: str = Field(default="downloads", description="Folder to save PDFs into.")

    def download_paper(paper_id: str, base_folder: str = "downloads") -> dict[str, Any]:
        """Download the open-access PDF for a paper, returning the paper details and local path."""
        path = client.download_open_access_paper(paper_id, base_folder=base_folder)
        paper = client.get_paper(paper_id)
        paper["_local_pdf_path"] = path
        return paper

    tools.append(
        StructuredTool.from_function(
            func=download_paper,
            name="download_paper",
            description="Download the open-access PDF for a paper if available.",
            args_schema=DownloadPaperInput,
        )
    )

    return tools
