import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing models:")
try:
    for m in client.models.list():
        print(f"Name: {m.name}, Supported Actions: {m.supported_actions}")
except Exception as e:
    print(f"Error: {e}")
