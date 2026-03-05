# 🚨 Dispatch - AI-Powered 911 Emergency Call System

> An intelligent emergency dispatch system that uses AI to triage 911 calls, extract critical information, and provide real-time visualization for emergency operators.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000.svg)](https://flask.palletsprojects.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg)](https://www.typescriptlang.org/)

## 📋 Overview

Dispatch is a modern emergency call handling system that leverages AI to streamline 911 operations. The system automatically triages incoming calls, extracts critical information (emergency type, location, caller details), and provides dispatchers with a real-time dashboard featuring live transcripts and interactive maps.

### ✨ Key Features

- **🤖 AI-Powered Triage**: Automatically assesses call urgency (P0-P3) and extracts critical information using Google Gemini
- **📞 Voice Integration**: Seamless Twilio integration for real-time phone call handling with speech-to-text
- **🗣️ Natural Voice Synthesis**: High-quality text-to-speech using Gradium TTS for natural dispatcher responses
- **🗺️ Interactive Map**: Real-time visualization of emergency locations with geocoding
- **📊 Live Dashboard**: Real-time call monitoring with Server-Sent Events (SSE)
- **💾 Persistent Storage**: MongoDB integration for call history and analytics
- **⚡ Smart Prioritization**: Dynamic urgency assessment that adapts as calls progress
- **🔄 Operator Handoff**: Automatic transfer to human operators for high-priority emergencies

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Twilio Voice  │────────▶│  Flask Backend   │────────▶│   React UI      │
│   (Phone Calls) │         │  - AI Triage     │         │  - Live Map     │
└─────────────────┘         │  - TTS/STT       │         │  - Transcripts  │
                            │  - Geocoding     │         │  - Call List    │
                            └──────────────────┘         └─────────────────┘
                                     │
                            ┌────────┴────────┐
                            │                 │
                      ┌─────▼─────┐    ┌─────▼─────┐
                      │  MongoDB  │    │  Gemini   │
                      │  (Calls)  │    │   (AI)    │
                      └───────────┘    └───────────┘
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** and npm
- **MongoDB** (local or Atlas)
- **Twilio Account** (for voice integration)
- **Google AI API Key** (for Gemini)
- **Gradium API Key** (for TTS)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dispatch.git
cd dispatch
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from sample
cp .env.sample .env
# Edit .env with your API keys (see Configuration section)
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file from sample
cp .env.sample .env
# Edit .env with your backend URL
```

### Configuration

#### Backend Environment Variables (`.env`)

```env
# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Gradium TTS
GRADIUM_API_KEY=your_gradium_api_key_here
GRADIUM_VOICE_ID=your_voice_id_here
GRADIUM_REGION=us

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Dispatch

# Flask
PORT=5001
FLASK_DEBUG=1
```

#### Frontend Environment Variables (`.env`)

```env
# Backend API URL
VITE_API_BASE_URL=http://127.0.0.1:5001

# MongoDB (for direct access if needed)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Dispatch
```

### Running the Application

#### Start Backend

```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python app.py
```

Backend runs at `http://localhost:5001`

#### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173`

### For Production Deployment

#### Backend (with ngrok for Twilio webhooks)

```bash
# Terminal 1: Start backend
cd backend
python app.py

# Terminal 2: Expose with ngrok
ngrok http 5001
```

Update your Twilio webhook URLs to point to your ngrok URL:
- Voice URL: `https://your-ngrok-url.ngrok.io/voice`
- Status Callback: `https://your-ngrok-url.ngrok.io/voice/respond`

## 📚 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/voice` | Twilio webhook for incoming calls |
| `POST` | `/voice/respond` | Twilio webhook for caller speech |
| `GET` | `/api/events` | SSE stream for real-time updates |
| `POST` | `/api/chat` | Text-based testing endpoint |
| `GET` | `/api/calls` | Fetch all persisted calls |
| `GET` | `/api/active-calls` | Get in-memory active calls |
| `GET` | `/api/health` | Health check |
| `GET` | `/audio/<filename>` | Serve generated audio files |

### Example: Text-Based Testing

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-123",
    "message": "There is a fire at 123 Main Street"
  }'
```

## 🧠 AI Triage System

The system uses a sophisticated priority-based triage algorithm:

### Priority Levels

- **P0 (Critical)**: Immediate life threat
  - No re-asking, immediate operator transfer
  - Examples: cardiac arrest, active shooter, severe trauma
  
- **P1 (Urgent)**: Serious emergency requiring rapid response
  - Re-ask emergency + location (1x each), then transfer
  - Skip name/phone collection
  - Examples: chest pain, difficulty breathing, serious injury
  
- **P2 (Moderate)**: Standard emergency
  - Full information collection with re-asks
  - Examples: minor injuries, property damage, theft
  
- **P3 (Low)**: Non-urgent
  - Complete information gathering
  - Examples: noise complaints, minor incidents

### Information Extraction

The AI extracts four key pieces of information:
1. **Emergency Type**: What happened (under 5 words)
2. **Location**: Address or landmark
3. **Caller Name**: Full name
4. **Phone Number**: Callback number

### Dynamic Urgency Assessment

Urgency is reassessed on **every turn** based on the full conversation context, allowing the system to escalate priority as new information emerges.

## 🗺️ Geocoding

The system uses OpenStreetMap Nominatim API for free geocoding:
- Converts text addresses to lat/lng coordinates
- Provides confidence scores (0-100%)
- Results are cached for performance
- Automatically scoped to Kingston, Ontario, Canada (configurable)

## 🛠️ Technology Stack

### Backend
- **Flask** - Web framework
- **Twilio** - Voice/SMS integration
- **Google Gemini** - AI language model
- **Gradium** - Text-to-speech synthesis
- **MongoDB** - Database
- **OpenStreetMap Nominatim** - Geocoding

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **MapLibre GL** - Interactive maps
- **Server-Sent Events** - Real-time updates

## 📁 Project Structure

```
dispatch/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── db.py                  # MongoDB operations
│   ├── events.py              # SSE event broadcasting
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Python dependencies
│   ├── routes/
│   │   └── calls.py          # Call history API
│   ├── services/
│   │   ├── ai.py             # Gemini AI integration
│   │   ├── triage.py         # Call triage logic
│   │   ├── voice.py          # TTS/audio generation
│   │   └── system_prompt.py  # AI prompts
│   └── test/
│       ├── test_calls_api.py # API tests
│       └── run_live_demo.py  # Demo script
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main app component
│   │   ├── api.ts            # API client
│   │   ├── types.ts          # TypeScript types
│   │   ├── components/
│   │   │   ├── CallList.tsx      # Call sidebar
│   │   │   ├── MapPanel.tsx      # Interactive map
│   │   │   └── CallDetailDrawer.tsx  # Call details
│   │   └── colors.ts         # Design system
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
└── README.md                 # This file
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest test/
```

### Run Live Demo

```bash
cd backend
python test/run_live_demo.py
```

### Test with Chat CLI

```bash
cd backend
python test/chat_cli.py
```

## 🚢 Deployment

### Backend Deployment (Railway/Render)

1. Connect your GitHub repository
2. Set environment variables in the platform dashboard
3. Deploy from `backend/` directory
4. Update Twilio webhooks with production URL

### Frontend Deployment (Vercel/Netlify)

1. Connect your GitHub repository
2. Set build command: `npm run build`
3. Set build directory: `frontend/dist`
4. Set environment variable: `VITE_API_BASE_URL=<your-backend-url>`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👥 Authors

- **Your Name** - [GitHub](https://github.com/yourusername) | [LinkedIn](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgments

- Built for QHacks 2025
- Powered by Google Gemini AI
- Voice integration by Twilio
- Maps by MapLibre GL
- TTS by Gradium

## 📧 Contact

For questions or feedback, please reach out:
- Email: your.email@example.com
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- GitHub: [@yourusername](https://github.com/yourusername)

---

**⚠️ Disclaimer**: This is a demonstration project for educational purposes. It is not intended for use in actual emergency services without proper testing, certification, and compliance with local regulations.
