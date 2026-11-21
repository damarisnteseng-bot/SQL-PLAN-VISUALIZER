from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import get_connection
from app.analyzer.rules import analyze_plan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    sql: str

def validate_query(sql: str):
    # Returns an error message if the query is not allowed, otherwise None
    cleaned = sql.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if not cleaned:
        return "Please enter a SQL query."
    if ";" in cleaned:
        return "Only a single statement is allowed."
    first_word = cleaned.split()[0].lower()
    if first_word not in ("select", "with"):
        return "Only SELECT queries can be analyzed here."
    return None

@app.get("/")
def root():
    return {"status": "SQL Plan Visualizer API is running"}

@app.post("/analyze")
def analyze_query(request: QueryRequest):
    problem = validate_query(request.sql)
    if problem:
        return JSONResponse(status_code=400, content={"error": problem})

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
