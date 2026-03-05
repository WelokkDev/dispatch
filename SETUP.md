# 🛠️ Quick Setup Guide

This guide will help you get Dispatch running locally in under 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.8 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] Git installed
- [ ] Code editor (VS Code recommended)

## Step-by-Step Setup

### 1️⃣ Clone and Navigate

```bash
git clone https://github.com/yourusername/dispatch.git
cd dispatch
```

### 2️⃣ Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.sample .env
```

**Edit `backend/.env`** and add your API keys:

```env
GEMINI_API_KEY=your_key_here          # Get from https://aistudio.google.com/app/apikey
GRADIUM_API_KEY=your_key_here         # Get from https://gradium.ai
TWILIO_ACCOUNT_SID=your_sid_here      # Get from https://console.twilio.com/
TWILIO_AUTH_TOKEN=your_token_here     # Get from https://console.twilio.com/
MONGODB_URI=your_mongodb_uri_here     # Get from https://cloud.mongodb.com/
```

### 3️⃣ Frontend Setup (2 minutes)

```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.sample .env
```

**Edit `frontend/.env`**:

```env
VITE_API_BASE_URL=http://127.0.0.1:5001
```

### 4️⃣ Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python app.py
```

You should see:
```
============================================================
  [Dev] Dispatch backend starting on http://localhost:5001
  (If using Twilio locally, use ngrok and point webhooks to /voice)
============================================================
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v7.2.4  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 5️⃣ Open the Application

Open your browser and navigate to:
```
http://localhost:5173
```

You should see the Dispatch dashboard with a map and call list!

## 🧪 Test the System

### Option A: Text-Based Testing (No Phone Required)

Use the chat API to simulate a call:

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-001",
    "message": "There is a fire at 123 Main Street"
  }'
```

You should see the call appear in the dashboard immediately!

### Option B: Phone Testing (Requires Twilio Setup)

1. **Install ngrok** (if not already installed):
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Expose your local backend**:
   ```bash
   ngrok http 5001
   ```
   
   Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

3. **Configure Twilio**:
   - Go to https://console.twilio.com/
   - Navigate to Phone Numbers → Your Twilio number
   - Under "Voice Configuration":
     - Set "A CALL COMES IN" to: `https://your-ngrok-url.ngrok.io/voice`
     - Set method to `HTTP POST`
   - Save

4. **Call your Twilio number** and speak to the AI dispatcher!

## 🎯 Getting API Keys

### Google Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key to your `.env` file

### Gradium API Key
1. Sign up at https://gradium.ai
2. Navigate to API Keys section
3. Create a new API key
4. Copy both the API key and Voice ID to your `.env` file

### Twilio Credentials
1. Sign up at https://www.twilio.com/try-twilio
2. Get $15 free credit for testing
3. Go to https://console.twilio.com/
4. Copy Account SID and Auth Token to your `.env` file
5. Get a phone number (free with trial)

### MongoDB URI
1. Sign up at https://cloud.mongodb.com/
2. Create a free cluster (M0 Sandbox)
3. Create a database user
4. Get connection string and add to your `.env` file

## ❓ Troubleshooting

### Backend won't start

**Error: `ModuleNotFoundError`**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: `Port 5001 already in use`**
```bash
# Change port in backend/.env
PORT=5002

# Update frontend/.env to match
VITE_API_BASE_URL=http://127.0.0.1:5002
```

### Frontend won't start

**Error: `Cannot find module`**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database connection issues

**Error: `MongoServerError: Authentication failed`**
- Check your MongoDB URI in `.env`
- Ensure database user has correct permissions
- Verify IP whitelist includes your IP (or use 0.0.0.0/0 for testing)

### API calls failing

**Error: `Failed to load calls`**
1. Check backend is running on port 5001
2. Check `VITE_API_BASE_URL` in `frontend/.env`
3. Check browser console for CORS errors
4. Verify MongoDB connection

## 🎉 Success!

If everything is working, you should see:
- ✅ Backend running on http://localhost:5001
- ✅ Frontend running on http://localhost:5173
- ✅ Dashboard loads with map
- ✅ Test API call creates a new call entry
- ✅ Real-time updates appear instantly

## 📚 Next Steps

- Read the [README.md](README.md) for full documentation
- Check out the API endpoints at http://localhost:5001/api
- Try the live demo script: `python backend/test/run_live_demo.py`
- Set up Twilio for real phone call testing

## 💬 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Review the code comments in `backend/app.py` and `frontend/src/App.tsx`

---

**Happy Dispatching!** 🚨
