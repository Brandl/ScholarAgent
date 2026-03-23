# ScholarAgent

A Python library and CLI for the [Semantic Scholar Academic Graph API](https://api.semanticscholar.org/), with an optional LLM-powered research agent built on [LangGraph](https://github.com/langchain-ai/langgraph).

ScholarAgent provides three layers you can use independently:

1. **`SemanticScholarClient`** — a rate-limited Python client for the full Semantic Scholar API
2. **CLI** — search papers, fetch metadata, and download PDFs from your terminal
3. **Research Agent** — an LLM agent that autonomously searches, reads citations, and summarizes literature

---

## Installation

Requires Python 3.11+.

```bash
# with uv (recommended)
uv add scholaragent

# from source
git clone https://github.com/Brandl/ScholarAgent.git
cd ScholarAgent
uv sync
```

For development (includes pytest, responses, ruff):

```bash
uv sync --extra dev
```

## Configuration

ScholarAgent needs a [Semantic Scholar API key](https://www.semanticscholar.org/product/api). The research agent additionally needs an OpenAI API key.

Create a `.env` file in your project root (see `.env.example`):

```
S2_API_KEY=your_semantic_scholar_api_key
OPENAI_API_KEY=your_openai_api_key
```

Or export them directly:

```bash
export S2_API_KEY=your_semantic_scholar_api_key
export OPENAI_API_KEY=your_openai_api_key  # only needed for the agent
```

## Rate Limiting

The Semantic Scholar API enforces a rate limit of **1 request per second**, cumulative across all endpoints. ScholarAgent respects this automatically — every request goes through a shared rate-limited session. If the API returns `429` (rate limited) or `500` (server error), the client backs off and retries.

You can adjust the rate when constructing the client:

```python
client = SemanticScholarClient(api_key="...", requests_per_second=1)  # default
```

---

## Python Library

### Quick Start

```python
from scholaragent import SemanticScholarClient

client = SemanticScholarClient(api_key="your_key")

# Search for papers
results = client.search_papers("transformers attention mechanism", year="2023-2024", limit=5)
for paper in results["data"]:
    print(f"{paper['title']} ({paper['year']}) — {paper['citationCount']} citations")

# Get a specific paper by DOI, ArXiv ID, or Semantic Scholar ID
paper = client.get_paper("DOI:10.18653/v1/2023.acl-long.1")

# Get an author
author = client.get_author("1741101")
print(f"{author['name']} — h-index: {author['hIndex']}")
```

### Client Methods

All methods accept an optional `fields` parameter to control which fields are returned. When omitted, a sensible set of defaults is used.

#### Paper Endpoints

```python
# Search with filters
client.search_papers(
    "neural networks",
    year="2024",
    venue="NeurIPS,ICML",
    fieldsOfStudy="Computer Science",
    minCitationCount="10",
    limit=50,
)

# Bulk search (token-based pagination, up to 10M results)
batch = client.search_papers_bulk("deep learning", sort="citationCount:desc")
next_batch = client.search_papers_bulk("deep learning", token=batch["token"])

# Find best title match
client.match_paper("Attention Is All You Need")

# Autocomplete
client.autocomplete_paper("attention is all")

# Paper details
client.get_paper("649def34f8be52c8b66281af98ae884c09aef38b")
client.get_paper("DOI:10.1234/example")
client.get_paper("ArXiv:2301.00001")
client.get_paper("CorpusID:12345")

# Paper relationships
client.get_paper_authors("649def34f8be52c8b66281af98ae884c09aef38b")
client.get_paper_citations("649def34f8be52c8b66281af98ae884c09aef38b", limit=100)
client.get_paper_references("649def34f8be52c8b66281af98ae884c09aef38b")
```

#### Author Endpoints

```python
client.search_authors("Geoffrey Hinton")
client.get_author("1741101")
client.get_author_papers("1741101", publicationDateOrYear="2023-2024")
```

#### Download Open-Access PDFs

```python
path = client.download_open_access_paper("649def34f8be52c8b66281af98ae884c09aef38b")
if path:
    print(f"Saved to {path}")
else:
    print("No open-access PDF available")
```

### Generic Request Interface

Every endpoint is registered in an internal registry. You can call any endpoint by name using `client.request()`:

```python
client.request("search_papers", query="LLM agents", year="2024", limit=5)
client.request("get_paper_citations", paper_id="abc123", limit=10)
```

This is what the CLI's `api` subcommand uses under the hood.

### Selecting Fields

By default, the client requests a comprehensive set of fields for each endpoint category. You can override this to reduce payload size and improve response times:

```python
# Only get title and citation count
client.search_papers("transformers", fields="title,citationCount", limit=10)

# Paper fields: paperId, corpusId, externalIds, url, title, abstract, venue,
#   publicationVenue, year, referenceCount, citationCount, influentialCitationCount,
#   isOpenAccess, openAccessPdf, fieldsOfStudy, s2FieldsOfStudy, publicationTypes,
#   publicationDate, journal, citationStyles, authors, citations, references,
#   embedding, tldr

# Author fields: authorId, externalIds, url, name, affiliations, homepage,
#   paperCount, citationCount, hIndex, papers
```

---

## CLI

The `scholaragent` command provides direct access to the API from your terminal. All output is JSON, so it works well with `jq`.

### Search Papers

```bash
scholaragent search "machine learning" -n 5
scholaragent search "transformer architectures" --year 2023-2024 --fields "title,year,citationCount"
scholaragent search "LLM agents" -n 20 | jq '.data[].title'
```

### Get Paper Details

```bash
scholaragent paper 649def34f8be52c8b66281af98ae884c09aef38b
scholaragent paper "DOI:10.18653/v1/2023.acl-long.1" --fields "title,abstract,authors"
scholaragent paper "ArXiv:2301.00001"
```

### Get Author Details

```bash
scholaragent author 1741101
scholaragent author 1741101 --fields "name,hIndex,paperCount"
```

### Download Open-Access PDFs

```bash
scholaragent download 649def34f8be52c8b66281af98ae884c09aef38b
scholaragent download "DOI:10.18653/v1/2023.acl-long.1" -o ./papers
```

### Generic API Access

Call any endpoint by name with arbitrary key=value parameters. Use `scholaragent endpoints` to see all available endpoints.

```bash
# List all endpoints and their parameters
scholaragent endpoints

# Call any endpoint directly
scholaragent api search_papers query="neural networks" limit=5 year=2024
scholaragent api get_paper_citations paper_id=abc123 limit=10
scholaragent api get_author_papers author_id=1741101 publicationDateOrYear=2024
scholaragent api search_papers_bulk query="transformers" sort="citationCount:desc"
scholaragent api match_paper query="Attention Is All You Need"
```

### Run the Research Agent

The agent requires an `OPENAI_API_KEY` in addition to `S2_API_KEY`.

```bash
scholaragent agent "machine learning in cyber security" --years 2023-2024
scholaragent agent "protein folding" --model gpt-4o --temperature 0.2
```

---

## LangChain / LangGraph Integration

ScholarAgent generates LangChain-compatible tools from the endpoint registry, ready to plug into any LangChain or LangGraph agent.

### Using the Tools Directly

```python
from scholaragent import SemanticScholarClient, create_tools

client = SemanticScholarClient(api_key="your_key")
tools = create_tools(client)

# tools is a list of StructuredTool instances
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

### Using the Built-in Agent

```python
from scholaragent import SemanticScholarClient, build_agent, run_agent

client = SemanticScholarClient(api_key="your_s2_key")
graph = build_agent(client, model="gpt-4o", temperature=0)

run_agent(graph, "Find recent papers on retrieval-augmented generation")
```

### Custom Agent

Use `create_tools()` with your own LangGraph or LangChain setup:

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from scholaragent import SemanticScholarClient, create_tools

client = SemanticScholarClient(api_key="your_s2_key")
tools = create_tools(client)

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(llm, tools)

for event in agent.stream({"messages": [("user", "Find papers on quantum computing from 2024")]}):
    # handle events
    ...
```

---

## Available Endpoints

| Endpoint | Description | Key Parameters |
|---|---|---|
| `get_paper` | Get paper by ID | `paper_id` |
| `search_papers` | Search papers | `query`, `year`, `venue`, `fieldsOfStudy`, `minCitationCount` |
| `search_papers_bulk` | Bulk search with token pagination | `query`, `token`, `sort` |
| `match_paper` | Find best title match | `query` |
| `autocomplete_paper` | Autocomplete titles | `query` |
| `get_paper_authors` | Get paper's authors | `paper_id` |
| `get_paper_citations` | Get citing papers | `paper_id`, `publicationDateOrYear` |
| `get_paper_references` | Get referenced papers | `paper_id` |
| `get_author` | Get author by ID | `author_id` |
| `search_authors` | Search authors | `query` |
| `get_author_papers` | Get author's papers | `author_id`, `publicationDateOrYear` |

Paginated endpoints also accept `offset` and `limit`. All endpoints accept `fields`.

---

## Project Structure

```
src/scholaragent/
    __init__.py         Public API exports
    _endpoints.py       Endpoint registry (single source of truth)
    client.py           Rate-limited API client
    tools.py            LangChain tool generation
    agent.py            LangGraph research agent
    cli.py              CLI entry point
tests/
    test_client.py      HTTP-mocked client tests
    test_endpoints.py   Registry integrity tests
    test_tools.py       Tool generation tests
```

The endpoint registry in `_endpoints.py` is the single source of truth. The client methods, LangChain tools, Pydantic schemas, and CLI are all derived from it. To add a new endpoint, add one entry to the registry — everything else is generated automatically.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linter
uv run ruff check src/ tests/

# Run a specific test
uv run pytest tests/test_client.py::test_search_papers -v
```

## License

MIT
