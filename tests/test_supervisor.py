"""Tests for supervisor.py delimiter splitting and header parsing — the tolerant
parsing that survives the LLM's formatting drift. Pure regex/string helpers."""

import supervisor


# --- _SPLIT (revised-brief delimiter, drift-tolerant) ---------------------

def test_split_exact_delimiter():
    text = "VERDICT: REVISED\n- fixed a claim\n---REVISED BRIEF---\nThe corrected brief."
    parts = supervisor._SPLIT.split(text, maxsplit=1)
    assert len(parts) == 2
    assert parts[1].strip() == "The corrected brief."


def test_split_markdown_heading_drift():
    text = "VERDICT: REVISED\n## REVISED BRIEF\nBody after heading."
    parts = supervisor._SPLIT.split(text, maxsplit=1)
    assert len(parts) == 2
    assert parts[1].strip() == "Body after heading."


def test_split_bold_colon_drift():
    text = "VERDICT: REVISED\n**Revised Brief:**\nBody after bold label."
    parts = supervisor._SPLIT.split(text, maxsplit=1)
    assert len(parts) == 2
    assert parts[1].strip() == "Body after bold label."


def test_split_absent_delimiter_yields_single_part():
    text = "VERDICT: PASS\n- none"
    parts = supervisor._SPLIT.split(text, maxsplit=1)
    assert len(parts) == 1


# --- _parse_header --------------------------------------------------------

def test_parse_header_extracts_verdict_and_issues():
    header = "VERDICT: REVISED\n- removed an unsupported statistic\n- rephrased a claim"
    verdict, issues = supervisor._parse_header(header)
    assert verdict == "REVISED"
    assert issues == ["removed an unsupported statistic", "rephrased a claim"]


def test_parse_header_skips_none_issue():
    verdict, issues = supervisor._parse_header("VERDICT: PASS\n- none")
    assert verdict == "PASS"
    assert issues == []


def test_parse_header_defaults_when_no_verdict_line():
    verdict, issues = supervisor._parse_header("some text with no verdict")
    assert verdict == "REVISED"            # documented default
    assert issues == []
