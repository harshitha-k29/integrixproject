"""Groq API integration using plain HTTP (no Groq SDK / pydantic dependency)."""
import os
from pathlib import Path
import requests

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

def _load_local_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and not os.getenv(key):
                os.environ[key] = value

def ask_groq(prompt: str) -> str:
    _load_local_env()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Groq API key not found. Add GROQ_API_KEY to the Integrix/.env file.")
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are Integrix, a careful data-quality assistant. Explain detected issue summaries clearly. Never invent data values or claim a repair was made unless the summary says so. Flag ambiguity."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 900
        },
        timeout=45
    )
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Groq API error ({response.status_code}): {detail}")
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Groq returned an unexpected response: {response.text[:500]}") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Groq returned an empty response. Please try again.")
    return content.strip()
