import asyncio
import json
import os
import threading

import redis
from dotenv import load_dotenv
from fastapi import FastAPI

from agent.agent import run_review_agent
from agent.db import db_manager

load_dotenv()

app = FastAPI(title="GitHub Code Reviewer Agent")

# Redis connection (synchronous client — the blocking pubsub loop runs in a thread).
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD") or None,
    decode_responses=True,
)

# Filled in on startup so the listener thread can hand coroutines back to the loop.
_event_loop: asyncio.AbstractEventLoop | None = None
_listener_thread: threading.Thread | None = None


def _handle_message(pr_data: dict) -> None:
    """Run the async review agent from the listener thread and publish the result."""
    assert _event_loop is not None
    future = asyncio.run_coroutine_threadsafe(run_review_agent(pr_data), _event_loop)
    try:
        review = future.result()
    except Exception as err:  # noqa: BLE001
        print(f"Error running review agent: {err}")
        review = f"Review failed: {err}"

    redis_client.publish(
        "reviews",
        json.dumps({
            "prNumber": pr_data.get("prNumber"),
            "review": review,
            "repository": pr_data.get("repository"),
        }),
    )
    print(f"Published review for PR #{pr_data.get('prNumber')}")


def _listen_loop() -> None:
    """Blocking Redis pubsub loop — runs in its own thread."""
    while True:
        try:
            pubsub = redis_client.pubsub()
            pubsub.subscribe("pull-request")
            print("Agent listening on pull-request channel")

            for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    pr_data = json.loads(message["data"])
                    print(f"Received PR #{pr_data.get('prNumber')}: {pr_data.get('title')}")
                    _handle_message(pr_data)
                except Exception as err:  # noqa: BLE001
                    print(f"Error processing message: {err}")
        except Exception as err:  # noqa: BLE001
            print(f"Redis listener error: {err}; reconnecting in 2s")
            import time

            time.sleep(2)


@app.on_event("startup")
async def startup() -> None:
    global _event_loop, _listener_thread
    print("Agent Service starting ...")
    await db_manager.init_db()
    print("Database initialized")

    _event_loop = asyncio.get_running_loop()
    _listener_thread = threading.Thread(target=_listen_loop, daemon=True)
    _listener_thread.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    print("Agent Service shutting down")
    await db_manager.close()
    print("db connection closed")


@app.get("/health")
async def health():
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "agent"}
    except Exception as err:  # noqa: BLE001
        return {"status": "unhealthy", "error": str(err)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent.main:app", host="0.0.0.0", port=8000)
