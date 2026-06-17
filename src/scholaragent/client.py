"""Semantic Scholar API client."""

from __future__ import annotations

import datetime
import os
import random
import time
from dataclasses import dataclass
from typing import Any

import requests
from requests_ratelimiter import LimiterAdapter

from scholaragent._endpoints import DEFAULT_FIELDS, ENDPOINTS_BY_NAME


@dataclass(frozen=True)
class RetryConfig:
    """Retry/backoff settings for courteous Semantic Scholar usage."""

    max_retries: int = 3
    initial_backoff_seconds: float = 5.0
    max_backoff_seconds: float = 120.0
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)
    jitter_fraction: float = 0.15


class SemanticScholarRateLimitError(requests.HTTPError):
    """Raised when Semantic Scholar still returns 429 after retries."""

    def __init__(self, response: requests.Response, retry_after: float | None = None):
        message = "Semantic Scholar rate limit exceeded"
        if retry_after is not None:
            message += f"; retry after approximately {retry_after:.0f} seconds"
        super().__init__(message, response=response)
        self.retry_after = retry_after


class SemanticScholarClient:
    """Thin, courteous client for the Semantic Scholar Academic Graph API.

    Defaults are intentionally conservative:

    - one request every two seconds (`requests_per_second=0.5`), below the public
      one-request-per-second guidance;
    - lean default fields to avoid over-fetching large citation/reference/embedding
      payloads;
    - exponential backoff that respects `Retry-After` when Semantic Scholar returns
      429 or transient 5xx responses.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    USER_AGENT = "ScholarAgent/0.1 (+https://github.com/Brandl/ScholarAgent)"

    def __init__(
        self,
        api_key: str | None = None,
        requests_per_second: float = 0.5,
        *,
        retry_config: RetryConfig | None = None,
        timeout: float = 30.0,
    ):
        self.retry_config = retry_config or RetryConfig()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self.session.mount(
            "https://",
            LimiterAdapter(per_second=requests_per_second, limit_statuses=[429, 500, 502, 503, 504]),
        )
        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    # ── retry/backoff helpers ────────────────────────────────────────

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            pass
        try:
            dt = datetime.datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            return max(0.0, (dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
        except ValueError:
            return None

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def _backoff_seconds(self, attempt: int, response: requests.Response) -> float:
        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
        if retry_after is not None:
            return min(retry_after, self.retry_config.max_backoff_seconds)
        base = min(
            self.retry_config.initial_backoff_seconds * (2 ** max(0, attempt - 1)),
            self.retry_config.max_backoff_seconds,
        )
        jitter = base * self.retry_config.jitter_fraction * random.random()
        return min(base + jitter, self.retry_config.max_backoff_seconds)

    def _get_with_retries(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        attempts = self.retry_config.max_retries + 1
        last_response: requests.Response | None = None
        for attempt in range(attempts):
            resp = self.session.get(url, params=params, timeout=self.timeout)
            last_response = resp
            if resp.status_code not in self.retry_config.retry_statuses:
                resp.raise_for_status()
                return resp
            if attempt >= self.retry_config.max_retries:
                if resp.status_code == 429:
                    raise SemanticScholarRateLimitError(
                        resp, retry_after=self._parse_retry_after(resp.headers.get("Retry-After"))
                    )
                resp.raise_for_status()
            self._sleep(self._backoff_seconds(attempt + 1, resp))
        assert last_response is not None  # defensive; loop always runs
        last_response.raise_for_status()
        return last_response

    # ── generic request ──────────────────────────────────────────────

    def request(self, endpoint_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a request for the named endpoint.

        Path parameters, query parameters, pagination, fields, and filters
        are all resolved from the endpoint registry.
        """
        ep = ENDPOINTS_BY_NAME[endpoint_name]
        path = ep.path.format(**{p: kwargs[p] for p in ep.path_params})

        params: dict[str, Any] = {}

        # fields: use lean defaults unless caller explicitly asks for more.
        fields = kwargs.get("fields")
        params["fields"] = fields if fields else DEFAULT_FIELDS[ep.field_category]

        # query params
        for qp in ep.query_params:
            val = kwargs.get(qp)
            if val is not None:
                params[qp] = val

        # pagination: small default page size; explicit limits are clamped to endpoint max.
        if ep.paginated:
            params["offset"] = kwargs.get("offset", 0)
            limit = kwargs.get("limit", ep.default_limit)
            params["limit"] = max(1, min(int(limit), ep.max_limit))

        # filters
        for f in ep.filters:
            val = kwargs.get(f)
            if val is not None:
                params[f] = val

        resp = self._get_with_retries(f"{self.BASE_URL}{path}", params=params)
        return resp.json()

    def check_status(self) -> dict[str, Any]:
        """Make one tiny request and report whether Semantic Scholar is reachable.

        This intentionally requests one result and only `paperId,title` fields.
        """
        try:
            data = self.search_papers("urban heat island", limit=1, fields="paperId,title")
        except SemanticScholarRateLimitError as exc:
            return {
                "ok": False,
                "status": "rate_limited",
                "status_code": exc.response.status_code if exc.response is not None else 429,
                "retry_after_seconds": exc.retry_after,
                "message": str(exc),
            }
        except requests.HTTPError as exc:
            return {
                "ok": False,
                "status": "http_error",
                "status_code": exc.response.status_code if exc.response is not None else None,
                "message": str(exc),
            }
        return {
            "ok": True,
            "status": "ok",
            "result_count": len(data.get("data", [])),
            "total": data.get("total"),
        }

    # ── convenience methods (thin wrappers for discoverability) ──────

    def get_paper(self, paper_id: str, *, fields: str | None = None) -> dict[str, Any]:
        return self.request("get_paper", paper_id=paper_id, fields=fields)

    def search_papers(
        self,
        query: str,
        *,
        offset: int = 0,
        limit: int = 10,
        fields: str | None = None,
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
        self, paper_id: str, *, offset: int = 0, limit: int = 100, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_authors", paper_id=paper_id, offset=offset, limit=limit, fields=fields,
        )

    def get_paper_citations(
        self, paper_id: str, *, offset: int = 0, limit: int = 100, fields: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_citations", paper_id=paper_id, offset=offset, limit=limit,
            fields=fields, **filters,
        )

    def get_paper_references(
        self, paper_id: str, *, offset: int = 0, limit: int = 100, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "get_paper_references", paper_id=paper_id, offset=offset, limit=limit, fields=fields,
        )

    def get_author(self, author_id: str, *, fields: str | None = None) -> dict[str, Any]:
        return self.request("get_author", author_id=author_id, fields=fields)

    def search_authors(
        self, query: str, *, offset: int = 0, limit: int = 10, fields: str | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "search_authors", query=query, offset=offset, limit=limit, fields=fields,
        )

    def get_author_papers(
        self, author_id: str, *, offset: int = 0, limit: int = 100, fields: str | None = None,
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
        resp = self.session.get(pdf_url, stream=True, timeout=self.timeout)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return path
