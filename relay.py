# relay.py
import os
import logging
from flask import Flask, request, jsonify, abort
import requests
from urllib.parse import urljoin

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Required env vars
AISENSY_API_KEY = os.getenv("AISENSY_API_KEY", "")
AISENSY_API_URL = os.getenv("AISENSY_API_URL", "https://api.aisensy.com/v1/message")

# Optional simple auth token for the relay endpoint
RELAY_SECRET = os.getenv("RELAY_SECRET", "")  # set to a random string in Render env

if not AISENSY_API_KEY:
    app.logger.warning("AISENSY_API_KEY not set. Relay will not send messages until it's configured.")

@app.route("/")
def home():
    return (
        "AiSensy relay running. POST /relay with JSON {to, type, text:{body}} "
        "and header X-Relay-Auth: <RELAY_SECRET> (if set)."
    )

def forward_to_aisensy(payload: dict) -> (int, str):
    headers = {
        "Authorization": f"Bearer {AISENSY_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(AISENSY_API_URL, json=payload, headers=headers, timeout=15)
        return resp.status_code, resp.text
    except requests.RequestException as e:
        app.logger.exception("Error sending to AiSensy")
        return 503, str(e)

@app.route("/relay", methods=["POST"])
def relay():
    # Optional: validate secret header
    if RELAY_SECRET:
        secret = request.headers.get("X-Relay-Auth", "")
        if secret != RELAY_SECRET:
            abort(401, description="Unauthorized: invalid relay secret")

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400

    # Basic validation: expect { to, type, text:{ body } } as AiSensy expects
    to = data.get("to")
    typ = data.get("type")
    text = data.get("text")
    if not to or not typ or not text or not isinstance(text, dict) or "body" not in text:
        return jsonify({"error": "missing fields, expected to,type,text{body}"}), 400

    # Optional: normalize phone number (basic)
    # AiSensy likely expects international format; ensure + prefix.
    if isinstance(to, str) and not to.startswith("+"):
        # If number starts with 0 and local (e.g. 05...), user must provide correct intl format.
        # We will not attempt unsafe guessing; just return an error.
        return jsonify({"error": "phone must be in international format starting with +"}), 400

    payload = {"to": to, "type": typ, "text": text}

    # Forward to AiSensy
    status, body = forward_to_aisensy(payload)
    app.logger.info("Forwarded to AiSensy: status=%s, to=%s", status, to)
    return (body, status, {"Content-Type": "application/json"})

# Small debug endpoint (safe when protected by RELAY_SECRET)
@app.route("/debug/health")
def health():
    return jsonify({
        "relay": True,
        "aisensy_key_present": bool(AISENSY_API_KEY),
        "aisensy_url": AISENSY_API_URL
    })

if __name__ == "__main__":
    # For local testing only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
