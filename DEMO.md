# 🎬 Demo Guide

This guide provides ready-to-use demo scenarios for showcasing Dispatch.

## Quick Demo Setup

### 1. Start the System

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
python app.py

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### 2. Open Dashboard

Navigate to: http://localhost:5173

## Demo Scenarios

### Scenario 1: High Priority Emergency (P0)

**Situation**: Cardiac arrest - immediate life threat

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p0-001",
    "message": "My husband is not breathing! He collapsed on the floor!"
  }'
```

**Expected Behavior**:
- ✅ Call appears immediately on dashboard
- ✅ Priority: P1 (red)
- ✅ AI extracts emergency type: "cardiac arrest" or "not breathing"
- ✅ System asks for location
- ✅ Quick transfer to human operator

**Follow-up message**:
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p0-001",
    "message": "123 Main Street, Kingston"
  }'
```

### Scenario 2: Urgent Emergency (P1)

**Situation**: House fire with people inside

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p1-001",
    "message": "There is a fire in my house! I can see smoke coming from the kitchen!"
  }'
```

**Expected Behavior**:
- ✅ Priority: P1 or P2 (red/orange)
- ✅ AI asks for location
- ✅ Collects emergency type and location
- ✅ Transfers to operator after key info collected

**Complete the scenario**:
```bash
# Location
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p1-001",
    "message": "456 Oak Avenue, apartment 3B"
  }'
```

### Scenario 3: Moderate Emergency (P2)

**Situation**: Car accident with minor injuries

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p2-001",
    "message": "I just got into a car accident. My car hit another vehicle at the intersection."
  }'
```

**Expected Behavior**:
- ✅ Priority: P2 or P3 (orange/yellow)
- ✅ AI collects full information: emergency, location, name, phone
- ✅ Natural conversation flow
- ✅ Call completes after all info collected

**Complete conversation**:
```bash
# Location
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p2-001",
    "message": "Corner of Princess Street and Division Street"
  }'

# Name
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p2-001",
    "message": "My name is John Smith"
  }'

# Phone
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p2-001",
    "message": "My number is 613-555-0123"
  }'

# Follow-up question
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p2-001",
    "message": "Yes, I have a cut on my forehead but I am okay"
  }'
```

### Scenario 4: Low Priority (P3)

**Situation**: Noise complaint

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "demo-p3-001",
    "message": "I want to report a noise complaint. My neighbors are being very loud."
  }'
```

**Expected Behavior**:
- ✅ Priority: P3 or P4 (yellow/blue)
- ✅ Full information collection
- ✅ Multiple follow-up questions
- ✅ Natural completion

### Scenario 5: Multiple Simultaneous Calls

**Demonstrate real-time capabilities**:

```bash
# Call 1: Medical emergency
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"call_id": "demo-multi-001", "message": "My mother fell down the stairs"}' &

# Call 2: Fire
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"call_id": "demo-multi-002", "message": "There is a fire at 789 Elm Street"}' &

# Call 3: Burglary
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"call_id": "demo-multi-003", "message": "Someone broke into my house"}' &

wait
```

**Expected Behavior**:
- ✅ All three calls appear simultaneously
- ✅ Different priorities and colors
- ✅ Map shows multiple markers
- ✅ Real-time updates for all calls

## Demo Script for Presentations

### Introduction (1 minute)

> "Dispatch is an AI-powered 911 call system that automatically triages emergency calls, extracts critical information, and provides dispatchers with real-time visualization. Let me show you how it works."

### Demo Flow (3-5 minutes)

**1. Show the Dashboard** (30 seconds)
- Point out the call list, map, and real-time features
- Highlight the clean, professional UI

**2. Simulate a High-Priority Call** (1 minute)
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "live-demo-001",
    "message": "Help! My house is on fire and I am trapped inside!"
  }'
```

- Watch the call appear in real-time
- Point out the priority indicator (red for P1)
- Show the live transcript updating
- Highlight the AI's response

**3. Provide Location** (30 seconds)
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "live-demo-001",
    "message": "I am at 100 Queen Street in Kingston"
  }'
```

- Watch the map update with a marker
- Point out the geocoding and confidence score
- Show the location label in the call details

**4. Show Call Details** (30 seconds)
- Click on the call in the list
- Show the detailed drawer with full transcript
- Highlight the extracted information (emergency type, location, priority)
- Point out the AI-generated summary (if available)

**5. Demonstrate Multiple Calls** (1 minute)
- Run the multiple simultaneous calls scenario
- Show how the system handles multiple calls at once
- Highlight the map with multiple markers
- Show different priority levels

**6. Explain Key Features** (1 minute)
- AI triage with dynamic priority assessment
- Real-time updates via Server-Sent Events
- Automatic geocoding and mapping
- Voice integration with Twilio (mention but don't demo)
- Persistent storage with MongoDB

### Closing (30 seconds)

> "This system can handle real phone calls through Twilio, supports multiple simultaneous emergencies, and provides dispatchers with all the critical information they need to respond effectively. It's built with modern technologies like React, Flask, and Google Gemini AI."

## Testing the Voice System (Optional)

If you have Twilio set up and want to demo actual phone calls:

### 1. Start ngrok

```bash
ngrok http 5001
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 2. Update Twilio Webhook

Go to your Twilio console and set:
- Voice URL: `https://your-ngrok-url.ngrok.io/voice`

### 3. Call Your Twilio Number

Speak naturally:
- "There's a fire at my house on Main Street"
- "I need an ambulance, someone is having a heart attack"
- "I want to report a car accident"

### 4. Watch the Dashboard

The call will appear in real-time with live transcription!

## Tips for a Great Demo

### Before the Demo

- [ ] Clear any test data from previous demos
- [ ] Ensure backend and frontend are running
- [ ] Have the dashboard open and visible
- [ ] Test your curl commands beforehand
- [ ] Prepare your demo script

### During the Demo

- ✅ Speak clearly and confidently
- ✅ Point out features as they happen
- ✅ Highlight the real-time nature
- ✅ Show the clean, professional UI
- ✅ Mention the technology stack

### After the Demo

- 📊 Show the code structure (optional)
- 🔗 Share the GitHub repository
- 💬 Answer questions
- 📧 Provide contact information

## Troubleshooting Demo Issues

### Calls not appearing

```bash
# Check backend is running
curl http://localhost:5001/api/health

# Check SSE connection
curl http://localhost:5001/api/events
```

### Map not showing markers

- Ensure location is a valid address
- Check browser console for errors
- Verify geocoding is working (check backend logs)

### Real-time updates not working

- Check browser console for SSE errors
- Ensure CORS is enabled
- Verify backend SSE endpoint is accessible

## Demo Data Cleanup

To clear demo data and start fresh:

```bash
# Clear in-memory calls (restart backend)
# Or use MongoDB to clear the calls collection

# If using MongoDB:
# mongosh "your-connection-string"
# use dispatch
# db.calls.deleteMany({})
```

## Advanced Demo Features

### Show the Code

If you have time, show key files:
- `backend/app.py` - Main application logic
- `backend/services/triage.py` - AI triage system
- `frontend/src/App.tsx` - React dashboard
- `frontend/src/components/MapPanel.tsx` - Map component

### Explain the Architecture

```
Phone Call → Twilio → Flask Backend → Gemini AI → Response
                            ↓
                        MongoDB (Storage)
                            ↓
                    React Frontend (SSE) → Live Dashboard
```

### Highlight Technical Achievements

- Real-time bidirectional communication
- AI-powered natural language understanding
- Production-ready voice integration
- Scalable architecture
- Modern tech stack

---

**Good luck with your demo! 🚀**
