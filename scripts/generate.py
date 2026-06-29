"""
generate.py — produce one daily curiosity brief + vocabulary list via an
OpenAI-compatible chat API (DeepSeek by default; Claude via OpenRouter also works).

Reuses the retry/backoff pattern from ai-daily-digest/scripts/summarize.py.

The model returns:
  TOPIC: <specific title>          (first line — parsed for filename/state)
  # <title> ... full English brief ... ## Vocabulary Builder ...
  ```json [ {word, pos, ipa, definition, example}, ... ] ```   (machine-readable)

generate() returns (topic_title, body_markdown, vocab_list). The trailing JSON
block is stripped from the saved/emailed body; the human-readable Vocabulary
Builder section stays in the brief.
"""

import json
import os
import re
import time

import requests

MAX_RETRIES = 5
MAX_BACKOFF = 60


SYSTEM_PROMPT = """You are a brilliant, curious explainer — part economist, part \
investigative journalist, part patient teacher. You write a short daily brief whose job \
is to spark genuine curiosity and teach the reader HOW to think about a topic, not just \
hand them facts.

Your style:
- Concrete, vivid, and intellectually honest. No fluff, no hype, no padding.
- You "tear a problem into pieces": expose the underlying mechanic, follow the incentives \
(who pays, who profits), and trace second-order effects.
- You leave the reader with one genuinely open question — a loose end that keeps them \
thinking after they close the email.
- You write in clear English at an advanced-but-readable level, deliberately using some \
precise, useful vocabulary (a learner is reading this to grow their English).
- Never fabricate specific statistics, dates, or names you are unsure of; reason from \
mechanisms and clearly mark illustrative examples as such."""


def _build_user_prompt(area, recent_topics, date_str):
    recent_block = "\n".join(f"- {t}" for t in recent_topics) or "(none yet — this is an early day)"
    return f"""Today is {date_str}. The reader's broad interest area for today is:

  **{area}**

Choose ONE specific, sharp, curiosity-sparking angle within or adjacent to that area —
something narrow enough to dig into deeply (a single mechanism, market, tension, or
puzzle), not a broad survey. It MUST be clearly different from every topic already
covered:

Already covered (do NOT repeat or closely overlap):
{recent_block}

Then write the brief in EXACTLY this structure and order, in Markdown:

TOPIC: <a short, specific title — just the title text, on the very first line>

# <the same title>

> <one-line hook that makes the reader curious>

## Why this is interesting
<2–4 sentences>

## The core mechanic
<how it actually works, plainly — the gears under the hood>

## Break it into pieces
<3–5 bullet points: the sub-questions or tensions worth pulling apart>

## Follow the incentives
<who pays, who profits, who bears the risk — and why they each act as they do>

## Second-order effects
<the non-obvious downstream consequences, intended or not>

## A question to sit with
<ONE genuinely open question, left deliberately unresolved>

## Go deeper
<2–3 concrete threads, examples, or cases the reader could explore or discuss next>

## Vocabulary Builder
<8–12 useful or advanced words/phrases that appear in (or are natural to) this brief.
Format each as a numbered list item exactly like:
1. **word** — (part of speech, /IPA/) — concise definition. _Example: a sentence using it in this topic's context._>

Finally, AFTER the brief, output the SAME vocabulary as a single fenced JSON code block
(this is parsed by a program — keep keys exactly as shown, valid JSON, no comments):

```json
[
  {{"word": "...", "pos": "...", "ipa": "...", "definition": "...", "example": "..."}}
]
```"""


def generate(area, recent_topics, date_str):
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")

    base_url = os.environ.get("API_BASE_URL") or "https://api.deepseek.com"
    model = os.environ.get("API_MODEL") or "deepseek-chat"

    user_prompt = _build_user_prompt(area, recent_topics, date_str)

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,  # higher than the news digest — we want creative topic variety
        "max_tokens": 8192,
    }

    print(f"Calling {model}...")
    result = _post_with_retry(url, headers, payload)
    text = result["choices"][0]["message"]["content"].strip()
    return _parse(text, model, date_str)


def _parse(text, model, date_str):
    """Split model output into (topic, body_markdown, vocab_list)."""
    topic = "Untitled"
    lines = text.splitlines()
    if lines and lines[0].strip().upper().startswith("TOPIC:"):
        topic = lines[0].split(":", 1)[1].strip() or topic
        text = "\n".join(lines[1:]).strip()

    # Pull out the trailing machine-readable JSON block and remove it from the body.
    vocab = []
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, list):
                vocab = parsed
        except json.JSONDecodeError:
            print("  [warn] could not parse vocab JSON block — skipping vocab log.")
        text = text[: m.start()].rstrip()

    body = f"{text}\n\n---\n*Curiosity Daily · {date_str} · generated with {model}*\n"
    return topic, body, vocab


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
