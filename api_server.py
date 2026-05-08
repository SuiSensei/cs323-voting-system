from flask import Flask, request, jsonify
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.route("/vote", methods=["POST"])
def receive_vote():
    vote = request.get_json()

    required = ["user_id", "poll_id", "choice"]

    for field in required:
        if field not in vote:
            return jsonify({"error": f"{field} missing"}), 400

    supabase.table("votes").insert(vote).execute()

    return jsonify({"status": "accepted"}), 200

if __name__ == "__main__":
    app.run(debug=True)
    
    supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)