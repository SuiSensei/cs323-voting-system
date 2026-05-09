import os
import time
import socket
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

WORKER_ID = f"worker-{socket.gethostname()}-{os.getpid()}"
POLL_INTERVAL = 1.0
BATCH_SIZE = 10

def claim_messages():
    """
    Atomically claim pending messages using a Postgres RPC.
    This is the FOR UPDATE SKIP LOCKED pattern — equivalent to Pub/Sub pull.
    """
    # We use rpc to a stored function for atomic claim. Alternative: simple update.
    result = supabase.rpc("claim_vote_messages", {
        "worker_id_in": WORKER_ID,
        "batch_size": BATCH_SIZE
    }).execute()
    return result.data or []

def process_vote(message):
    """Process a single vote message idempotently."""
    vote = message["payload"]
    queue_id = message["id"]

    # Idempotency key: same user + same poll = same doc
    doc_id = f"{vote['user_id']}_{vote['poll_id']}"

    try:
        # Upsert ensures duplicates collapse into a single record
        supabase.table("votes").upsert({
            "doc_id": doc_id,
            "user_id": vote["user_id"],
            "poll_id": vote["poll_id"],
            "choice": vote["choice"],
            "edge_id": vote.get("edge_id"),
            "timestamp": vote["timestamp"],
            "time_created": vote.get("time_created"),
        }).execute()

        # Acknowledge: mark queue row as done
        supabase.table("vote_queue").update({"status": "done"}).eq("id", queue_id).execute()
        print(f"[{WORKER_ID}] ✓ Processed: {vote['user_id'][:8]} | Poll: {vote['poll_id']} | Choice: {vote['choice']}")
        return True

    except Exception as e:
        # Don't ack — release for retry
        retry = message.get("retry_count", 0) + 1
        new_status = "failed" if retry >= 5 else "pending"
        supabase.table("vote_queue").update({
            "status": new_status,
            "retry_count": retry,
            "locked_by": None,
            "locked_at": None,
        }).eq("id", queue_id).execute()
        print(f"[{WORKER_ID}] ✗ Error processing {queue_id} (retry {retry}): {e}")
        return False

def run_worker():
    """Continuously poll the queue and process messages."""
    print(f"[{WORKER_ID}] Worker started. Polling queue every {POLL_INTERVAL}s")
    while True:
        try:
            messages = claim_messages()
            if not messages:
                time.sleep(POLL_INTERVAL)
                continue
            for msg in messages:
                process_vote(msg)
        except Exception as e:
            print(f"[{WORKER_ID}] Loop error: {e}")
            time.sleep(POLL_INTERVAL * 2)

if __name__ == "__main__":
    run_worker()