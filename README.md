# Smart Retail Assistant 🛒

An AI-powered multi-agent retail administration system for managing inventory, sales, and customer support.

## 🚀 Docker Setup (Recommended)

The easiest way to run the project is using Docker Compose.

### 1. Build and Run
```bash
docker compose up --build
```

### 2. Run in Background
```bash
docker compose up -d
```

### 3. Rebuild (after major changes)
```bash
docker compose build --no-cache
```

### 4. Stop
```bash
docker compose down
```

### 5. Run Tests inside Docker
```bash
docker exec -it smart-retail-app python -m pytest tests/test_agents.py
```

## 🛠 Project Structure
- `app/backend/`: Flask API and backend logic.
- `app/frontend/`: HTML/CSS/JS files for the admin dashboard.
- `agents/`: Multi-agent system (Supervisor, Inventory, Sales, Support).
- `ml/`: Local Machine Learning model for demand forecasting.
- `rag/`: FAISS vector index for product information.

## 🧪 Testing
Unit tests are located in the `tests/` directory and use `pytest`. They are configured to run with mocked services so no database or API keys are required for testing.

## 📦 Deployment
The `Dockerfile` is optimized for production-grade environments (like Azure App Service). It includes all necessary ODBC drivers for Azure SQL connectivity.

### Environment Variables
Ensure your `.env` file is populated with:
- `AZURE_SQL_SERVER`, `AZURE_SQL_USER`, etc.
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, etc.
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`
