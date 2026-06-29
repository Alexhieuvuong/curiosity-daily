"""
llm.py — one shared OpenAI-compatible chat call (DeepSeek by default), with
retry/backoff. Used by generate.py (daily brief) and weekly_review.py.

Env: API_KEY (required), API_BASE_URL (default https://api.deepseek.com),
API_MODEL (default deepseek-chat).
"""

import os
import time

import requests

MAX_RETRIES = 5
MAX_BACKOFF = 60


def chat(system_prompt, user_prompt, temperature=0.7, max_tokens=8192):
    """Return (content, model). Raises if API_KEY is missing or all retries fail."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")

    base_url = os.environ.get("API_BASE_URL") or "https://api.deepseek.com"
    model = os.environ.get("API_MODEL") or "deepseek-chat"

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    print(f"Calling {model}...")
    result = _post_with_retry(url, headers, payload)
    return result["choices"][0]["message"]["content"].strip(), model


def _post_with_retry(url, headers, payload):
    """POST with backoff, honoring Retry-After on 429/5xx (free models rate-limit)."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                wait = 2 ** attempt
            wait = min(wait, MAX_BACKOFF) + 1
            last_exc = requests.exceptions.HTTPError(
                f"{resp.status_code} from API", response=resp
            )
            if attempt < MAX_RETRIES - 1:
                print(f"  [retry] {resp.status_code} — waiting {wait:.0f}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            raise last_exc
        resp.raise_for_status()
        return resp.json()
    raise last_exc
