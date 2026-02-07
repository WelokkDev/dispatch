# Dispatch Backend

Flask API for the Dispatch app. Serves on port **5001** and allows requests from the Vite frontend (port 5173) via CORS.

## Prerequisites

- Python 3.8+

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate    # Windows
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
python app.py
```

Server runs at **http://localhost:5001** with debug mode on.

## API Endpoints

| Method | Path           | Description                    |
|--------|----------------|--------------------------------|
| GET    | `/api`         | API info                       |
| GET    | `/api/health`  | Health check (backend status)  |

### Examples

```bash
curl http://localhost:5001/api
# {"message":"Dispatch API"}

curl http://localhost:5001/api/health
# {"status":"ok","message":"Backend connected"}
```

## Frontend

The frontend (Vite/React) runs on **http://localhost:5173**. CORS is configured so the React app can call this API. Use base URL `http://localhost:5001` for API requests from the frontend.

## Dependencies

- **Flask** — web framework
- **flask-cors** — CORS support for cross-origin requests from the frontend
