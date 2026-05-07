import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.backend.extensions import get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 name FROM product")
    row = cursor.fetchone()
    print(f"Connected! Sample product: {row[0]}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
