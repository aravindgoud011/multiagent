import os
import pyodbc
import json
from datetime import datetime
from dotenv import load_dotenv

def seed_database():
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
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seed_file = os.path.join(base_dir, 'seed_data.json')
    
    if not os.path.exists(seed_file):
        print(f"No {seed_file} found. Skipping seeding.")
        return

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)

        print("Starting data seeding...")

        # Order matters for foreign keys
        tables = ['users', 'product', 'bill', 'payment', 'bill_item', 'notification', 'support_ticket']

        for table in tables:
            rows = seed_data.get(table, [])
            if not rows:
                continue
            
            print(f"Seeding table: {table} ({len(rows)} rows)")
            
            # Enable identity insert so we can preserve IDs
            cursor.execute(f"SET IDENTITY_INSERT {table} ON")
            
            for row in rows:
                # Check if already exists by ID
                cursor.execute(f"SELECT id FROM {table} WHERE id = ?", row['id'])
                if cursor.fetchone():
                    continue # Skip if already exists
                
                columns = list(row.keys())
                placeholders = ", ".join(["?" for _ in columns])
                col_names = ", ".join(columns)
                
                values = []
                for col in columns:
                    val = row[col]
                    # Handle datetime strings
                    if col in ['created_at', 'updated_at'] and isinstance(val, str):
                        try:
                            val = datetime.fromisoformat(val)
                        except:
                            pass
                    values.append(val)
                
                sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                cursor.execute(sql, values)
            
            cursor.execute(f"SET IDENTITY_INSERT {table} OFF")
            print(f"- {table} seeding completed.")

        conn.commit()
        print("Seeding finished successfully!")
        conn.close()
        
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_database()
