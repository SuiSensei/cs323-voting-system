import requests
import uuid
import random
import time

API_URL = "http://127.0.0.1:5000/vote"

def generate_vote(edge_id):
    return {
        "user_id": str(uuid.uuid4()),
        "poll_id": "poll_1",
        "choice": random.choice(["A", "B", "C"]),
        "edge_id": edge_id,
        "timestamp": time.time()
    }

def send_vote(vote):
    try:
        requests.post(API_URL, json=vote)
        print("Vote sent:", vote["user_id"])
    except Exception as e:
        print("Transmission failed:", e)

def run_edge_node(edge_id):
    while True:
        vote = generate_vote(edge_id)

        # intentional duplicate
        send_vote(vote)
        send_vote(vote)

        time.sleep(random.uniform(1, 3))

run_edge_node("edge_1")