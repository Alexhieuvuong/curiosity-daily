"""
vocab_log.py — append each day's extracted vocabulary to a cumulative JSONL file.

vocab/vocab.jsonl is the machine-readable source of truth (one JSON object per
line), so it can later be exported to Anki / Quizlet. The human-readable list also
lives inline in each day's brief under "## Vocabulary Builder".
"""

import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_FILE = os.path.join(ROOT, "vocab", "vocab.jsonl")


def _existing_words_for_date(date_str):
    """Set of lowercased words already logged for date_str, so a rerun (FORCE_RUN, or
    a second cron tick that slips past the daily guard) doesn't double-log them."""
    existing = set()
    if not os.path.exists(VOCAB_FILE):
        return existing
    with open(VOCAB_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("date") == date_str:
                existing.add((row.get("word") or "").strip().lower())
    return existing


def append_vocab(entries, topic, date_str):
    """Append vocab rows; returns how many were written. Skips entries without a word
    and any word already logged for this date (dedup across reruns)."""
    if not entries:
        return 0
    os.makedirs(os.path.dirname(VOCAB_FILE), exist_ok=True)
    seen_today = _existing_words_for_date(date_str)
    written = 0
    with open(VOCAB_FILE, "a", encoding="utf-8") as f:
        for e in entries:
            if not isinstance(e, dict):
                continue
            word = (e.get("word") or "").strip()
            if not word:
                continue
            key = word.lower()
            if key in seen_today:  # already logged today — skip the duplicate
                continue
            seen_today.add(key)
            row = {
                "date": date_str,
                "topic": topic,
                "word": word,
                "pos": (e.get("pos") or "").strip(),
                "ipa": (e.get("ipa") or "").strip(),
                "definition": (e.get("definition") or "").strip(),
                "example": (e.get("example") or "").strip(),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
    return written


def load_recent(days):
    """Vocab rows from the last `days` days (inclusive of today), deduped by word.

    ISO date strings (YYYY-MM-DD) sort lexically, so a string >= comparison is a
    correct date filter. Keeps the first occurrence of each word.
    """
    if not os.path.exists(VOCAB_FILE):
        return []
    cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
    seen_words = set()
    out = []
    with open(VOCAB_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("date", "") < cutoff:
                continue
            key = (row.get("word") or "").strip().lower()
            if not key or key in seen_words:
                continue
            seen_words.add(key)
            out.append(row)
    return out
