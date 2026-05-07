import pyodbc
import os
from dotenv import load_dotenv

def get_product_mapping():
    load_dotenv()
    conn_str = (
        "Driver={SQL Server};"
        f"Server={os.getenv('AZURE_SQL_SERVER')};"
        f"Database={os.getenv('AZURE_SQL_DBNAME')};"
        f"Uid={os.getenv('AZURE_SQL_USER')};"
        f"Pwd={os.getenv('AZURE_SQL_PASSWORD')};"
        "Encrypt=yes;"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get all unique products that might have been in the training data
        cursor.execute("SELECT DISTINCT name FROM product")
        products = [row[0] for row in cursor.fetchall()]
        products.sort() # LabelEncoder sorts alphabetically
        
        mapping = {name: i for i, name in enumerate(products)}
        conn.close()
        return mapping
    except Exception as e:
        print(f"Error fetching products: {e}")
        return {}

if __name__ == "__main__":
    mapping = get_product_mapping()
    print("Alphabetical Product Mapping (LabelEncoder Style):")
    for name, code in mapping.items():
        print(f"{code}: {name}")
