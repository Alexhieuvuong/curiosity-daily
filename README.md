# Curiosity Daily

One curiosity-sparking topic every morning — generated, not scraped — written to make you
think, plus a vocabulary builder so the habit grows your English over time.

Each day the tool picks a broad interest area from `interests.txt`, asks an LLM (DeepSeek by
default) for a **fresh, specific angle** it hasn't covered before, and writes an English
brief that *tears the topic into pieces*: the core mechanic, who pays and who profits, the
second-order effects, and one open question left deliberately unresolved. It then extracts
8–12 useful words into a cumulative vocabulary log, emails you the brief, and archives it.

## What you get each morning
- An email (via Resend) with the day's brief.
- A dated archive file: `daily/YYYY-MM-DD-<topic-slug>.md`.
- New words appended to `vocab/vocab.jsonl` (one JSON row per word — Anki/Quizlet friendly).

## Brief structure
Why this is interesting → The core mechanic → Break it into pieces → Follow the incentives →
Second-order effects → A question to sit with → Go deeper → **Vocabulary Builder**.

The "Go deeper" threads and the open question are good prompts to then discuss with Claude.

## Setup
1. `pip install -r requirements.txt`
2. `cp .env.example .env` and fill in `API_KEY` (DeepSeek) and `RESEND_API_KEY` (Resend).
3. Edit `interests.txt` to taste.

## Run
```bash
python scripts/main.py --dry-run   # generate & print only — no save/email/state
python scripts/main.py             # full run: save + log vocab + email + record topic
```
A run is skipped if a topic was already generated today (set `FORCE_RUN=1` to override).

## Daily automation (GitHub Actions)
`.github/workflows/daily.yml` runs once each morning (~07:00 Rome, DST-safe twin cron) and
commits the brief + vocab + state back to the repo. Configure on the repo:
- **Secrets:** `API_KEY`, `RESEND_API_KEY`
- **Variables:** `EMAIL_TO` (the Resend account owner address), optional `API_BASE_URL`,
  `API_MODEL`, `EMAIL_FROM`

Trigger a test run from the Actions tab ("Run workflow") — manual runs force generation.

## Using Claude instead of DeepSeek
Set repo Variables `API_BASE_URL=https://openrouter.ai/api/v1` and
`API_MODEL=anthropic/claude-3.5-sonnet` (any OpenAI-compatible endpoint works).

## Layout
```
scripts/main.py        orchestrator
scripts/topics.py      area selection + seen-topic state
scripts/generate.py    LLM call -> brief + vocab (DeepSeek, retry/backoff)
scripts/vocab_log.py   append words to vocab/vocab.jsonl
scripts/email_brief.py Resend delivery
interests.txt          broad areas to draw from
daily/                 dated brief archive
vocab/vocab.jsonl      cumulative vocabulary log
data/seen_topics.json  covered topics (prevents repeats)
```
