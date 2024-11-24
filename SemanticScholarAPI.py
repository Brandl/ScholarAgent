import datetime
import os
import requests
from requests_ratelimiter import LimiterAdapter
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Initialize the API client
class SemanticScholarAPIClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        # Set rate limit to 1/second as per API policy
        self.session.mount('https://', LimiterAdapter(per_second=1, limit_statuses=[429, 500]))
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
        
        self.default_fields = {
            "paper": (
                "paperId,corpusId,externalIds,url,title,abstract,venue,publicationVenue,year,"
                "referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,"
                "fieldsOfStudy,s2FieldsOfStudy,publicationTypes,publicationDate,journal,citationStyles,"
                "authors,citations,references,embedding,tldr"
            ),
            "author": (
                "authorId,externalIds,url,name,affiliations,homepage,paperCount,citationCount,hIndex,papers"
            ),
            "reference": (
                "paperId,title,contexts,title,authors"
            ),
            "citation": (
                "paperId,title,contexts,title,authors"
            )
        }

    # Define methods for each API endpoint

    def get_paper(self, paper_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": fields or self.default_fields["paper"]}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_author(self, author_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/author/{author_id}"
        params = {"fields": fields or self.default_fields["author"]}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_papers(self, query: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None,
                      **filters) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "offset": offset,
            "limit": limit,
            "fields": fields or self.default_fields["paper"]
        }
        params.update(filters)
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_authors(self, query: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/author/search"
        params = {
            "query": query,
            "offset": offset,
            "limit": limit,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_paper_authors(self, paper_id: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/paper/{paper_id}/authors"
        params = {
            'offset': offset,
            'limit': limit,
            "fields": fields or self.default_fields["author"]
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_paper_citations(self, paper_id: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            'offset': offset,
            'limit': limit,
            "fields": fields or self.default_fields["citation"]
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_paper_references(self, paper_id: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/paper/{paper_id}/references"
        params = {
            'offset': offset,
            'limit': limit,
            "fields": fields or self.default_fields["reference"]
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_author_papers(self, author_id: str, offset: int = 0, limit: int = 100, fields: Optional[str] = None,
                          **filters) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/author/{author_id}/papers"
        params = {
            'offset': offset,
            'limit': limit, 
            "fields": fields or self.default_fields["paper"]
        }
        params.update(filters)
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_default_fields(self, endpoint: str) -> str:
        return self.default_fields[endpoint]

    # Add more methods as needed for other endpoints


# Instantiate the API client (replace 'your_api_key' with your actual API key)
api_client = SemanticScholarAPIClient(api_key=os.environ["S2_API_KEY"])


# Define Pydantic v2 models for tool input schemas
class GetPaperInput(BaseModel):
    paper_id: str = Field(..., description="The ID of the paper to fetch.")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("paper"))


class GetAuthorInput(BaseModel):
    author_id: str = Field(..., description="The ID of the author to fetch.")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("author"))


class SearchPapersInput(BaseModel):
    query: str = Field(..., description="The search query string.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of results to return (max 100).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("paper"))
    year: Optional[str] = Field(None, description="Year or range of years to filter by.")
    # Additional filters can be added as optional fields


class SearchAuthorsInput(BaseModel):
    query: str = Field(..., description="The search query string.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of results to return (max 100).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("author"))


class GetPaperAuthorsInput(BaseModel):
    paper_id: str = Field(..., description="The ID of the paper to fetch authors for.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of authors to return (max 1000).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("author"))


class GetPaperCitationsInput(BaseModel):
    paper_id: str = Field(..., description="The ID of the paper to fetch citations for.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of citations to return (max 1000).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("citation"))


class GetPaperReferencesInput(BaseModel):
    paper_id: str = Field(..., description="The ID of the paper to fetch references for.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of references to return (max 1000).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("reference"))


class GetAuthorPapersInput(BaseModel):
    author_id: str = Field(..., description="The ID of the author to fetch papers for.")
    offset: Optional[int] = Field(0, description="Result offset for pagination.")
    limit: Optional[int] = Field(100, description="Number of papers to return (max 100).")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to include. Defaults to all fields. Choose from: " + api_client.get_default_fields("paper"))
    # Additional filters can be added as optional fields


# Define tools using the @tool decorator
@tool(name_or_callable="get_paper", args_schema=GetPaperInput)
def get_paper_tool(paper_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
    """Fetch details about a paper given its ID."""
    response = api_client.get_paper(paper_id, fields=fields)
    return response


@tool(name_or_callable="get_author", args_schema=GetAuthorInput)
def get_author_tool(author_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
    """Fetch details about an author given their ID."""
    response = api_client.get_author(author_id, fields=fields)
    return response


@tool(name_or_callable="search_papers", args_schema=SearchPapersInput)
def search_papers_tool(
    query: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None,
    year: Optional[str] = None,
    **filters
) -> Dict[str, Any]:
    """Search for papers based on a query string."""
    response = api_client.search_papers(
        query=query,
        offset=offset,
        limit=limit,
        fields=fields,
        year=year,
        **filters
    )
    return response


@tool(name_or_callable="search_authors", args_schema=SearchAuthorsInput)
def search_authors_tool(
    query: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """Search for authors based on a query string."""
    response = api_client.search_authors(
        query=query,
        offset=offset,
        limit=limit,
        fields=fields
    )
    return response


@tool(name_or_callable="get_paper_authors", args_schema=GetPaperAuthorsInput)
def get_paper_authors_tool(
    paper_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch authors of a paper given its ID."""
    response = api_client.get_paper_authors(
        paper_id=paper_id,
        offset=offset,
        limit=limit,
        fields=fields
    )
    return response


@tool(name_or_callable="get_paper_citations", args_schema=GetPaperCitationsInput)
def get_paper_citations_tool(
    paper_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch citations of a paper given its ID."""
    response = api_client.get_paper_citations(
        paper_id=paper_id,
        offset=offset,
        limit=limit,
        fields=fields
    )
    return response


@tool(name_or_callable="get_paper_references", args_schema=GetPaperReferencesInput)
def get_paper_references_tool(
    paper_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch references of a paper given its ID."""
    response = api_client.get_paper_references(
        paper_id=paper_id,
        offset=offset,
        limit=limit,
        fields=fields
    )
    return response


@tool(name_or_callable="get_author_papers", args_schema=GetAuthorPapersInput)
def get_author_papers_tool(
    author_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    fields: Optional[str] = None,
    **filters
) -> Dict[str, Any]:
    """Fetch papers of an author given their ID."""
    response = api_client.get_author_papers(
        author_id=author_id,
        offset=offset,
        limit=limit,
        fields=fields,
        **filters
    )
    return response


def download_open_access_paper(url: str, base_folder: str = "downloads") -> str:
    """
    Downloads an open-access paper from the given URL and saves it into a unique subfolder.

    Args:
        url (str): The URL of the open-access paper to download.
        base_folder (str, optional): The base folder to save the downloads. Defaults to "downloads".

    Returns:
        str: The path to the downloaded file.
    """
    # Create a unique subfolder based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subfolder = os.path.join(base_folder, timestamp)
    os.makedirs(subfolder, exist_ok=True)

    # Get the filename from the URL
    filename = os.path.basename(url)
    if not filename or '.' not in filename:
        filename = "downloaded_paper.pdf"

    # Ensure the filename ends with .pdf
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    # Full path to save the file
    file_path = os.path.join(subfolder, filename)

    # Download the file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Write the content to the file in chunks
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded paper saved to {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the paper: {e}")
        return ""


@tool(name_or_callable="download_paper_tool", args_schema=GetPaperInput)
def download_paper_tool(paper_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
    """Fetch details about a paper given its ID."""
    response = api_client.get_paper(paper_id, fields=fields)
    # Extract the open-access PDF URL if available
    pdf_url = response.get('openAccessPdf', {}).get('url')
    if pdf_url:
        # Download the paper
        download_open_access_paper(pdf_url)
    return response


tool_list = [get_paper_tool, 
             get_author_tool, 
             search_papers_tool, 
             search_authors_tool, 
             get_paper_authors_tool, 
             get_paper_citations_tool, 
             get_paper_references_tool, 
             get_author_papers_tool,
             download_paper_tool]