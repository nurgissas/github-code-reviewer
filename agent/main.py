from fastapi import FastAPI
import asyncio
import redis
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI(title="GitHub Code Reviewer Agent")

# Redis Connection
redis_client = redis.Redis(
  host = os.getenv("REDIS_HOST", "redis"),
  port = int(os.getenv("REDIS_PORT", 6379)),
  decode_responses = True
)

@app.on_event("startup")
async def startup():
  print("Agent Service starting ...")
  asyncio.create_task(listen_to_redis())

async def listen_to_redis():
  """Subscribe to Redis pull-request channel and process incoming PRs."""
  try:
    pubsub = redis_client.pubsub()
    pubsub.subscribe("pull_request")
    print("Agent listening on pull-request channel")

    for message in pubsub.listen():
      if message["type"] == "message":
        pr_data = json.load(message["data"])
        print(f"Received PR #{pr_data['prNumber']}: {pr_data['title']}")

        # LangGraph agent will be here
  except Exception as err:
    print(f"Error in listen_to_redis: {err}")
    await asyncio.sleep(2)
    await listen_to_redis() # retry

@app.get("/health")
async def health():
  """Health check endpoint for Docker"""
  try:
    redis_client.ping()
    return {"status": "healthy", "service": "agent"}
  except Exception as err:
    return {"status": "unhealthy", "error": str(err)}, 503
  

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)