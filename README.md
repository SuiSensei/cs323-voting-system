# CS323 Distributed Voting System (Supabase)

## Architecture

Edge Nodes → Supabase Edge Function (Ingest) → Queue Table → Worker → Votes Table

## Components

- Edge Nodes: Python scripts simulating clients
- Ingest Function: HTTP API for vote submission
- Worker Function: Asynchronous vote processor
- vote_queue: Message buffering table
- votes: Final persistent storage

## Fault Tolerance

- Duplicate messages handled via idempotent upserts
- Worker downtime causes queue buildup
- Recovery automatically processes queued votes

## Setup

1. Deploy Supabase Edge Functions
2. Run multiple edge nodes
3. Observe queueing, processing, and recovery

## Reflection

(Individual reflection per student)
