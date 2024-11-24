from langchain_core.tools import tool
from semanticscholar import SemanticScholar
import os
from typing import List
from pyrate_limiter import Duration, Rate, Limiter

# Create rate limiters
search_limiter = Limiter(Rate(1, Duration.SECOND*2), max_delay=30000)  # 1 request per second, wait 30 seconds if rate limit is exceeded
get_limiter = Limiter(Rate(5, Duration.SECOND), max_delay=30000)     # 5 requests per second, wait 30 seconds if rate limit is exceeded

# Updated search_paper tool with more complete output
@tool
def search_paper(
    query: str,
    limit: int = 10,
    year: str = None,
    publication_types: List[str] = None,
    open_access_pdf: bool = None,
    venue: List[str] = None,
    fields_of_study: List[str] = None,
    min_citation_count: int = None,
    sort: str = None,
    #match_title: bool = False
) -> str:
    """
    Searches for papers based on a query string.

    Args:
        query: The search query string.
        limit: The maximum number of results to return (default 10).
        year: Restrict results to a specific publication year or range (optional).
        publication_types: Restrict results to the given publication type list (optional).
        open_access_pdf: Restrict results to papers with public PDFs (optional).
        venue: Restrict results to the given venue list (optional).
        fields_of_study: Restrict results to given field-of-study list (optional).
        min_citation_count: Restrict results to papers with at least the given number of citations (optional).
        sort: Sort results using "<field>:<order>" format, where "field" is either paperId, publicationDate, or citationCount, and "order" is asc (ascending) or desc (descending) (optional).
        match_title: Retrieve a single paper whose title best matches the given query (optional).
    
    Returns:
        A string containing detailed information of the papers found.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        search_limiter.try_acquire("search")
        results = sch.search_paper(
            query,
            year=year,
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            venue=venue,
            fields_of_study=fields_of_study,
            min_citation_count=min_citation_count,
            limit=limit,
            sort=sort,
            #match_title=match_title
        )
        return results.items
    except Exception as e:
        return f"Error searching for papers: {str(e)}"

# Updated get_paper tool with more complete output
@tool
def get_paper(paper_id: str, fields: List[str] = None) -> str:
    """
    Retrieves detailed information about a specific paper using its ID.

    Args:
        paper_id: The ID of the paper (DOI, Corpus ID, etc.).
        fields: List of fields to retrieve (optional).

    Returns:
        A string containing the paper's detailed information.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        get_limiter.try_acquire("get")
        paper = sch.get_paper(paper_id, fields=fields)
        return paper
    except Exception as e:
        return f"Error retrieving paper: {str(e)}"

# Updated get_paper_citations tool with more complete output
@tool
def get_paper_citations(paper_id: str, limit: int = 10) -> str:
    """
    Retrieves citations of a specific paper.

    Args:
        paper_id: The ID of the paper (DOI, Corpus ID, etc.).
        limit: The maximum number of citations to return (default 10).

    Returns:
        A string containing detailed information of the citations.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        get_limiter.try_acquire("get")
        results = sch.get_paper_citations(paper_id, limit=limit)
        return results.items
    except Exception as e:
        return f"Error retrieving paper citations: {str(e)}"

# Updated get_paper_references tool with more complete output
@tool
def get_paper_references(paper_id: str, limit: int = 10) -> str:
    """
    Retrieves references of a specific paper.

    Args:
        paper_id: The ID of the paper (DOI, Corpus ID, etc.).
        limit: The maximum number of references to return (default 10).

    Returns:
        A string containing detailed information of the references.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        get_limiter.try_acquire("get")
        results = sch.get_paper_references(paper_id, limit=limit)
        return results.items
    except Exception as e:
        return f"Error retrieving paper references: {str(e)}"

# Updated search_author tool with more complete output
@tool
def search_author(query: str, limit: int = 10) -> str:
    """
    Searches for authors by their name

    Args:
        query: The search query string, eg. author name.
        limit: The maximum number of results to return (default 10).

    Returns:
        A string containing detailed information of the authors found.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        search_limiter.try_acquire("search")
        results = sch.search_author(query, limit=limit)
        return results.items
    except Exception as e:
        return f"Error searching for authors: {str(e)}"

# Updated get_author tool with more complete output
@tool
def get_author(author_id: str, fields: List[str] = None) -> str:
    """
    Retrieves detailed information about a specific author using their ID.

    Args:
        author_id: The ID of the author.
        fields: List of fields to retrieve (optional).

    Returns:
        A string containing the author's detailed information.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        get_limiter.try_acquire("get")
        author = sch.get_author(author_id, fields=fields)
        return author
    except Exception as e:
        return f"Error retrieving author: {str(e)}"

# Updated get_author_papers tool with more complete output
@tool
def get_author_papers(author_id: str, limit: int = 10) -> str:
    """
    Retrieves papers of a specific author.

    Args:
        author_id: The ID of the author.
        limit: The maximum number of papers to return (default 10).

    Returns:
        A string containing detailed information of the author's papers.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        get_limiter.try_acquire("get")
        results = sch.get_author_papers(author_id, limit=limit)
        return results.items
    except Exception as e:
        return f"Error retrieving author's papers: {str(e)}"

# List of tools
tool_list = [
    search_paper,
    get_paper,
    get_paper_citations,
    get_paper_references,
    search_author,
    get_author,
    get_author_papers
]
