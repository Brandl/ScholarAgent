"""Semantic Scholar API client."""

from __future__ import annotations

import datetime
import os
from typing import Any

import requests
from requests_ratelimiter import LimiterAdapter

from scholaragent._endpoints import DEFAULT_FIELDS, ENDPOINTS_BY_NAME


class SemanticScholarClient:
    """Thin, rate-limited client for the Semantic Scholar Academic Graph API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str | None = None, requests_per_second: int = 1):
        self.session = requests.Session()
        self.session.mount(
            "https://",
            LimiterAdapter(per_second=requests_per_second, limit_statuses=[429, 500]),
        )
        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    # ── generic request ──────────────────────────────────────────────

    def request(self, endpoint_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a request for the named endpoint.

        Path parameters, query parameters, pagination, fields, and filters
        are all resolved from the endpoint registry.
        """
        ep = ENDPOINTS_BY_NAME[endpoint_name]
        path = ep.path.format(**{p: kwargs[p] for p in ep.path_params})

        params: dict[str, Any] = {}

        # fields
        fields = kwargs.get("fields")
        params["fields"] = fields if fields else DEFAULT_FIELDS[ep.field_category]

        # query params
        for qp in ep.query_params:
            val = kwargs.get(qp)
            if val is not None:
                params[qp] = val

        # pagination
        if ep.paginated:
            params["offset"] = kwargs.get("offset", 0)
            params["limit"] = kwargs.get("limit", ep.max_limit)

        # filters
        for f in ep.filters:
            val = kwargs.get(f)
            if val is not None:
                params[f] = val

        resp = self.session.get(f"{self.BASE_URL}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    # ── convenience methods (thin wrappers for discoverability) ──────

    def get_paper(self, paper_id: str, *, fields: str | None = None) -> dict[str, Any]:
        return self.request("get_paper", paper_id=paper_id, fields=fields)

    def search_papers(
        self, query: str, *, offset: int = 0, limit: int = 100, fields: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        return self.request(
            "search_papers", query=query, offset=offset, limit=limit, fields=fields, **filters,
        )

    def search_papers_bulk(
        self, query: str, *, token: str | None = None, sort: str | None = None,
        fields: str | None = None, **filters: Any,
    ) -> dict[str, Any]:
        return self.request(
            "search_papers_bulk", query=query, token=token, sort=sort, fields=fields, **filters,
        )

    def match_paper(self, query: str, *, fields: str | None = None, **filters: Any) -> dict[str, Any]:
        return self.request("match_paper", query=query, fields=fields, **filters)

    def autocomplete_paper(self, query: str, *, fields: str | None = None) -> dict[str, Any]:
        return self.request("autocomplete_paper", query=query, fields=fields)

    def get_paper_authors(
        self, paper_id: str, *, offset: int = 0, limit: int = 1000, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_authors", paper_id=paper_id, offset=offset, limit=limit, fields=fields,
        )

    def get_paper_citations(
        self, paper_id: str, *, offset: int = 0, limit: int = 1000, fields: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_citations", paper_id=paper_id, offset=offset, limit=limit,
            fields=fields, **filters,
        )

    def get_paper_references(
        self, paper_id: str, *, offset: int = 0, limit: int = 1000, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_references", paper_id=paper_id, offset=offset, limit=limit, fields=fields,
        )

    def get_author(self, author_id: str, *, fields: str | None = None) -> dict[str, Any]:
        return self.request("get_author", author_id=author_id, fields=fields)

    def search_authors(
        self, query: str, *, offset: int = 0, limit: int = 1000, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "search_authors", query=query, offset=offset, limit=limit, fields=fields,
        )

    def get_author_papers(
        self, author_id: str, *, offset: int = 0, limit: int = 1000, fields: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        return self.request(
            "get_author_papers", author_id=author_id, offset=offset, limit=limit,
            fields=fields, **filters,
        )

    # ── download helper ──────────────────────────────────────────────

    def download_open_access_paper(
        self, paper_id: str, base_folder: str = "downloads",
    ) -> str | None:
        """Download the open-access PDF for a paper, if available.

        Returns the local file path on success, or None if no PDF is available.
        """
        paper = self.get_paper(paper_id, fields="openAccessPdf")
        pdf_url = (paper.get("openAccessPdf") or {}).get("url")
        if not pdf_url:
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = os.path.join(base_folder, timestamp)
        os.makedirs(folder, exist_ok=True)

        filename = os.path.basename(pdf_url)
        if not filename or "." not in filename:
            filename = "paper.pdf"
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        path = os.path.join(folder, filename)
        resp = self.session.get(pdf_url, stream=True)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return path
