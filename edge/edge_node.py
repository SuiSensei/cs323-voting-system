import requests
import uuid
import random
import time

# 🔗 Supabase Edge Function URL (ingest-vote)
API_URL = "https://YOUR_PROJECT_REF.supabase.co/functions/v1/ingest-vote"

# Optional: identify which edge node this is
EDGE_ID = str(uuid.uuid4())

def generate_vote():
    """
    Generates a single vote (simulates a user action).
    Each vote is unique.
    """
    return {
        "user_id": str(uuid.uuid4()),
        "poll_id": "poll_1",
        "choice": random.choice(["A", "B", "C"]),
        "timestamp": time.time(),
        "edge_id": EDGE_ID
    }

def send_vote(vote, retries=3):
    """
    Sends a vote to the Supabase ingestion API.
    Includes retry logic to simulate network instability.
    """
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, json=vote, timeout=5)
            print(f"✅ Vote sent ({response.status_code}) - User {vote['user_id']}")
            return
        except Exception as e:
            print(f"❌ Send failed (attempt {attempt + 1}):", e)
            time.sleep(1)

def run_edge_node():
    """
    Continuously generates and sends votes
    with random delays to simulate real edge behavior.
    """
    print(f"🟢 Edge node started: {EDGE_ID}")

    while True:
        vote = generate_vote()

        # Normal send
        send_vote(vote)

        # 🔁 OPTIONAL: simulate duplicate messages
        # send_vote(vote)

        time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    run_edge_node()