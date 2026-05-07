print("Test script starting...")
import os
import sys
from dotenv import load_dotenv
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.admin_graph import process_admin_query

load_dotenv()

def test():
    queries = [
        "What is the current stock of sugar?",
        "Show me sales for the last 3 days",
        "Are there any customer requests?",
        "Add a new product: 'Brown Rice', Category: 'Grains', Price: 80, Stock: 50"
    ]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        try:
            response = process_admin_query(q)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(15)

if __name__ == "__main__":
    test()
