import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, text
from pgvector.sqlalchemy import Vector
from datetime import datetime
import asyncio
import logging

logger=logging.getLogger(__name__)

# db base class for ORM models
Base = declarative_base()

class CodeEmbedding(Base):
  """Model for storing code embeddings in PostgreSQL"""
  __tablename__ = "code_embeddings"

  id = Column(Integer, primary_key=True, autoincrement = True)
  file_path=Column(String(500), nullable=False)
  code_snippet = Column(String(5000), nullable=False)
  embedding = Column(Vector(1536), nullable=False)
  repository = Column(String(200), nullable=False)
  created_at = Column(DateTime, default = datetime.timezone.utc)

  def __repr__(self):
    return f"<CodeEmbedding(file={self.file_path}, repo={self.repository})>"
  
class DatabaseManager:
  """Handles all db operations"""

  def __init__(self):
    """Init DB connection"""
    db_url = os.getenv(
      "DATABASE_URL",
      "postgresql+asyncpg://reviewer:password123@localhost:5432/code-reviewer"
    )

    # create async engine with connection pooling
    # pool size = 20 - 20 connections ready
    # max_overflow=0 - don't create more than pool_size connections
    self.engine = create_async_engine(
      db_url,
      echo=False,
      pool_size = 20,
      max_overflow=0,
      pool_pre_ping=True, # verify connection is alive before using
    )

    # session factory for creating db sessions
    # expire_on_commit=False - keep objects in memory after commit

    self.async_session = sessionmaker(
      self.engine,
      class_=AsyncSession,
      expire_on_commit=False
    )
  
  async def init_db(self):
    """Init db schema (create tables if absent)"""

    try:
      async with self.engine.begin() as conn:
        # enable pgvector extension - allows vector column type to work
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # create tables from orm models
        await conn.run_sync(Base.metadata.create_all)

      logger.info("Database initialized successfully")
    
    except Exception as e:
      logger.error(f"Failed to initialize db: {e}")
      raise
  
  async def store_embedding(
      self,
      file_path: str,
      code_snippet: str,
      embedding: list,
      repository: str
  ) -> int:
    """Store code and its embedding in PostgreSQL
    Args:
            file_path: Path to file (e.g., "src/auth.py")
            code_snippet: The actual code text
            embedding: 1536-dimensional vector from OpenAI
            repository: Repository name (owner/repo)
        
        Returns:
            ID of inserted record
    """
    async with self.async_session() as session:
      try:
        # create record
        record = CodeEmbedding(
          file_path = file_path,
          code_snippet = code_snippet,
          embedding = embedding,
          repository= repository
        )

        session.add(record)
        await session.commit()

        logger.info(f"Stored embedding for {file_path}")

      except Exception as e:
        await session.rollback()
        logger.error(f"Failed to store embedding: {e}")
        raise
  async def search_similar_code(
      self,
      query_embedding: list,
      repository: str,
      limit: int=5
  ) -> list:
    """Search pgvector for similar code
        
        How it works:
        1. Takes query embedding (from "PR title" converted to vector)
        2. Finds code embeddings with smallest distance (cosine similarity)
        3. Returns top N results
        
        Why pgvector:
        - Regular SQL can't do similarity search efficiently
        - pgvector uses IVFFlat index for fast approximate search
        - <=> operator does cosine distance calculation
        
        Args:
            query_embedding: Vector from PR title/description
            repository: Search only this repository
            limit: Return top N results
        
        Returns:
            List of {file_path, code_snippet, similarity_score}
    """
    async with self.async_session() as session:
      try:
        # SQL: Find closest embeddings using cosine distance
        # <=> operator: pgvector's cosine distance
        # ORDER BY ... gives closest first (smallest distance = most similar)
        # LIMIT: Return top N
                
        from sqlalchemy import select, func, and_
        from sqlalchemy.sql import desc
                
        # Calculate distance (1 - cosine similarity)
        # pgvector returns negative distance, so we use abs()
        distance_col = (func.sqrt(1 - func.l2_distance(CodeEmbedding.embedding, query_embedding)))
                
        stmt = (
           select(
              CodeEmbedding.file_path,
              CodeEmbedding.code_snippet,
              distance_col.label("similarity")
                    )
                    .where(CodeEmbedding.repository == repository)
                    .order_by(desc(distance_col))
                    .limit(limit)
                )
                
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                # Convert to list of dicts
                results = [
                    {
                        "file": row.file_path,
                        "snippet": row.code_snippet,
                        "similarity": float(row.similarity)
                    }
                    for row in rows
                ]
                
                logger.info(f"✓ Found {len(results)} similar code sections")
                return results
                
            except Exception as e:
                logger.error(f"✗ Search failed: {e}")
                return []
    
    async def close(self):
        """Close database connection pool"""
        await self.engine.dispose()
        logger.info("✓ Database connection closed")


# Global instance (singleton pattern) - don't create multiple connections, reuse one
db_manager = DatabaseManager()
