"""
Entry point — run the Flask development server.

Usage:
    python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Use host='0.0.0.0' to ensure accessibility from outside the container
    app.run(host='0.0.0.0', debug=True, port=5000)
