from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import requests

# --- Flask setup ---
app = Flask(__name__)

# Secret key
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret')

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# --- Database Model Example ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pickup = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(120), nullable=False)

# --- Home Route ---
@app.route('/')
def index():
    return "Flask app running! Use /echo to test or /relay to send WhatsApp messages."

# --- ECHO Test Route ---
@app.route('/echo', methods=['POST'])
def echo():
    """
    Simple echo route for testing.
    Sends back whatever JSON you send to it.
    """
    data = request.get_json(force=True, silent=True) or {}
    return jsonify({"you_sent": data, "status": "ok"})

# --- Debug Route to check AiSensy config ---
@app.route('/debug/aisensy', methods=['GET'])
def debug_aisensy():
    api_url = os.getenv('AISENSY_API_URL')
    api_key = os.getenv('AISENSY_API_KEY')
    return jsonify({
        "aisensy_api_url": api_url,
        "aisensy_api_key_present": bool(api_key)
    })

# --- Relay Route to send WhatsApp message ---
@app.route('/relay', methods=['POST'])
def relay_message():
    """
    Forwards a WhatsApp message to AiSensy API.
    Example POST JSON:
    {
        "to": "+971501234567",
        "type": "text",
        "text": {"body": "Hello!"}
    }
    """
    api_url = os.getenv('AISENSY_API_URL')
    api_key = os.getenv('AISENSY_API_KEY')
    if not api_url or not api_key:
        return jsonify({"error": "Missing AiSensy configuration"}), 500

    data = request.get_json(force=True, silent=True) or {}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(api_url, headers=headers, json=data, timeout=10)
        return jsonify({
            "status_code": resp.status_code,
            "response": resp.text
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- Run the app ---
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
