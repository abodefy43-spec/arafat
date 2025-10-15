# arafat — Flask app (AiSensy WhatsApp integration)

This repository contains a minimal Flask application prepared for deployment on Render. The app includes a small debug endpoint and a test script to send WhatsApp messages via AiSensy.

Files
- `app.py` — main Flask application (includes `/debug/aisensy`).
- `send_test_whatsapp.py` — CLI script to send a single WhatsApp message for testing.
- `requirements.txt` — Python dependencies.
- `runtime.txt` — Python runtime (3.9).
- `Procfile` — Gunicorn entry for Render.
- `.env.example` — example environment variables.

Requirements
- Python 3.9

Local setup
1. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file (or export env vars) with the following values (see `.env.example`):

```
AISENSY_API_KEY=your_aisensy_api_key
AISENSY_API_URL=https://api.aisensy.com/v1/message
SECRET_KEY=replace-with-a-strong-secret
```

3. Run the Flask app locally:

```bash
export FLASK_APP=app.py
export AISENSY_API_KEY="your_key"
export AISENSY_API_URL="https://api.aisensy.com/v1/message"
export SECRET_KEY="your_secret"
flask run --host=127.0.0.1 --port=5000
```

4. Check the AiSensy debug endpoint:

```bash
curl http://127.0.0.1:5000/debug/aisensy
```

Send a test WhatsApp message

Run the test script (make sure env vars are exported in the same shell):

```bash
python3 send_test_whatsapp.py '+971501234567' 'اختبار رسالة'
```

Deployment to Render
1. Create a new Web Service in Render and connect your GitHub repository.
2. Use the `web` service type and set the build command to `pip install -r requirements.txt` (Render does this automatically when requirements.txt exists).
3. Add environment variables in the Render dashboard:
   - AISENSY_API_KEY
   - AISENSY_API_URL
   - SECRET_KEY
4. Deploy. Render will use the `Procfile` to run `gunicorn app:app`.

Security notes
- Do not commit real API keys to source control. Use Render's environment variables or a secrets manager.
- Rotate your AiSensy API key if it was exposed.
# arafat
# arafat
