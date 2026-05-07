from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

print("Initializing LLM...")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
print("LLM Initialized. Sending test query...")
try:
    response = llm.invoke("Hi")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")
