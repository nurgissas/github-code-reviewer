import os
import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from agent.tools import _fetch_repo_code, _search_similar_code

logger = logging.getLogger(__name__)


# Definition of agent state
class AgentState(TypedDict):
    pr_number: int
    pr_title: str
    pr_body: str
    repo_owner: str
    repo_name: str
    repo_code: str        # fetched code from GitHub
    relevant_code: str    # retrieved from pgvector (RAG)
    review: str           # final review from the LLM


def _make_llm() -> ChatOpenAI:
    """Create the review LLM (DeepSeek via the OpenAI-compatible API)."""
    return ChatOpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY", "not-set"),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )


# node 1 — fetch repository code from GitHub
def fetch_repo_node(state: AgentState) -> AgentState:
    logger.info(f"Fetching repo: {state['repo_owner']}/{state['repo_name']}")
    state["repo_code"] = _fetch_repo_code(
        owner=state["repo_owner"],
        repo=state["repo_name"],
    )
    return state


# node 2 — retrieve relevant code sections using RAG (pgvector)
async def retrieve_rel_code_node(state: AgentState) -> AgentState:
    logger.info(f"Searching for code similar to: {state['pr_title']}")
    query = f"{state['pr_title']} {state['pr_body']}".strip()
    repository = f"{state['repo_owner']}/{state['repo_name']}"
    state["relevant_code"] = await _search_similar_code(
        query=query, limit=5, repository=repository
    )
    return state


# node 3 — generate the review with the LLM
async def review_code(state: AgentState) -> AgentState:
    prompt = f"""You are a senior code reviewer. Review this GitHub pull request.

Title: {state['pr_title']}
Description: {state['pr_body'] or 'No description provided'}

Relevant code retrieved from the repository via RAG:
{state['relevant_code'] or 'No related code found in the index.'}

Provide a structured review with:
1. Key Observations
2. Suggestions for improvement
3. Approval status (Approved / Request Changes)
"""
    if not os.getenv("DEEPSEEK_API_KEY"):
        state["review"] = (
            "Review could not be generated: DEEPSEEK_API_KEY is not configured."
        )
        return state

    try:
        llm = _make_llm()
        message = await llm.ainvoke([{"role": "user", "content": prompt}])
        state["review"] = message.content or "No review content returned."
    except Exception as e:
        logger.error(f"LLM review failed: {e}")
        state["review"] = f"Review failed: {e}"
    return state


# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("fetch_repo", fetch_repo_node)
workflow.add_node("retrieve_code", retrieve_rel_code_node)
workflow.add_node("review", review_code)

workflow.set_entry_point("fetch_repo")
workflow.add_edge("fetch_repo", "retrieve_code")
workflow.add_edge("retrieve_code", "review")
workflow.add_edge("review", END)

agent = workflow.compile()


async def run_review_agent(pr_data: dict) -> str:
    """Execute the review agent with PR data from the webhook."""
    # Derive owner/repo. Prefer explicit fields; fall back to "owner/repo".
    owner = pr_data.get("owner")
    repo = pr_data.get("repo")
    if (not owner or not repo) and pr_data.get("repository") and "/" in pr_data["repository"]:
        owner, repo = pr_data["repository"].split("/", 1)

    initial_state = AgentState(
        pr_number=pr_data.get("prNumber", 0),
        pr_title=pr_data.get("title", ""),
        pr_body=pr_data.get("body") or "",
        repo_owner=owner or "",
        repo_name=repo or "",
        repo_code="",
        relevant_code="",
        review="",
    )

    result = await agent.ainvoke(initial_state)
    return result["review"]
