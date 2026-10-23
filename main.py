"""Sofia backend: safety layer + Claude conversation + static frontend."""
import os
import re
from pathlib import Path
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
MODEL = os.getenv("SOFIA_MODEL", "claude-sonnet-5-5")
client = Anthropic()  
BASE = Path(__file__).parent

app = FastAPI(title="Sofia")


CRISIS_PATTERNS = [
    r"\bkill (myself|me)\b",
    r"\bsuicid(e|al)\b",
    r"\bend (my|this) life\b",
    r"\bend it all\b",
    r"\bwant(ed)? to die\b",
    r"\bwish i (was|were) dead\b",
    r"\bdon'?t want to (live|be alive|be here)\b",
    r"\bno reason to live\b",
    r"\b(self[- ]?harm|hurt myself|harm myself|cut myself)\b",
    r"\bbetter off (dead|without me)\b",
]
CRISIS_RE = re.compile("|".join(CRISIS_PATTERNS), re.IGNORECASE)

CRISIS_REPLY = (
    "I'm really glad you told me, and I'm concerned about you. "
    "Please reach out to someone right now. In India you can call or text "
    "Tele-MANAS at 14416, free and available at any hour, or call 112 if you "
    "are in immediate danger. If you're elsewhere, please call your local "
    "emergency number. If someone you trust is nearby, please go be with them "
    "or ask them to stay with you. I'm here with you while you do that."
)

SYSTEM_PROMPT = """You are Sofia, a warm, emotionally aware voice companion and personal assistant.

Style:
- You are spoken aloud, so keep replies short: 1 to 3 sentences, plain words, no lists, no markdown, no emojis.
- Be gentle, curious, and natural. Ask at most one question at a time.
- Help with everyday things too (reminders, planning, questions, small talk).

Emotional awareness:
- You may receive a soft camera signal about the user's facial expression. It is unreliable. Never state it as fact and never tell the user they are depressed, anxious, or ill.
- If it seems relevant, check in gently and ask permission, for example "You seem a bit tense, want to talk about it?" Otherwise ignore it.
- You can offer simple tools: slow breathing, grounding (name five things you can see), a short journaling prompt, or reframing a worry.

Boundaries:
- You are a wellness companion, not a doctor, therapist, or psychiatrist. Never diagnose, never suggest medication, and never claim to treat anything.
- If someone seems to be struggling for days or weeks, kindly encourage them to talk to a trusted person or a licensed professional.
- If the user expresses thoughts of suicide, self-harm, or being in danger, reply with exactly [[CRISIS]] and nothing else.
- Do not encourage the user to depend on you alone. Support their real-life connections."""


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    emotion: str | None = Field(default=None, max_length=300)
    history: list[Turn] = []


def is_crisis(text: str) -> bool:
    return bool(CRISIS_RE.search(text))


@app.post("/api/chat")
def chat(body: ChatIn):
   
    if is_crisis(body.message):
        return {"reply": CRISIS_REPLY, "crisis": True}

    system = SYSTEM_PROMPT
    if body.emotion:
        system += f"\n\nCamera signal (soft, may be wrong, user consented): {body.emotion}."

    messages = [t.model_dump() for t in body.history[-10:]]
    messages.append({"role": "user", "content": body.message})
    while messages and messages[0]["role"] != "user":
        messages.pop(0)

    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=300, system=system, messages=messages
        )
    except Exception as exc:  
        print("Claude API error:", exc)
        return {
            "reply": "I'm having trouble connecting right now. Please try again in a moment.",
            "crisis": False,
            "error": True,
        }

    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    
    if text.startswith("[[CRISIS]]"):
        return {"reply": CRISIS_REPLY, "crisis": True}

    return {"reply": text, "crisis": False}


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
