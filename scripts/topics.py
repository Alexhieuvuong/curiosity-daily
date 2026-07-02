"""
topics.py — pick the day's interest area and track covered topics so nothing repeats.

State lives in data/seen_topics.json as a list of
  {"date": "YYYY-MM-DD", "area": "<broad area>", "topic": "<specific title>"}
committed back to the repo by the GitHub Actions workflow.
"""

import json
import os
import random
import re
import unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERESTS_FILE = os.path.join(ROOT, "interests.txt")
SEEN_FILE = os.path.join(ROOT, "data", "seen_topics.json")


def load_interests():
    """Read interests.txt — one broad area per line; '#' lines and blanks ignored."""
    with open(INTERESTS_FILE, encoding="utf-8") as f:
        areas = [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    if not areas:
        raise ValueError("interests.txt is empty — add at least one interest area.")
    return areas


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def already_done_today(seen, date_str):
    """True if a topic was already generated today (guards the twin-cron second tick)."""
    return any(e.get("date") == date_str for e in seen)


def recent_topic_titles(seen, n=30):
    return [e["topic"] for e in seen[-n:] if e.get("topic")]


def pick_area(areas, seen):
    """Random area, de-weighting ones used in the most recent rounds for variety."""
    window = min(len(areas) - 1, len(seen)) if len(areas) > 1 else 0
    recent_areas = {e.get("area") for e in seen[-window:]} if window else set()
    fresh = [a for a in areas if a not in recent_areas]
    return random.choice(fresh or areas)


def append_seen(seen, topic, area, date_str):
    seen.append({"date": date_str, "area": area, "topic": topic})
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    # Write to a temp file then atomically replace, so a crash mid-write can never
    # leave data/seen_topics.json truncated or half-written (which would break the
    # next run's json.load and lose all topic history).
    tmp = SEEN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SEEN_FILE)
    return seen


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60] or "topic"


# Convenience for callers that just want today's ISO date in one place.
def today_str():
    return date.today().isoformat()
