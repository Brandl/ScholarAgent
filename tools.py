from langchain_core.tools import tool
from semanticscholar import SemanticScholar
import os
from typing import List

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
        papers_info = []
        for i, paper in enumerate(results[:limit]):
            authors = ', '.join([author.name for author in paper.authors]) if paper.authors else 'N/A'
            fields_of_study = ', '.join(paper.fieldsOfStudy) if paper.fieldsOfStudy else 'N/A'
            open_access_url = paper.openAccessPdf['url'] if paper.openAccessPdf else 'N/A'
            info = (
                f"Paper {i+1}:\n"
                f"ID: {paper.paperId}\n"
                f"Title: {paper.title}\n"
                f"Authors: {authors}\n"
                f"Abstract: {paper.abstract or 'N/A'}\n"
                f"Year: {paper.year or 'N/A'}\n"
                f"Venue: {paper.venue or 'N/A'}\n"
                f"Publication Types: {', '.join(paper.publicationTypes) if paper.publicationTypes else 'N/A'}\n"
                f"Fields of Study: {fields_of_study}\n"
                f"Citation Count: {paper.citationCount or 0}\n"
                f"Reference Count: {paper.referenceCount or 0}\n"
                f"Influential Citation Count: {paper.influentialCitationCount or 0}\n"
                f"Is Open Access: {'Yes' if paper.isOpenAccess else 'No'}\n"
                f"Open Access PDF: {open_access_url}\n"
                f"URL: {paper.url}\n"
                "---"
            )
            papers_info.append(info)
        return '\n'.join(papers_info)
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
        paper = sch.get_paper(paper_id, fields=fields)
        authors = ', '.join([author.name for author in paper.authors]) if paper.authors else 'N/A'
        fields_of_study = ', '.join(paper.fieldsOfStudy) if paper.fieldsOfStudy else 'N/A'
        open_access_url = paper.openAccessPdf['url'] if paper.openAccessPdf else 'N/A'
        info = (
            f"ID: {paper.paperId}\n"
            f"Title: {paper.title}\n"
            f"Authors: {authors}\n"
            f"Abstract: {paper.abstract or 'N/A'}\n"
            f"Year: {paper.year or 'N/A'}\n"
            f"Venue: {paper.venue or 'N/A'}\n"
            f"Publication Types: {', '.join(paper.publicationTypes) if paper.publicationTypes else 'N/A'}\n"
            f"Fields of Study: {fields_of_study}\n"
            f"Citation Count: {paper.citationCount or 0}\n"
            f"Reference Count: {paper.referenceCount or 0}\n"
            f"Influential Citation Count: {paper.influentialCitationCount or 0}\n"
            f"Is Open Access: {'Yes' if paper.isOpenAccess else 'No'}\n"
            f"Open Access PDF: {open_access_url}\n"
            f"URL: {paper.url}"
        )
        return info
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
        results = sch.get_paper_citations(paper_id, limit=limit)
        citations_info = []
        for i, citation in enumerate(results[:limit]):
            authors = ', '.join([author.name for author in citation.authors]) if citation.authors else 'N/A'
            fields_of_study = ', '.join(citation.fieldsOfStudy) if citation.fieldsOfStudy else 'N/A'
            info = (
                f"Citation {i+1}:\n"
                f"ID: {citation.paperId}\n"
                f"Title: {citation.title}\n"
                f"Authors: {authors}\n"
                f"Abstract: {citation.abstract or 'N/A'}\n"
                f"Year: {citation.year or 'N/A'}\n"
                f"Venue: {citation.venue or 'N/A'}\n"
                f"Fields of Study: {fields_of_study}\n"
                f"Citation Count: {citation.citationCount or 0}\n"
                f"Reference Count: {citation.referenceCount or 0}\n"
                f"Influential Citation Count: {citation.influentialCitationCount or 0}\n"
                f"URL: {citation.url}\n"
                "---"
            )
            citations_info.append(info)
        return '\n'.join(citations_info)
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
        results = sch.get_paper_references(paper_id, limit=limit)
        references_info = []
        for i, reference in enumerate(results[:limit]):
            authors = ', '.join([author.name for author in reference.authors]) if reference.authors else 'N/A'
            fields_of_study = ', '.join(reference.fieldsOfStudy) if reference.fieldsOfStudy else 'N/A'
            info = (
                f"Reference {i+1}:\n"
                f"ID: {reference.paperId}\n"
                f"Title: {reference.title}\n"
                f"Authors: {authors}\n"
                f"Abstract: {reference.abstract or 'N/A'}\n"
                f"Year: {reference.year or 'N/A'}\n"
                f"Venue: {reference.venue or 'N/A'}\n"
                f"Fields of Study: {fields_of_study}\n"
                f"Citation Count: {reference.citationCount or 0}\n"
                f"Reference Count: {reference.referenceCount or 0}\n"
                f"Influential Citation Count: {reference.influentialCitationCount or 0}\n"
                f"URL: {reference.url}\n"
                "---"
            )
            references_info.append(info)
        return '\n'.join(references_info)
    except Exception as e:
        return f"Error retrieving paper references: {str(e)}"

# Updated search_author tool with more complete output
@tool
def search_author(query: str, limit: int = 10) -> str:
    """
    Searches for authors based on a query string.

    Args:
        query: The search query string.
        limit: The maximum number of results to return (default 10).

    Returns:
        A string containing detailed information of the authors found.
    """
    sch = SemanticScholar(api_key=os.environ["S2_API_KEY"])
    try:
        results = sch.search_author(query, limit=limit)
        authors_info = []
        for i, author in enumerate(results[:limit]):
            affiliations = ', '.join(author.affiliations) if author.affiliations else 'N/A'
            info = (
                f"Author {i+1}:\n"
                f"ID: {author.authorId}\n"
                f"Name: {author.name}\n"
                f"Affiliations: {affiliations}\n"
                f"H-Index: {author.hIndex or 'N/A'}\n"
                f"Citation Count: {author.citationCount or 0}\n"
                f"Paper Count: {author.paperCount or 0}\n"
                f"URL: {author.url}\n"
                "---"
            )
            authors_info.append(info)
        return '\n'.join(authors_info)
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
        author = sch.get_author(author_id, fields=fields)
        affiliations = ', '.join(author.affiliations) if author.affiliations else 'N/A'
        info = (
            f"ID: {author.authorId}\n"
            f"Name: {author.name}\n"
            f"Affiliations: {affiliations}\n"
            f"H-Index: {author.hIndex or 'N/A'}\n"
            f"Citation Count: {author.citationCount or 0}\n"
            f"Paper Count: {author.paperCount or 0}\n"
            f"Homepage: {author.homepage or 'N/A'}\n"
            f"URL: {author.url}"
        )
        return info
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
        results = sch.get_author_papers(author_id, limit=limit)
        papers_info = []
        for i, paper in enumerate(results[:limit]):
            authors = ', '.join([author.name for author in paper.authors]) if paper.authors else 'N/A'
            fields_of_study = ', '.join(paper.fieldsOfStudy) if paper.fieldsOfStudy else 'N/A'
            open_access_url = paper.openAccessPdf['url'] if paper.openAccessPdf else 'N/A'
            info = (
                f"Paper {i+1}:\n"
                f"ID: {paper.paperId}\n"
                f"Title: {paper.title}\n"
                f"Authors: {authors}\n"
                f"Abstract: {paper.abstract or 'N/A'}\n"
                f"Year: {paper.year or 'N/A'}\n"
                f"Venue: {paper.venue or 'N/A'}\n"
                f"Publication Types: {', '.join(paper.publicationTypes) if paper.publicationTypes else 'N/A'}\n"
                f"Fields of Study: {fields_of_study}\n"
                f"Citation Count: {paper.citationCount or 0}\n"
                f"Reference Count: {paper.referenceCount or 0}\n"
                f"Influential Citation Count: {paper.influentialCitationCount or 0}\n"
                f"Is Open Access: {'Yes' if paper.isOpenAccess else 'No'}\n"
                f"Open Access PDF: {open_access_url}\n"
                f"URL: {paper.url}\n"
                "---"
            )
            papers_info.append(info)
        return '\n'.join(papers_info)
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
