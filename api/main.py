import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Distributed Voting API")

class Vote(BaseModel):
    user_id: str
    poll_id: str
    choice: str = Field(..., pattern="^[ABC]$")
    edge_id: str | None = None
    timestamp: float
    time_created: float | None = None

@app.get("/")
def health():
    return {"status": "ok", "service": "voting-api"}

@app.post("/vote")
def receive_vote(vote: Vote):
    """Accept a vote and enqueue it for async processing."""
    try:
        # Insert into the queue table — this is our 'publish to Pub/Sub' equivalent
        result = supabase.table("vote_queue").insert({
            "payload": vote.model_dump(),
            "status": "pending"
        }).execute()
        return {"status": "accepted", "queue_id": result.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))