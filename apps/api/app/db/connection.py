import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url = os.environ["DATABASE_URL"]
    return psycopg.connect(database_url)