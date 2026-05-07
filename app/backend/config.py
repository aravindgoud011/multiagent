"""
Application configuration.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from .env file at the project root
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "kirana-store-secret-key-2024")
