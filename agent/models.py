from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

class PRData(BaseModel):
  """Pull request data from webhook"""
  prNumber: int = Field(..., description="PR number")
  title: str = Field(..., description="PR title")
  body: Optional[str] = Field(default="", description="PR description")
  owner: str = Field(..., description="Repository Owner")
  repo: str = Field(..., description="Repository name")
  repository: str = Field(..., description="Full repo path (owner/repo)")

  class Config:
    # allow extra fields from webhook but ignores them
    extra = "allow"


# what pgvector search returns
class CodeSnippet(BaseModel):
  """A code snippet from the repository"""
  file: str
  snippet: str
  similarity: float = Field(..., ge=-1, le=1)

# what agent returns
class ReviewResult(BaseModel):
  """Final review from the agent"""
  prNumber: int
  review: str
  repository: str
  timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

# database model for storing embeddings
class EmbeddingRecord(BaseModel):
  """Stores code + its embedding in PostgreSQL"""
  id: Optional[int] = None # autogen
  file_path: str
  code_snippet: str
  embedding: List[float] = Field(..., description="1536-dim vector from OpenAI")
  repository: str
  created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


