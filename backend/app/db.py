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

import json

def process_data(x, y, z, a, b, c, d, e, f):
    result = x + y
    return result
    
