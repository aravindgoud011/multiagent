import os
import pyodbc
from dotenv import load_dotenv

def create_azure_sql_tables():
    """
    Creates all tables in the Azure SQL database using pure pyodbc.
    """
    load_dotenv()
    
    server = os.environ.get("AZURE_SQL_SERVER")
    username = os.environ.get("AZURE_SQL_USER")
    password = os.environ.get("AZURE_SQL_PASSWORD")
    db_name = os.environ.get("AZURE_SQL_DBNAME")
    
    if not all([server, username, password, db_name]):
        print("Please provide AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD, and AZURE_SQL_DBNAME in the .env file.")
        return
        
    print(f"Connecting to database {db_name} to create tables...")
    
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
        
        # Define table creation queries
        # Note: SQL Server specific types and syntax
        queries = [
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(120) NOT NULL,
                phone NVARCHAR(15) NOT NULL UNIQUE,
                password_hash NVARCHAR(256) NOT NULL,
                role NVARCHAR(10) NOT NULL DEFAULT 'customer',
                status NVARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='product' and xtype='U')
            CREATE TABLE product (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(150) NOT NULL,
                category NVARCHAR(80),
                price FLOAT NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                low_stock_threshold INT DEFAULT 10,
                unit NVARCHAR(20) DEFAULT 'pcs',
                image_url NVARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE(),
                updated_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='payment' and xtype='U')
            CREATE TABLE payment (
                id INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
                amount FLOAT NOT NULL,
                payment_mode NVARCHAR(10) NOT NULL,
                note NVARCHAR(255),
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='bill' and xtype='U')
            CREATE TABLE bill (
                id INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT FOREIGN KEY REFERENCES users(id),
                customer_name NVARCHAR(120),
                bill_type NVARCHAR(20) DEFAULT 'instant',
                total_amount FLOAT NOT NULL,
                discount FLOAT DEFAULT 0.0,
                final_amount FLOAT NOT NULL,
                status NVARCHAR(20) NOT NULL DEFAULT 'unpaid',
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='bill_item' and xtype='U')
            CREATE TABLE bill_item (
                id INT IDENTITY(1,1) PRIMARY KEY,
                bill_id INT NOT NULL FOREIGN KEY REFERENCES bill(id),
                product_id INT NOT NULL FOREIGN KEY REFERENCES product(id),
                quantity INT NOT NULL,
                price_per_unit FLOAT NOT NULL,
                subtotal FLOAT NOT NULL
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='notification' and xtype='U')
            CREATE TABLE notification (
                id INT IDENTITY(1,1) PRIMARY KEY,
                title NVARCHAR(100) NOT NULL,
                message NVARCHAR(500) NOT NULL,
                is_read BIT DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT GETUTCDATE()
            )
            """
        ]
        
        for q in queries:
            cursor.execute(q)
            
        conn.commit()
        print("Successfully created all tables in the database!")
        
        cursor.close()
        conn.close()
            
    except Exception as e:
        print("Failed to create tables. Please ensure the database exists and credentials are correct.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    create_azure_sql_tables()
