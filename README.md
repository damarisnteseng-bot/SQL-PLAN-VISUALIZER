# SQL Query Plan Visualizer & Optimizer Advisor

A full-stack tool that takes any SQL query, runs it through PostgreSQL's query planner, and automatically detects performance anti-patterns — returning specific, actionable index suggestions to fix them.

Built as a portfolio project to demonstrate systems thinking, backend engineering, and applied database knowledge.

---

## The Problem

Most developers write SQL that "works" but never look at how the database actually executes it. A query that's fast on 1,000 rows can fall over at 500,000 rows — and the difference is almost always visible in the execution plan, if you know how to read one.

This tool makes that invisible step visual and automatic.

---

## Demo

**Before adding an index — 225ms execution time, 166,843 rows scanned to find 1 match:**

![Issue detected](docs/screenshots/query-issue-detected.png)

**After applying the suggested index — 2ms execution time, clean result:**

![No issues](docs/screenshots/query-no-issues.png)

That's a ~110x speedup from a single index the tool suggested automatically.

---

## Features

- Paste any SQL query and get back its full execution plan as structured JSON
- Automatically detects 3 anti-patterns:
  - **Sequential scans** that waste work (distinguishes genuinely wasteful scans from necessary full-table reads)
  - **Bad row estimates** (stale table statistics), with a fix for false positives caused by LIMIT clauses
  - **Expensive nested loop joins** on large row counts
- Generates real, copy-pasteable CREATE INDEX SQL statements based on the detected filter columns
- Error handling: bad SQL returns a clean error message, not a server crash
- Before/after comparison: apply the suggested index and re-run to confirm the issue is gone

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Database | PostgreSQL 16 (Docker) | Industry standard, excellent EXPLAIN ANALYZE JSON output |
| Backend | Python + FastAPI | Fast to write, clean async API, great for JSON-heavy work |
| Frontend | React + Vite | Modern, fast dev experience, component-based UI |
| Data generation | Python + Faker | Realistic seed data at scale (700K+ rows) |
| Containerization | Docker + docker-compose | Reproducible, portable database setup |
| Version control | Git + GitHub | Full commit history showing incremental build |

---

## How It Works

1. User pastes a SQL query into the frontend
2. React sends a POST /analyze request to the FastAPI backend
3. FastAPI runs EXPLAIN (ANALYZE, FORMAT JSON) against PostgreSQL
4. The analyzer walks the returned plan tree recursively, checking each node for anti-patterns
5. Detected issues are returned alongside the raw plan, each with a severity level, explanation, and suggested fix
6. React renders the results: severity badges, issue messages, and copy-pasteable index SQL

---

## Project Structure
---

## Running Locally

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 22+

### Steps

**1. Start the database**
```bash
docker compose up -d
```

**2. Set up and start the backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary faker
uvicorn app.main:app --reload
```

**3. Seed the database (first time only)**
```bash
python3 seed-data/generate_data.py
```

**4. Start the frontend**
```bash
cd frontend
npm install
npm run dev
```

**5. Open in browser**
---

## Key Technical Decisions and Tradeoffs

**Why recursive tree-walking for plan analysis?**
PostgreSQL's execution plan is a tree, not a flat list. Walking it recursively ensures every node at every depth gets checked, regardless of query complexity.

**Why distinguish filtered vs unfiltered sequential scans?**
The naive approach flags every sequential scan as a problem. But a full-table scan with no WHERE clause is often intentional. I added a filter-presence check and a waste ratio calculation (rows discarded divided by rows scanned) to separate genuinely wasteful scans from necessary ones.

**Why skip row-estimate checks under a LIMIT node?**
PostgreSQL estimates row counts for the full result set, but LIMIT cuts execution short, so Actual Rows reflects a truncated count, not a true estimate mismatch. Without this fix, the tool produced false stale-statistics warnings on any query using LIMIT. Fixed by passing a flag down the tree during recursion to skip the check under Limit nodes.

**What is deliberately out of scope**
- Multi-database support (Oracle/MySQL have different plan formats)
- User authentication and multi-tenancy
- Full SQL parser for index suggestion (current regex heuristic covers the most common cases)

---

## What I Would Do Differently at Scale

- Replace the regex-based column extractor with a proper SQL parser like sqlglot
- Add a side-by-side plan comparison view (before/after applying a suggested index)
- Support saving and replaying query history
- Deploy with proper secrets management (credentials are currently hardcoded for local dev only)

---

*Built by Damaris Nteseng — Software Development student, Pretoria, South Africa*

## Live Demo

**Frontend:** https://sql-plan-visualizer-blond.vercel.app

**API:** https://sql-plan-visualizer-production.up.railway.app

## Running the Tests

The analyzer rules have a unit test suite covering all detection logic and edge cases:

    cd backend
    python3 tests/test_rules.py

All 7 tests pass, covering:
- Sequential scan detection (filtered vs unfiltered, size thresholds)
- Bad row estimate detection with LIMIT edge case fix
- Expensive nested loop detection
- Clean index scan producing zero false positives
