"""Tests for generate.py parsing/assembly helpers — the fragile bits that turn raw
LLM text into a saved brief. Pure functions, no LLM calls."""

import generate


SRC = [
    {"title": "Money", "url": "https://en.wikipedia.org/wiki/Money", "kind": "Wikipedia"},
    {"title": "A paper (2021)", "url": "https://doi.org/10.x", "kind": "academic paper"},
]


# --- _parse_raw -----------------------------------------------------------

def test_parse_raw_extracts_topic_and_vocab():
    raw = (
        "TOPIC: The Hidden Clock\n"
        "## Hook\nSome prose here.\n\n"
        '```json\n[{"word": "auction", "definition": "a sale"}]\n```\n'
    )
    topic, prose, vocab = generate._parse_raw(raw)
    assert topic == "The Hidden Clock"
    assert "Some prose here." in prose
    assert "```json" not in prose          # vocab block stripped from prose
    assert vocab == [{"word": "auction", "definition": "a sale"}]


def test_parse_raw_topic_case_insensitive():
    topic, _prose, _vocab = generate._parse_raw("topic: lowercase label\nBody")
    assert topic == "lowercase label"


def test_parse_raw_missing_topic_defaults_untitled():
    topic, prose, vocab = generate._parse_raw("## Hook\nNo topic line at all.")
    assert topic == "Untitled"
    assert prose.startswith("## Hook")
    assert vocab == []


def test_parse_raw_malformed_json_is_skipped_but_block_stripped():
    raw = "TOPIC: X\nProse.\n\n```json\n[not valid json,,,]\n```\n"
    topic, prose, vocab = generate._parse_raw(raw)
    assert topic == "X"
    assert vocab == []                     # unparseable -> empty, not a crash
    assert "```json" not in prose          # still stripped so it never reaches the reader


def test_parse_raw_non_list_json_ignored():
    raw = 'TOPIC: X\nProse.\n\n```json\n{"word": "solo"}\n```\n'
    _topic, _prose, vocab = generate._parse_raw(raw)
    assert vocab == []                     # a dict (not a list) is not accepted


def test_parse_raw_no_fence_leaves_prose_intact():
    topic, prose, vocab = generate._parse_raw("TOPIC: X\nJust prose, no vocab fence.")
    assert prose == "Just prose, no vocab fence."
    assert vocab == []


# --- _sources_section -----------------------------------------------------

def test_sources_section_populated():
    md = generate._sources_section(SRC)
    assert md.startswith("## Sources")
    assert "[1] [Money](https://en.wikipedia.org/wiki/Money) — Wikipedia" in md
    assert "[2] [A paper (2021)](https://doi.org/10.x) — academic paper" in md


def test_sources_section_empty_states_first_principles():
    md = generate._sources_section([])
    assert "## Sources" in md
    assert "first principles" in md.lower()


# --- _assemble ------------------------------------------------------------

def test_assemble_injects_sources_before_vocabulary_builder():
    prose = "## Hook\nText.\n\n## Vocabulary Builder\n- word"
    body = generate._assemble(prose, SRC, "2026-07-02", "deepseek-chat")
    assert body.index("## Sources") < body.index("## Vocabulary Builder")
    assert body.index("## Hook") < body.index("## Sources")


def test_assemble_appends_sources_when_no_vocab_section():
    prose = "## Hook\nText only, no vocabulary section."
    body = generate._assemble(prose, SRC, "2026-07-02", "deepseek-chat")
    assert "## Sources" in body
    assert body.index("## Hook") < body.index("## Sources")


def test_assemble_footer_format():
    body = generate._assemble("## Hook\nT.", SRC, "2026-07-02", "deepseek-chat")
    assert body.rstrip().endswith(
        "*Curiosity Daily · 2026-07-02 · grounded & fact-checked · deepseek-chat*"
    )
