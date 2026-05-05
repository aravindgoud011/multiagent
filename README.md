# Smart Retail AI System — Kirana Store Backend

A production-ready Flask backend for managing inventory, billing, credit, and payments for a Kirana (retail) store.

## Tech Stack
- **Flask** — lightweight web framework
- **SQLAlchemy** — ORM (SQLite dev → MySQL prod)
- **Flask-JWT-Extended** — JWT authentication
- **Blueprint architecture** — modular, scalable code

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python run.py
```

Server starts at `http://127.0.0.1:5000`

## API Prefixes
| Module     | Prefix            |
|------------|-------------------|
| Auth       | `/api/auth`       |
| Inventory  | `/api/inventory`  |
| Billing    | `/api/billing`    |
| Payments   | `/api/payments`   |
| Customer   | `/api/customer`   |
