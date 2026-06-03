from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langgraph_openai import GhatOpenAI
from agent.tools import tools
import json
import os

# Definition of agent state
class AgentState(TypedDict):
  pr_number: int
  pr_title: str
  pr_body: str
  repo_owner: str
  repo_name: str
  repo_code: str # fetched code from github
  relevant_code: str # retrieved from pgvector
  review: str # final review from external AI

# initialize llm
llm = ChatOpenAI(
  api_key = os.getenv("DEEPSEEK_API_KEY"),
  base_url = "https://api.deepseek.com/v1",
  model = "deepseek-chat"
)

# bind tools to llm (llm can call these functions)
llm_with_tools = llm.bind_tools(tools)

# node 1. fetch repository code
async def fetch_repo_node(state: AgentState) -> AgentState:
  """Fetch repo code structure"""
  print(f"Fetching repo: {state['repo_owner']}/{state['repo_name']}")

  repo_code = await fetch_repo_code(
    owner=state['repo_owner'],
    repo=state['repo_name']
  )

  state['repo_code'] = repo_code
  return state

# node 2. retrieve relevant code sections using RAG
async def retrieve_rel_code_node(state: AgentState) -> AgentState:
  """Search pgvector for code sections relevant to the PR"""
  print(f"Searching for code similar to: {state["pr_title"]}")

  query = f"{state['pr_title']} {state['pr_body']}"

  relevant = await search similar_code(query = query, limit=5)

  state['relevant_code'] = relevant

  return state

# node 3. generate review with deepseek

async def review_code(state: AgentState) -> AgentState:
  """Call deepseek with pr data + relevant code context"""

  prompt = f"""
  Review this GitHub PR:
  Title: {state['pr_title']}
  Description: {state['pr_body']}

  Relevant code from the repository (retrieved via RAG): {state['relevant_code']}

  Provide a structured review with:
  1. Key Observations
  2. Suggestions for improvement
  3. Approval status(Approved/Request Change)
"""
  message = await llm_with_tools.ainvoke([
    {"role": "user", "content": prompt}
  ])

  state['review'] = message.content
  return state


# Building graph
workflow = StateGraph(AgentState)

# add nodes
workflow.add_node("fetch_repo", fetch_repo_node)
workflow.add_node("retrieve_code", retrieve_rel_code_node)
workflow.add_node("reivew", review_code)

# add edges (order of execution)
workflow.set_entry_point("fetch_repo")
workflow.add_edge("fetch_repo", "retrieve_code")
workflow.add_edge("retrieve_code", "review")
workflow.add_edge("review", END)

# compiling into exec agent
agent = workflow.compile()

# run the agent
async def run_review_agent(pr_data: dict) -> str:
  """Execute the review agent with PR data"""
  initial_state = AgentState(
    pr_number=pr_data['prNumber'],
    pr_title=pr_data['title'],
    pr_body=pr_data["body"],
    repo_owner=pr_data["owner"],
    repo_name=pr_data["repo"],
    repo_code="",
    relevant_code="",
    review=""
  )

  # execute agent (run through all nodes in order)
  result = await agent.ainvoke(initial_state)

  return result['review']
