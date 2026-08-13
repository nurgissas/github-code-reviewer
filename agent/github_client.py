import os
import logging
from typing import Dict, List, Optional
from github import Github, GithubException
import json

logger = logging.getLogger(__name__)

class GithubClient:
  """Handles github api operations - cloning repos, and fetching code"""
  def __init__(self):
    """init github client with authentication"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
      raise ValueError("GITHUB_TOKEN env var is not set")
    self.client = Github(github_token)
    logger.info("Github client initialised")
  
  def fetch_repository_files(self, owner: str, repo: str, ref: str = "main")-> Dict:
    """Fetch repo code structure and important files
    Args:
      owner: Repository owner (e.g., "nurgissas")
      repo: Repository name (e.g., "github-code-reviewer")
      ref: Branch name (default: "main")
    
    Returns:
      Dictionary with:
        - files: List of Python files in repo
        - content: Dictionary of important file contents
        - repo_info: Metadata (description, language, etc)
    """

    try:
      repository = self.client.get_user(owner).get_repo(repo)
      logger.info(f"Fetching files from {owner}/{repo} (branch: {ref})")
      repo_info = {
        "name": repository.name,
        "description": repository.description,
        "language": repository.language,
        "stars": repository.stargazers_count,
        "url": repository.html_url
      }

      python_files = self._get_python_files(repository, ref)
      file_contents = {}
      for file_path in python_files[:20]:
        try:
          content = self._read_file(repository, file_path, ref)
          if content:
            file_contents[file_path] = content
        except Exception as e:
          logger.warning(f"Failed to read {file_path}: {e}")
          continue
      logger.info(f"Retrieved {len(file_contents)} python files")

      return {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "repo_info": repo_info,
        "files": list(file_contents.keys()),
        "content": file_contents
      }
    except GithubException as e:
      logger.error(f"Github API error: {e}")
    except Exception as e:
      logger.error(f"Failed to fetch repo: {e}")
  
  def _get_python_files(self, repository, ref: str="main", max_files: int=50)-> List[str]:
    """Recursively get all python files from repo
    Args:
      repository: GitHub repository object
      ref: Branch/ref to search
      max_files: Maximum files to return
    
    Returns:
      List of Python file paths (e.g., ["src/main.py", "tests/test_main.py"])
    """
    python_files=[]

    try:
      contents = repository.get_contents("", ref=ref)
      while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
          contents.extend(repository.get_contents(file_content.path, ref=ref))
        elif file_content.name.endswith(".py"):
          python_files.append(file_content.path)
          if len(python_files) >= max_files:
            break
      
      logger.info(f"Found {len(python_files)} python files")
      return python_files[:max_files]

    except Exception as e:
      logger.info(f"Failed to get python files: {e}")
      return []

  def _read_file(self, repository, file_path: str, ref:str="main") -> Optional[str]:
    """Read a single file content from repository.
    
    Args:
      repository: GitHub repository object
      file_path: Path to file (e.g., "src/main.py")
      ref: Branch/ref to read from
    
    Returns:
      File content as string, or None if failed
    """

    try:
      file_obj = repository.get_contents(file_path, ref=ref)
      if file_obj.size > 100000:
        logger.warning(f"File {file_path} is too large ({file_obj.size} bytes), skipping")
        return None
      content = file_obj.decoded_content.decode("utf-8")
      return content
    except Exception as e:
      logger.warning(f"Filaed to read {file_path}: {e}")
      return None
  
github_client = GithubClient()