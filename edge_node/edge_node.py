import os
import time
import uuid
import random
import socket
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/vote")
EDGE_ID = f"edge-{socket.gethostname()}-{random.randint(1000, 9999)}"
MAX_RETRIES = 3

def generate_vote():
    """Generate a synthetic vote tagged with this edge node's ID."""
    return {
        "user_id": str(uuid.uuid4()),
        "poll_id": "poll_1",
        "choice": random.choice(["A", "B", "C"]),
        "edge_id": EDGE_ID,
        "timestamp": time.time(),
        "time_created": time.time(),
    }

def send_vote(vote):
    """Send vote with exponential backoff retry to simulate resilience."""
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(API_URL, json=vote, timeout=5)
            if r.status_code == 200:
                print(f"[{EDGE_ID}] ✓ Sent: {vote['user_id'][:8]} | Choice: {vote['choice']}")
                return True
            else:
                print(f"[{EDGE_ID}] ✗ HTTP {r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt + random.uniform(0, 1)
            print(f"[{EDGE_ID}] Retry {attempt + 1}/{MAX_RETRIES} after {wait:.1f}s: {e}")
            time.sleep(wait)
    print(f"[{EDGE_ID}] ✗ Failed after {MAX_RETRIES} attempts")
    return False

def run_edge_node():
    """Continuously generate and send votes with random delays."""
    print(f"[{EDGE_ID}] Edge node started. Streaming votes to {API_URL}")
    while True:
        vote = generate_vote()
        send_vote(vote)
        # Uncomment to simulate duplicate transmission (Part 5 Step 1):
        # send_vote(vote)
        time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    run_edge_node()