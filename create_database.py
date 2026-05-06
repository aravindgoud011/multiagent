import os
import pyodbc
from dotenv import load_dotenv

def create_azure_sql_database():
    """
    Connects to Azure SQL master database using pyodbc and creates the target database if it doesn't exist.
    """
    load_dotenv()
    
    server = os.environ.get("AZURE_SQL_SERVER")
    username = os.environ.get("AZURE_SQL_USER")
    password = os.environ.get("AZURE_SQL_PASSWORD")
    db_name = os.environ.get("AZURE_SQL_DBNAME")
    
    if not all([server, username, password, db_name]):
        print("Please provide AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD, and AZURE_SQL_DBNAME in the .env file.")
        return

    print(f"Attempting to log into Azure SQL server to create database: {db_name}")
    
    # Connection string for master database
    conn_str = (
        "Driver={SQL Server};"
        f"Server={server};"
        "Database=master;"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    
    try:
        # Connect to master with autocommit so CREATE DATABASE works
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", db_name)
        if cursor.fetchone():
            print(f"Database '{db_name}' already exists.")
        else:
            print(f"Database '{db_name}' not found. Creating...")
            cursor.execute(f"CREATE DATABASE [{db_name}]")
            print(f"Database '{db_name}' created successfully.")
            
        cursor.close()
        conn.close()
                
    except Exception as e:
        print("Failed to connect or create Azure SQL database. Please check your credentials and firewall settings.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    create_azure_sql_database()
