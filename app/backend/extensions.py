"""
Shared extension instances and database utilities.
"""

import os
import pyodbc

def get_db_connection():
    server = os.environ.get("AZURE_SQL_SERVER")
    username = os.environ.get("AZURE_SQL_USER")
    password = os.environ.get("AZURE_SQL_PASSWORD")
    db_name = os.environ.get("AZURE_SQL_DBNAME")
    
    # Use different driver names for Windows vs Linux (Docker)
    driver = "{ODBC Driver 18 for SQL Server}" if os.name != 'nt' else "{SQL Server}"
    
    conn_str = (
        f"Driver={driver};"
        f"Server={server};"
        f"Database={db_name};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;" # Set to yes for dev convenience in docker
        "Connection Timeout=5;"
    )
    
    conn = pyodbc.connect(conn_str)
    return conn
