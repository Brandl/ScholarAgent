import responses

from scholaragent.client import SemanticScholarClient

BASE = SemanticScholarClient.BASE_URL


@responses.activate
def test_get_paper():
    responses.get(f"{BASE}/paper/abc123", json={"paperId": "abc123", "title": "Test"})
    client = SemanticScholarClient()
    result = client.get_paper("abc123")
    assert result["paperId"] == "abc123"


@responses.activate
def test_search_papers():
    responses.get(f"{BASE}/paper/search", json={"total": 1, "data": [{"paperId": "1"}]})
    client = SemanticScholarClient()
    result = client.search_papers("machine learning", year="2024")
    assert result["total"] == 1
    assert "year" in responses.calls[0].request.params


@responses.activate
def test_search_authors_passes_fields():
    """Regression: search_authors previously dropped the fields parameter."""
    responses.get(f"{BASE}/author/search", json={"total": 0, "data": []})
    client = SemanticScholarClient()
    client.search_authors("Hinton", fields="name,hIndex")
    assert responses.calls[0].request.params["fields"] == "name,hIndex"


@responses.activate
def test_get_paper_citations():
    responses.get(f"{BASE}/paper/abc/citations", json={"data": []})
    client = SemanticScholarClient()
    result = client.get_paper_citations("abc", limit=10)
    assert responses.calls[0].request.params["limit"] == "10"


@responses.activate
def test_api_key_header():
    responses.get(f"{BASE}/paper/x", json={})
    client = SemanticScholarClient(api_key="test-key")
    client.get_paper("x")
    assert responses.calls[0].request.headers["x-api-key"] == "test-key"
