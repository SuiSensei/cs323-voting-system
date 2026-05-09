# Distributed Voting System with Edge–Cloud Architecture and Fault Tolerance

**Course:** CS323 — Distributed Computing
**Lab Activity:** Second Laboratory (Final)
**Group:** Group X
**Members:** Member 1, Member 2, Member 3, Member 4

---

## 1. System Overview

This project implements a **distributed voting system** where multiple edge nodes
generate votes independently and transmit them to a cloud-based ingestion pipeline.
The system processes votes asynchronously and stores them in a persistent database,
remaining functional even when individual components fail.

The system was originally specified for **Google Cloud Platform (GCP)**. This
implementation maps that architecture to an equivalent **Supabase + FastAPI** stack
while preserving every distributed-systems property required by the lab: event-driven
flow, decoupled ingestion and processing, retries, idempotency, and asynchronous
recovery.

### 1.1 Architecture Mapping (GCP → Supabase)

| Lab requirement (GCP)        | Our implementation                                       | Role                                              |
|------------------------------|----------------------------------------------------------|---------------------------------------------------|
| Edge nodes                   | Python scripts (one per group member)                    | Generate and transmit votes                       |
| Cloud Run API                | FastAPI deployed on Render                               | Receive HTTP POST requests, validate, enqueue     |
| Pub/Sub topic + subscription | Postgres `vote_queue` table + `claim_vote_messages` RPC  | Decouple ingestion from processing, buffer load   |
| Worker service               | Python worker (long-running, polls the queue)            | Consume messages, write to storage                |
| Firestore                    | Supabase Postgres `votes` table                          | Persistent storage of processed votes             |

The Pub/Sub equivalent uses Postgres' `FOR UPDATE SKIP LOCKED` pattern — a
well-established message-queue technique that gives the same guarantees as a real
broker (at-least-once delivery, retry-on-failure, multi-worker safety).

### 1.2 Architecture Diagram

```text
+---------------+     HTTP POST      +-----------------+
|  Edge Node 1  |  ---------------> |                 |
+---------------+                    |    FastAPI      |     INSERT
+---------------+                    |  (on Render)    |  -----------+
|  Edge Node 2  |  ---------------> |                 |             |
+---------------+                    +-----------------+             v
+---------------+                                          +-------------------+
|  Edge Node N  |  ----------------------------------->   |   vote_queue      |
+---------------+                                          |   (Postgres)      |
                                                           +-------------------+
                                                                    |
                                                  claim_vote_messages RPC
                                                  (FOR UPDATE SKIP LOCKED)
                                                                    |
                                                                    v
                                                           +-------------------+
                                                           |  Worker Service   |
                                                           |  (Python loop)    |
                                                           +-------------------+
                                                                    |
                                                              UPSERT (idempotent)
                                                                    |
                                                                    v
                                                           +-------------------+
                                                           |   votes table     |
                                                           |   (Postgres)      |
                                                           +-------------------+
```

### 1.3 Distributed-Systems Properties Demonstrated

- **Event-driven pipeline** — components communicate via the queue, not direct calls
- **Decoupling** — the API does not block on processing; the worker can scale or fail independently
- **Idempotency** — `doc_id = user_id_poll_id` is the primary key; duplicate deliveries collapse via UPSERT
- **At-least-once delivery** — failed messages remain `pending` and are retried
- **Asynchronous recovery** — when the worker is restored, it drains the queue automatically
- **Eventual consistency** — even with delays or duplicates, the final state of `votes` is correct

### 1.4 Deployed API Endpoint

```text
https://YOUR-APP-NAME.onrender.com
```

Health check: `GET /` returns `{"status": "ok", "service": "voting-api"}`
Vote endpoint: `POST /vote` with JSON body `{user_id, poll_id, choice, edge_id, timestamp, time_created}`

---

## 2. Repository Structure

```text
voting-system/
├── edge_node/
│   ├── edge_node.py          # Vote generator + HTTP sender (one per group member)
│   └── requirements.txt
├── api/
│   ├── main.py               # FastAPI ingestion service (Cloud Run equivalent)
│   └── requirements.txt
├── worker/
│   ├── worker.py             # Async queue consumer (Cloud Run worker equivalent)
│   └── requirements.txt
├── supabase/
│   └── schema.sql            # Tables, indexes, and the claim RPC
├── .env.example              # Template for environment variables
├── .gitignore
└── README.md
```

---

## 3. Setup and Execution Instructions

### 3.1 Prerequisites

- Python 3.10+
- A free Supabase account: <https://supabase.com>
- A free Render account (for deploying the API): <https://render.com>
- Git

### 3.2 Provision Supabase

1. Create a new project at <https://supabase.com> and pick a region close to your group
   (we used **Southeast Asia — Singapore**)
2. Open the **SQL Editor** and run the contents of `supabase/schema.sql`. This creates
   the `votes` table, the `vote_queue` table, and the `claim_vote_messages` function
3. Copy your credentials from **Project Settings → API**:
   - `Project URL` → goes into `SUPABASE_URL`
   - `service_role` secret key → goes into `SUPABASE_SERVICE_KEY`

### 3.3 Configure local environment

```bash
git clone https://github.com/YOUR_GROUP/voting-system.git
cd voting-system

# Copy the template and fill in real values
cp .env.example .env          # macOS/Linux
copy .env.example .env        # Windows
```

Edit `.env`:

```env
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
API_URL=http://localhost:8000/vote
```

### 3.4 Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows PowerShell
# source .venv/bin/activate         # macOS/Linux

pip install -r api/requirements.txt
pip install -r worker/requirements.txt
pip install -r edge_node/requirements.txt
```

### 3.5 Run the system locally (3+ terminals)

Make sure each terminal shows `(.venv)` at the prompt. PowerShell users: separate
commands with `;` instead of `&&`, or run them on separate lines.

```powershell
# Terminal 1 - API
cd api
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Worker
cd worker
python worker.py

# Terminal 3, 4, 5... - Edge nodes (one per group member)
cd edge_node
python edge_node.py
```

You should immediately see:

- The edge node printing `OK Sent: <user_id> | Choice: <A/B/C>`
- The API printing `200 OK` for each request
- The worker printing `OK Processed: <user_id> | Poll: poll_1`
- New rows appearing in the `votes` table in the Supabase Table Editor

### 3.6 Deploy the API to Render (for distributed edge testing)

So group members on different machines can share one API:

1. Push this repo to GitHub
2. On Render: **New → Web Service → connect repo**
3. Settings:
   - **Root Directory:** `api`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
5. After deployment, copy the public URL and update each member's `.env`:

   ```env
   API_URL=https://your-app.onrender.com/vote
   ```

Each member can now run `edge_node.py` from their own laptop — true distributed edges.

### 3.7 Fault Injection Tests

#### Test A — Duplicate transmission (idempotency check)

In `edge_node/edge_node.py`, uncomment the duplicate line in `run_edge_node()`:

```python
vote = generate_vote()
send_vote(vote)
send_vote(vote)   # duplicate
```

Restart the edge node and run in the SQL Editor:

```sql
SELECT
  (SELECT COUNT(*) FROM vote_queue) AS queued,
  (SELECT COUNT(*) FROM votes) AS stored;
```

**Observation:** `queued` is roughly 2× `stored`. The `votes` count remains correct
because the worker uses `UPSERT` on `doc_id`. This proves idempotency works.

#### Test B — Worker failure (failure isolation)

While the edge node is running, kill the worker (Ctrl+C). Wait ~30 seconds:

```sql
SELECT status, COUNT(*) FROM vote_queue GROUP BY status;
```

**Observation:** `pending` count grows continuously, `done` is frozen, but the API
keeps accepting votes. Failure is isolated to the worker layer.

#### Test C — Recovery (asynchronous catchup)

Restart the worker (`python worker.py`). Watch its log — it bursts through the backlog.
Re-run the query from Test B.

**Observation:** `pending` drains rapidly to ~0, `done` jumps. No votes lost, no
manual intervention required. This proves asynchronous recovery via message
persistence.

### 3.8 Evaluation Queries

After running the system for 10+ minutes:

```sql
-- Total votes by choice
SELECT choice, COUNT(*) FROM votes GROUP BY choice;

-- Throughput per minute
SELECT date_trunc('minute', processed_at) AS minute, COUNT(*) AS votes
FROM votes GROUP BY 1 ORDER BY 1 DESC LIMIT 20;

-- End-to-end latency (edge timestamp -> Firestore-equivalent timestamp)
SELECT user_id,
       ROUND((EXTRACT(EPOCH FROM processed_at) - time_created)::numeric, 3) AS latency_seconds
FROM votes ORDER BY processed_at DESC LIMIT 10;

-- Final consistency check
SELECT
  (SELECT COUNT(*) FROM vote_queue WHERE status='done') AS processed,
  (SELECT COUNT(*) FROM votes) AS stored,
  (SELECT COUNT(*) FROM vote_queue WHERE status='pending') AS still_pending;
```

---

## 4. Demo

A short demonstration video showing the full pipeline (edge → API → queue → worker
→ database, plus fault injection and recovery) is included in this repository:

`demo/demo.mp4` — or — `demo/demo.gif`

---

## 5. Individual Reflections

> Each member writes their own reflection in paragraph form, grounded in what they
> actually observed during implementation and testing. Focus on real outcomes from
> the edge nodes, API, queue, worker, and database — not textbook definitions.
> Suggested aspects to touch on (not all required):
>
> - Differences between sequential vs. distributed execution
> - System behavior as vote volume increases (latency, queue buildup, throughput)
> - Implementation challenges (Supabase setup, integration, async debugging)
> - Insights about communication overhead, buffering, eventual consistency
> - Where distribution helped, and where it added complexity

### 5.1 Member 1 — _Full Name_

### 5.2 Member 2 — _Full Name_

_Your reflection here..._

### 5.3 Member 3 — _Full Name_

_Your reflection here..._

### 5.4 Member 4 — _Full Name_

_Your reflection here..._

---

## 6. Trade-offs Observed

Documented as required by the lab's evaluation step:

- **Queue buffering** improved reliability (no votes lost during worker downtime) but
  introduced a small ingestion-to-storage delay even under normal load.
- **API + worker decoupling** improved scalability (the API never blocks on storage)
  but required us to add an idempotency key (`doc_id`) so duplicate deliveries don't
  corrupt vote counts.
- **Distributed edge nodes** reduced perceived load on any single sender but
  complicated debugging — logs are spread across multiple terminals/machines, so
  we added an `edge_id` field to every vote to trace its origin.
- **Render free tier** has cold-start delays after inactivity, which we observed as
  occasional 2–5 second response spikes after idle periods. This mirrors the
  cold-start trade-off Cloud Run also exhibits.

---

## 7. Notes for the Instructor

We chose Supabase (Postgres) over GCP because of platform-availability constraints
during the lab window, but every required distributed-systems concept is
demonstrably implemented:

| Lab requirement                     | Where it lives in this repo                           |
|-------------------------------------|-------------------------------------------------------|
| Edge-to-cloud HTTP pipeline         | `edge_node/edge_node.py` → `api/main.py`              |
| Asynchronous messaging (Pub/Sub)    | `vote_queue` table + `claim_vote_messages` RPC        |
| Worker consuming from a queue       | `worker/worker.py`                                    |
| Persistent storage (Firestore)      | `votes` table                                         |
| Retry + exponential backoff         | `send_vote()` in `edge_node.py`                       |
| Idempotency                         | `doc_id` PK + `UPSERT` in `worker.py`                 |
| Fault injection (worker downtime)   | Section 3.7, Test B                                   |
| Recovery via message persistence    | Section 3.7, Test C                                   |
| End-to-end latency measurement      | Section 3.8 latency query                             |
| Eventual consistency check          | Section 3.8 consistency query                         |
