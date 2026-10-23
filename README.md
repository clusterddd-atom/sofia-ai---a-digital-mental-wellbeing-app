# Sofia

Voice companion that reads facial expression signals on-device and talks back.
Prototype: FastAPI backend + browser frontend (MediaPipe, Web Speech API, Claude API).

## Run it

```bash
cd sofia
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then put your ANTHROPIC_API_KEY in .env
uvicorn main:app --reload
```

In Windows PowerShell, use `Copy-Item .env.example .env` to create the local
configuration file, then edit `.env` and set `ANTHROPIC_API_KEY` there. Keep the
key out of chat messages and source control.

Open http://localhost:8000 in **Chrome or Edge** (voice input needs them).
Camera and mic only work on `localhost` or HTTPS.

## How it works

- `static/index.html`: consent screen, camera + MediaPipe face blendshapes (on-device),
  rule-based expression label, speech-to-text, text-to-speech, chat, mood check-ins,
  breathing tool, delete-my-data. Mood log lives in the browser's localStorage.
  Speech output prefers an available female-coded English voice (favoring en-IN);
  available voices depend on the browser and operating system.
- `main.py`: `/api/chat`. A keyword safety check runs first and returns a fixed
  crisis reply with helplines. Otherwise the message, a short emotion hint, and recent
  history go to Claude. If the model replies `[[CRISIS]]`, the fixed reply is used.

## Before real users

1. Have a psychologist or psychiatrist review the system prompt, crisis keywords and replies.
2. Test the crisis flow in many phrasings and languages (Tamil, Hindi, Tanglish).
3. Replace the rule-based expression heuristic with a trained model and test across
   skin tones, lighting, glasses and masks.
4. Add HTTPS hosting, rate limiting, usage caps and monitoring.
5. Write a privacy policy; check DPDP Act requirements with a lawyer.
6. Keep wording wellness-only: no "diagnose", "treat" or "therapy" claims.

## Next steps

Wrap as a mobile app (Capacitor or Flutter WebView), swap Web Speech for Whisper for
better accuracy, add accounts, and add a human counsellor handoff.
