from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # Vite dev server

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Backend connected"})

@app.route("/api")
def index():
    return jsonify({"message": "Dispatch API"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
