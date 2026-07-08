from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.db import get_connection
from app.analyzer.rules import analyze_plan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://sql-plan-visualizer-blond.vercel.app",
        "https://*.vercel.app"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    sql: str

@app.get("/")
def root():
    return {"status": "SQL Plan Visualizer API is running"}

@app.post("/analyze")
def analyze_query(request: QueryRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {request.sql}")
        result = cur.fetchone()[0]
        issues = analyze_plan(result)
        return {"plan": result, "issues": issues}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
