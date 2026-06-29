"""
weekly_review.py — weekly active-recall vocabulary review.

Pulls the last 7 days of words from vocab/vocab.jsonl, asks the LLM for a cloze
quiz + answer key + a short paragraph that reuses the words (active recall, not
just rereading), appends a canonical word list, then emails it and archives to
weekly/YYYY-Www.md.

Run:  python scripts/weekly_review.py [--dry-run]
Skips if a review for the current ISO week already exists (FORCE_RUN=1 overrides),
so the workflow's twin DST tick never double-posts.
"""

import argparse
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load a local .env for convenient local runs (CI provides env vars directly).
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

from llm import chat  # noqa: E402
from vocab_log import load_recent  # noqa: E402
from email_brief import send_email  # noqa: E402

WEEKLY_DIR = os.path.join(ROOT, "weekly")
DAYS = 7

SYSTEM_PROMPT = """You are a warm, effective English vocabulary coach. You design a \
weekly review that reinforces words through ACTIVE RECALL — making the learner retrieve \
each word from memory, not just reread it. Be encouraging and concise. Output Markdown \
only, no preamble."""


def _build_prompt(rows, start_s, end_s):
    words_block = "\n".join(
        f"- {r['word']} ({r.get('pos', '')}): {r.get('definition', '')}" for r in rows
    )
    return f"""Here are this week's {len(rows)} vocabulary words ({start_s} to {end_s}):

{words_block}

Write a review with EXACTLY these sections, in this order, in Markdown:

## This week in a nutshell
<1–2 encouraging sentences noting how many words and the date span.>

## Active recall quiz
<For EACH word, write ONE new fill-in-the-blank sentence in a DIFFERENT context than a \
plain dictionary example, with the target word replaced by "______". Number them 1..N. \
Never reveal the target word inside its own sentence.>

## Answer key
<A numbered list matching the quiz, giving the word for each blank.>

## Connect the dots
<One short paragraph (4–7 sentences) that naturally weaves in as many of these words as \
possible in a single coherent scene or argument. **Bold** each target word where it \
appears.>"""


def _reference(rows):
    lines = ["## This week's words (reference)", ""]
    for r in rows:
        ipa = f" {r['ipa']}" if r.get("ipa") else ""
        pos = f" *({r['pos']})*" if r.get("pos") else ""
        lines.append(f"- **{r['word']}**{ipa}{pos} — {r.get('definition', '')}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Weekly vocabulary review digest.")
    ap.add_argument("--dry-run", action="store_true",
                    help="generate and print only; do not save or email")
    args = ap.parse_args()

    rows = load_recent(DAYS)
    if not rows:
        print("No vocabulary logged in the last 7 days — nothing to review.")
        return

    iso = date.today().isocalendar()
    week_id = f"{iso.year}-W{iso.week:02d}"
    end = date.today()
    start = end - timedelta(days=DAYS - 1)
    start_s, end_s = start.isoformat(), end.isoformat()
    path = os.path.join(WEEKLY_DIR, f"{week_id}.md")

    force = os.environ.get("FORCE_RUN") == "1"
    if not args.dry_run and not force and os.path.exists(path):
        print(f"Weekly review {week_id} already exists — skipping.")
        return

    print(f"Reviewing {len(rows)} words for {week_id} ({start_s} → {end_s})")

    header = (f"# \U0001F4DA Weekly Vocab Review · {week_id}\n\n"
              f"> {len(rows)} words from {start_s} to {end_s}.\n")
    try:
        review, model = chat(SYSTEM_PROMPT, _build_prompt(rows, start_s, end_s),
                             temperature=0.7)
        footer = f"\n\n---\n*Curiosity Daily · weekly review · generated with {model}*\n"
    except Exception as e:  # never fail the run over the quiz — fall back to the list
        print(f"[warn] LLM review failed ({e}); sending plain word list.")
        review = "_(Automated quiz unavailable this week — here are your words to review.)_"
        footer = "\n\n---\n*Curiosity Daily · weekly review*\n"

    body = f"{header}\n{review}\n\n{_reference(rows)}{footer}"

    if args.dry_run:
        print("\n" + "=" * 70 + "\n")
        print(body)
        print("\n[dry-run] not saving or emailing.")
        return

    os.makedirs(WEEKLY_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved {path}")

    send_email(f"\U0001F4DA Weekly Vocab Review · {len(rows)} words", body)
    print("Done.")


if __name__ == "__main__":
    main()
