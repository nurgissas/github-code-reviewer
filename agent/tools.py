from typing import Optional
import os
import json
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field

# tool input schemas
class FetchRepoInput(BaseModel):
  owner: str = Field(description="Github repo owner")
  repo: str = Field(description="Repository name")
  ref: str = Field(default="main", description="Branch name")

class SearchCodeInput(BaseModel):
  query: str = Field(description="Search query for relevant code")
  limit: int = Field(default=5, description="Number of results")

# tool definition
@tool("fetch_repo_code")
def fetch_repo_code(owner: str, repo: str, ref: str = "main") -> str:
  """Fetch repository code structure and key files
  Returns a Json string with file list and content of important files. this simulates cloning the repo and reading files
  """
  # todo: will be implemented using possibly GitPython or Github API - mock data for now
  return json.dumps({
    "files": ["main.py", "utils.py", "model.py"],
    "content": {
      "main.py": "def process(): pass",
      "utils.py": "def helper(): pass"
    }
  })

@tool("search_similar_code")
def search_similar_code(query: str, limit: int=5) -> str:
  """Search pgvector db for code sections similar to query
  This searches embedding stored in PostgreSQL and returns the most relevant code snippets for the PR changes
  """
  #todo: will be connected to pgvector and do similarity search later on - mock data for now

  return json.dumps([
    {"file": "main.py", "snippet": "def process():", "similarity": 0.95 },
    {"file": "utils.py", "snippet": "def helper():", "similarity": 0.87 }
  ])


@tool("generate_embedding")
def generate_embedding(text: str) -> str:
  """Generate embedding vector for code text.
  Returns a vector that represents semantic meaning of the code
  Used to store pgvector for later similarity searches
  """

  # todo: use openAI embeddings or local model - mock vector for now

  return json.dumps({"embedding": [0.1,0.2,0.3], "dimension": 1536})


# export tools as a list
tools = [fetch_repo_code, search_similar_code, generate_embedding]