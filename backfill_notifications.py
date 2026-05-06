import os
import pyodbc
from dotenv import load_dotenv

def backfill_notifications():
    load_dotenv()
    server = os.environ.get("AZURE_SQL_SERVER")
    username = os.environ.get("AZURE_SQL_USER")
    password = os.environ.get("AZURE_SQL_PASSWORD")
    db_name = os.environ.get("AZURE_SQL_DBNAME")
    
    conn_str = (
        "Driver={SQL Server};"
        f"Server={server};"
        f"Database={db_name};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Find all pending users
    cursor.execute("SELECT name, phone FROM users WHERE status = 'pending' AND role = 'customer'")
    pending_users = cursor.fetchall()
    
    for user in pending_users:
        name, phone = user
        # Check if notification already exists to avoid duplicates
        cursor.execute("SELECT id FROM notification WHERE title = 'New Registration' AND message LIKE ?", f"%{phone}%")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO notification (title, message) VALUES (?, ?)",
                ("New Registration", f"Customer {name} ({phone}) has registered and is pending approval.")
            )
            print(f"Added notification for {name}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    backfill_notifications()
