import psycopg2
import os

def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="planviz",
        user="visualizer",
        password="localdevpassword"
    )
