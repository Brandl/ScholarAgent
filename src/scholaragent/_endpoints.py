"""
Endpoint registry — single source of truth for all Semantic Scholar API endpoints.

Each endpoint is described as data. The client, tools, and Pydantic schemas
are all derived from this registry, eliminating boilerplate.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str
    description: str
    field_category: str  # key into DEFAULT_FIELDS
    path_params: tuple[str, ...] = ()
    query_params: tuple[str, ...] = ()
    paginated: bool = False
    max_limit: int = 100
    filters: tuple[str, ...] = ()


# Default field sets requested from the API.
DEFAULT_FIELDS: dict[str, str] = {
    "paper": (
        "paperId,corpusId,externalIds,url,title,abstract,venue,publicationVenue,year,"
        "referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,"
        "fieldsOfStudy,s2FieldsOfStudy,publicationTypes,publicationDate,journal,"
        "citationStyles,authors,citations,references,embedding,tldr"
    ),
    "author": (
        "authorId,externalIds,url,name,affiliations,homepage,paperCount,citationCount,hIndex,papers"
    ),
    "citation": "paperId,title,contexts,authors",
    "reference": "paperId,title,contexts,authors",
}


ENDPOINTS: tuple[Endpoint, ...] = (
    # ── Paper endpoints ──────────────────────────────────────────────
    Endpoint(
        name="get_paper",
        path="/paper/{paper_id}",
        description="Fetch details about a single paper by its ID.",
        field_category="paper",
        path_params=("paper_id",),
    ),
    Endpoint(
        name="search_papers",
        path="/paper/search",
        description="Search for papers matching a query string.",
        field_category="paper",
        query_params=("query",),
        paginated=True,
        filters=(
            "year",
            "publicationDateOrYear",
            "venue",
            "fieldsOfStudy",
            "publicationTypes",
            "openAccessPdf",
            "minCitationCount",
        ),
    ),
    Endpoint(
        name="search_papers_bulk",
        path="/paper/search/bulk",
        description="Bulk search for papers. Returns up to 10M results via token-based pagination.",
        field_category="paper",
        query_params=("query", "token", "sort"),
        filters=(
            "year",
            "publicationDateOrYear",
            "venue",
            "fieldsOfStudy",
            "publicationTypes",
            "openAccessPdf",
            "minCitationCount",
        ),
    ),
    Endpoint(
        name="match_paper",
        path="/paper/search/match",
        description="Find the paper that best matches a given title query.",
        field_category="paper",
        query_params=("query",),
        filters=(
            "year",
            "publicationDateOrYear",
            "venue",
            "fieldsOfStudy",
            "publicationTypes",
            "openAccessPdf",
            "minCitationCount",
        ),
    ),
    Endpoint(
        name="autocomplete_paper",
        path="/paper/autocomplete",
        description="Autocomplete paper titles from a partial query string.",
        field_category="paper",
        query_params=("query",),
    ),
    Endpoint(
        name="get_paper_authors",
        path="/paper/{paper_id}/authors",
        description="Get the authors of a paper.",
        field_category="author",
        path_params=("paper_id",),
        paginated=True,
        max_limit=1000,
    ),
    Endpoint(
        name="get_paper_citations",
        path="/paper/{paper_id}/citations",
        description="Get papers that cite the given paper.",
        field_category="citation",
        path_params=("paper_id",),
        paginated=True,
        max_limit=1000,
        filters=("publicationDateOrYear",),
    ),
    Endpoint(
        name="get_paper_references",
        path="/paper/{paper_id}/references",
        description="Get papers referenced by the given paper.",
        field_category="reference",
        path_params=("paper_id",),
        paginated=True,
        max_limit=1000,
    ),
    # ── Author endpoints ─────────────────────────────────────────────
    Endpoint(
        name="get_author",
        path="/author/{author_id}",
        description="Fetch details about a single author by their ID.",
        field_category="author",
        path_params=("author_id",),
    ),
    Endpoint(
        name="search_authors",
        path="/author/search",
        description="Search for authors matching a query string.",
        field_category="author",
        query_params=("query",),
        paginated=True,
        max_limit=1000,
    ),
    Endpoint(
        name="get_author_papers",
        path="/author/{author_id}/papers",
        description="Get papers written by the given author.",
        field_category="paper",
        path_params=("author_id",),
        paginated=True,
        max_limit=1000,
        filters=("publicationDateOrYear",),
    ),
)

ENDPOINTS_BY_NAME: dict[str, Endpoint] = {ep.name: ep for ep in ENDPOINTS}
