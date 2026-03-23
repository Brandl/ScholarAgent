from scholaragent.client import SemanticScholarClient
from scholaragent.tools import create_tools


def test_creates_expected_tools():
    client = SemanticScholarClient()
    tools = create_tools(client)
    names = {t.name for t in tools}
    assert "get_paper" in names
    assert "search_papers" in names
    assert "search_authors" in names
    assert "get_paper_citations" in names
    assert "download_paper" in names


def test_tool_count():
    """One tool per endpoint + the download tool."""
    client = SemanticScholarClient()
    tools = create_tools(client)
    # 11 endpoints + 1 download tool = 12
    assert len(tools) == 12
