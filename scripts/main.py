"""
main.py — Curiosity Daily orchestrator.

Flow:
  1. Load interest areas + already-covered topics (state).
  2. Pick a fresh broad area, gather recent topic titles to avoid repeats.
  3. Generate one English brief + vocabulary via DeepSeek (generate.py).
  4. Save the brief to daily/YYYY-MM-DD-<slug>.md.
  5. Append the day's words to vocab/vocab.jsonl.
  6. Record the topic in data/seen_topics.json.
  7. Email the brief via Resend.

Run:  python scripts/main.py            (full run)
      python scripts/main.py --dry-run  (generate & print only; no save/email/state)

A run is skipped if a topic was already generated today, so the twin-cron's second
tick never double-posts. Set FORCE_RUN=1 (workflow_dispatch does this) to override.
"""

import argparse
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load a local .env for convenient local runs (CI provides env vars directly).
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

from topics import (  # noqa: E402  (import after dotenv load is intentional)
    load_interests, load_seen, already_done_today, recent_topic_titles,
    pick_area, append_seen, slugify, today_str,
)
from generate import generate  # noqa: E402
from vocab_log import append_vocab  # noqa: E402
from email_brief import send_email  # noqa: E402

DAILY_DIR = os.path.join(ROOT, "daily")


def main():
    ap = argparse.ArgumentParser(description="Generate the daily curiosity brief.")
    ap.add_argument("--dry-run", action="store_true",
                    help="generate and print only; do not save, email, or update state")
    args = ap.parse_args()

    date_str = today_str()
    areas = load_interests()
    seen = load_seen()

    force = os.environ.get("FORCE_RUN") == "1"
    if not args.dry_run and not force and already_done_today(seen, date_str):
        print(f"Already generated a topic for {date_str} — skipping.")
        return

    area = pick_area(areas, seen)
    recent = recent_topic_titles(seen, 30)
    print(f"Area: {area}")

    topic, body, vocab = generate(area, recent, date_str)
    print(f"Topic: {topic}  ({len(vocab)} vocab words)")

    if args.dry_run:
        print("\n" + "=" * 70 + "\n")
        print(body)
        print("\n[dry-run] not saving, emailing, or updating state.")
        return

    os.makedirs(DAILY_DIR, exist_ok=True)
    path = os.path.join(DAILY_DIR, f"{date_str}-{slugify(topic)}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {path}")

    n = append_vocab(vocab, topic, date_str)
    print(f"Logged {n} vocab words to vocab/vocab.jsonl")

    append_seen(seen, topic, area, date_str)

    send_email(f"\U0001F9E0 Curiosity Daily · {topic}", body)
    print("Done.")


if __name__ == "__main__":
    main()
