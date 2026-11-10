"""Tests for vocab_log.py — the append-only JSONL log and its recent-window reader.
VOCAB_FILE is monkeypatched to a tmp path so no real data is touched."""

import json
from datetime import date, timedelta

import pytest

import vocab_log


@pytest.fixture
def vocab_file(tmp_path, monkeypatch):
    path = tmp_path / "vocab.jsonl"
    monkeypatch.setattr(vocab_log, "VOCAB_FILE", str(path))
    return path


def _read_rows(path):
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


# --- append_vocab ---------------------------------------------------------

def test_append_writes_rows_and_returns_count(vocab_file):
    entries = [
        {"word": "auction", "pos": "n", "definition": "a sale"},
        {"word": "cadence", "pos": "n", "definition": "rhythm"},
    ]
    assert vocab_log.append_vocab(entries, "Topic", "2026-07-02") == 2
    rows = _read_rows(vocab_file)
    assert [r["word"] for r in rows] == ["auction", "cadence"]
    assert rows[0]["date"] == "2026-07-02" and rows[0]["topic"] == "Topic"


def test_append_skips_entries_without_word(vocab_file):
    entries = [{"word": "", "definition": "x"}, {"definition": "no word key"}, "not-a-dict"]
    assert vocab_log.append_vocab(entries, "Topic", "2026-07-02") == 0
    assert not vocab_file.exists() or _read_rows(vocab_file) == []


def test_append_dedups_same_day_rerun(vocab_file):
    entries = [{"word": "auction", "definition": "a sale"}]
    assert vocab_log.append_vocab(entries, "Topic", "2026-07-02") == 1
    # A rerun for the same date (FORCE_RUN, or a second cron tick) must not double-log.
    assert vocab_log.append_vocab(entries, "Topic", "2026-07-02") == 0
    assert len(_read_rows(vocab_file)) == 1


def test_append_dedup_is_case_insensitive(vocab_file):
    vocab_log.append_vocab([{"word": "Auction", "definition": "x"}], "T", "2026-07-02")
    assert vocab_log.append_vocab([{"word": "auction", "definition": "x"}], "T", "2026-07-02") == 0


def test_append_same_word_different_day_is_allowed(vocab_file):
    vocab_log.append_vocab([{"word": "auction", "definition": "x"}], "T", "2026-07-01")
    assert vocab_log.append_vocab([{"word": "auction", "definition": "x"}], "T", "2026-07-02") == 1
    assert len(_read_rows(vocab_file)) == 2


# --- load_recent ----------------------------------------------------------

def test_load_recent_missing_file_returns_empty(vocab_file):
    assert vocab_log.load_recent(7) == []


def test_load_recent_respects_date_cutoff(vocab_file):
    today = date.today()
    old = (today - timedelta(days=10)).isoformat()
    recent = (today - timedelta(days=1)).isoformat()
    vocab_log.append_vocab([{"word": "stale", "definition": "x"}], "T", old)
    vocab_log.append_vocab([{"word": "fresh", "definition": "x"}], "T", recent)
    words = [r["word"] for r in vocab_log.load_recent(7)]
    assert words == ["fresh"]


def test_load_recent_dedups_by_word(vocab_file):
    today = date.today()
    d1 = (today - timedelta(days=2)).isoformat()
    d2 = (today - timedelta(days=1)).isoformat()
    vocab_log.append_vocab([{"word": "echo", "definition": "first"}], "T", d1)
    vocab_log.append_vocab([{"word": "echo", "definition": "second"}], "T", d2)
    rows = vocab_log.load_recent(7)
    assert len(rows) == 1
    assert rows[0]["definition"] == "first"     # keeps the first occurrence


def test_load_recent_skips_malformed_lines(vocab_file):
    vocab_log.append_vocab([{"word": "good", "definition": "x"}], "T", date.today().isoformat())
    with open(vocab_file, "a", encoding="utf-8") as f:
        f.write("{ this is not valid json\n")
    rows = vocab_log.load_recent(7)
    assert [r["word"] for r in rows] == ["good"]
