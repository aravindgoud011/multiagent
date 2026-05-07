from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")

print(f"Checking index: {index_name}")
indexes = pc.list_indexes().names()
print(f"Available indexes: {indexes}")

if index_name in indexes:
    print("Index exists!")
else:
    print("Index NOT found.")
