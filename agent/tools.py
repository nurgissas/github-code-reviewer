import os
import json
import logging

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings

from agent.db import db_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plain (non-tool) helpers — used directly by the LangGraph nodes.
# These are also wrapped as LangChain tools below so the LLM can call them.
# ---------------------------------------------------------------------------
def _fetch_repo_code(owner: str, repo: str, ref: str = "main") -> str:
    """Fetch repository code structure and key files as a JSON string."""
    try:
        from agent.github_client import github_client

        logger.info(f"Fetching repo {owner}/{repo} from GitHub")
        result = github_client.fetch_repository_files(owner, repo, ref)

        if result:
            logger.info(f"Successfully fetched {len(result.get('files', []))} files")
            return json.dumps(result)

        logger.warning("GitHub fetch returned no data")
    except Exception as e:
        logger.error(f"Failed to fetch repo {owner}/{repo}: {e}")

    # Fallback so the pipeline keeps running even without GitHub access.
    return json.dumps({
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "files": [],
        "content": {},
        "error": "Could not fetch repository files",
    })


async def _search_similar_code(query: str, limit: int = 5, repository: str = "default") -> str:
    """Search the pgvector store for code similar to the query. Returns JSON string."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — skipping semantic search")
        return json.dumps([])

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
        query_embedding = await embeddings.aembed_query(query)

        results = await db_manager.search_similar_code(
            query_embedding=query_embedding,
            repository=repository or "default",
            limit=limit,
        )
        return json.dumps(results)
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return json.dumps([])


async def _generate_embedding(text: str) -> str:
    """Generate an embedding vector for the given text. Returns JSON string."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return json.dumps({"embedding": [], "error": "OPENAI_API_KEY not set", "success": False})

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
        vector = await embeddings.aembed_query(text)
        return json.dumps({"embedding": vector, "dimension": len(vector), "success": True})
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return json.dumps({"embedding": [], "error": str(e), "success": False})


# ---------------------------------------------------------------------------
# LangChain tool wrappers (so the LLM can invoke them if bound to the model).
# ---------------------------------------------------------------------------
@tool("fetch_repo_code")
def fetch_repo_code(owner: str, repo: str, ref: str = "main") -> str:
    """Fetch repository code structure and key files from GitHub.

    Args:
        owner: GitHub username (e.g. "nurgissas").
        repo: Repository name (e.g. "github-code-reviewer").
        ref: Branch name (default: "main").

    Returns:
        JSON string with files, contents and repo metadata.
    """
    return _fetch_repo_code(owner, repo, ref)


@tool("search_similar_code")
async def search_similar_code(query: str, limit: int = 5, repository: str = "default") -> str:
    """Search the pgvector database for code sections similar to a query (RAG).

    Args:
        query: Natural-language search query.
        limit: Number of results to return.
        repository: Restrict the search to a single repository.

    Returns:
        JSON string: list of {file, snippet, similarity}.
    """
    return await _search_similar_code(query, limit, repository)


@tool("generate_embedding")
async def generate_embedding(text: str) -> str:
    """Generate a 1536-dimensional embedding vector for the given text.

    Returns:
        JSON string with the embedding vector and its dimension.
    """
    return await _generate_embedding(text)


# Export tools as a list for llm.bind_tools(...)
tools = [fetch_repo_code, search_similar_code, generate_embedding]
