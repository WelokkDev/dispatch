# ⚡ Quick Start

Get Dispatch running in 5 minutes.

## Prerequisites

```bash
# Check you have these installed
python3 --version  # Need 3.8+
node --version     # Need 18+
```

## Installation

```bash
# 1. Clone
git clone https://github.com/yourusername/dispatch.git
cd dispatch

# 2. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env
# Edit .env with your API keys

# 3. Frontend
cd ../frontend
npm install
cp .env.sample .env
# Edit .env if needed
```

## Run

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Test

```bash
# Open http://localhost:5173

# Send test call
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test-1", "message": "Fire at 123 Main St"}'
```

## API Keys Needed

- **Gemini**: https://aistudio.google.com/app/apikey
- **Gradium**: https://gradium.ai
- **Twilio**: https://console.twilio.com/
- **MongoDB**: https://cloud.mongodb.com/

## Project Structure

```
dispatch/
├── backend/          # Flask API
│   ├── app.py       # Main app
│   ├── services/    # AI, voice, triage
│   └── routes/      # API endpoints
├── frontend/         # React UI
│   └── src/
│       ├── App.tsx  # Main component
│       └── components/
└── README.md        # Full docs
```

## Key Endpoints

- `GET /api/health` - Health check
- `POST /api/chat` - Test endpoint
- `GET /api/calls` - Fetch calls
- `GET /api/events` - SSE stream
- `POST /voice` - Twilio webhook

## Common Commands

```bash
# Backend tests
cd backend && python -m pytest test/

# Frontend build
cd frontend && npm run build

# Check logs
tail -f backend/logs/*.log
```

## Need Help?

- 📖 Read [README.md](README.md) for full documentation
- 🛠️ See [SETUP.md](SETUP.md) for detailed setup
- 🎬 Check [DEMO.md](DEMO.md) for demo scenarios
- ✨ View [FEATURES.md](FEATURES.md) for feature list

## Quick Links

- Backend: http://localhost:5001
- Frontend: http://localhost:5173
- API Docs: http://localhost:5001/api
- Health: http://localhost:5001/api/health

---

**Built for QHacks 2025** | MIT License
