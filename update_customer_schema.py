import os
import pyodbc
from dotenv import load_dotenv

def update_schema():
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
        
        print("Updating schema for customer portal...")

        # 1. Add loyalty_points to users
        try:
            cursor.execute("ALTER TABLE users ADD loyalty_points INT DEFAULT 0")
            print("- Added loyalty_points to users table")
        except:
            print("- loyalty_points already exists in users table")

        # 2. Add user_id to notification
        try:
            cursor.execute("ALTER TABLE notification ADD user_id INT FOREIGN KEY REFERENCES users(id)")
            print("- Added user_id to notification table")
        except:
            print("- user_id already exists in notification table")

        # 3. Create support_ticket table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='support_ticket' and xtype='U')
            CREATE TABLE support_ticket (
                id INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
                title NVARCHAR(150) NOT NULL,
                description NVARCHAR(MAX) NOT NULL,
                category NVARCHAR(50) DEFAULT 'General',
                status NVARCHAR(20) DEFAULT 'Open',
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
        """)
        print("- Created/Verified support_ticket table")

        conn.commit()
        print("Schema updated successfully!")
        
        cursor.close()
        conn.close()
            
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
