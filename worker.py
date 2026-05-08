from supabase import create_client
from dotenv import load_dotenv
import os
import time

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

while True:

    response = supabase.table("votes") \
        .select("*") \
        .eq("processed", False) \
        .execute()

    votes = response.data

    for vote in votes:

        doc_id = f"{vote['user_id']}_{vote['poll_id']}"

        existing = supabase.table("processed_votes") \
            .select("*") \
            .eq("user_id", vote["user_id"]) \
            .eq("poll_id", vote["poll_id"]) \
            .execute()

        if len(existing.data) == 0:

            supabase.table("processed_votes").insert({
                "user_id": vote["user_id"],
                "poll_id": vote["poll_id"],
                "choice": vote["choice"],
                "edge_id": vote["edge_id"],
                "timestamp": vote["timestamp"]
            }).execute()

            print("Processed:", vote["user_id"])

        supabase.table("votes") \
            .update({"processed": True}) \
            .eq("id", vote["id"]) \
            .execute()

    time.sleep(2)
    
    supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)