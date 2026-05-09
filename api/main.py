import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
API_VERSION = os.getenv("API_VERSION", "1.0.0")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Distributed Voting API", version=API_VERSION)

class Vote(BaseModel):
    user_id: str
    poll_id: str
    choice: str = Field(..., pattern="^[ABC]$")
    edge_id: str | None = None
    timestamp: float
    time_created: float | None = None


@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "voting-api",
        "version": API_VERSION,
        "time": datetime.utcnow().isoformat(),
    }


@app.get("/stats")
def stats():
    """Return basic queue statistics."""
    try:
        pending = supabase.table("vote_queue").select("id", count="exact").eq("status", "pending").execute()
        return {
            "pending_count": pending.count if hasattr(pending, "count") else len(pending.data),
        }
    except Exception as e:
        logger.exception("Failed to fetch stats")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vote")
def receive_vote(vote: Vote):
    """Accept a vote and enqueue it for async processing."""
    try:
        # Insert into the queue table — this is our 'publish to Pub/Sub' equivalent
        result = supabase.table("vote_queue").insert({
            "payload": vote.model_dump(),
            "status": "pending"
        }).execute()
        queue_id = result.data[0]["id"]
        logger.info(f"Vote accepted | poll={vote.poll_id} choice={vote.choice} edge={vote.edge_id} queue_id={queue_id}")
        return {"status": "accepted", "queue_id": queue_id}
    except Exception as e:
        logger.exception("Failed to enqueue vote")
        raise HTTPException(status_code=500, detail=str(e))