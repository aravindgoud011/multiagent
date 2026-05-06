import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()
conn_str = (
    "Driver={SQL Server};"
    f"Server={os.environ['AZURE_SQL_SERVER']};"
    f"Database={os.environ['AZURE_SQL_DBNAME']};"
    f"Uid={os.environ['AZURE_SQL_USER']};"
    f"Pwd={os.environ['AZURE_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE product ADD image_url NVARCHAR(500)")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE bill ALTER COLUMN customer_id INT NULL")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE bill ADD customer_name NVARCHAR(120)")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE bill ADD bill_type NVARCHAR(20) DEFAULT 'instant'")
except Exception as e:
    print(e)

conn.commit()
print("Done")
