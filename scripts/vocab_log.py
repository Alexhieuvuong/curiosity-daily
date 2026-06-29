"""
vocab_log.py — append each day's extracted vocabulary to a cumulative JSONL file.

vocab/vocab.jsonl is the machine-readable source of truth (one JSON object per
line), so it can later be exported to Anki / Quizlet. The human-readable list also
lives inline in each day's brief under "## Vocabulary Builder".
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB_FILE = os.path.join(ROOT, "vocab", "vocab.jsonl")


def append_vocab(entries, topic, date_str):
    """Append vocab rows; returns how many were written. Skips entries without a word."""
    if not entries:
        return 0
    os.makedirs(os.path.dirname(VOCAB_FILE), exist_ok=True)
    written = 0
    with open(VOCAB_FILE, "a", encoding="utf-8") as f:
        for e in entries:
            if not isinstance(e, dict):
                continue
            word = (e.get("word") or "").strip()
            if not word:
                continue
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
