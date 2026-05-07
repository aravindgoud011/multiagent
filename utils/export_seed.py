import os
import pyodbc
import json
from datetime import datetime
from dotenv import load_dotenv

def export_to_seed():
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
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        tables = ['users', 'product', 'bill', 'bill_item', 'payment', 'notification', 'support_ticket']
        seed_data = {}
        
        for table in tables:
            print(f"Exporting table: {table}")
            cursor.execute(f"SELECT * FROM {table}")
            columns = [column[0] for column in cursor.description]
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Convert datetime objects to string
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                rows.append(row_dict)
            seed_data[table] = rows
            
        with open('seed_data.json', 'w') as f:
            json.dump(seed_data, f, indent=4)
            
        print("Data exported successfully to seed_data.json")
        conn.close()
        
    except Exception as e:
        print(f"Error exporting data: {e}")

if __name__ == "__main__":
    export_to_seed()
