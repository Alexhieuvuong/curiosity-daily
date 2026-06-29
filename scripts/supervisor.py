"""
supervisor.py — the fact-checking review pass (adapted from Supervisor-Skills'
pre-submission-reviewer). Audits a drafted brief against its sources and auto-revises
to remove unsupported/uncited claims before delivery.

Fail-safe by design: any error or unparseable output returns the ORIGINAL prose
unchanged, so a flaky review never breaks or blanks the daily run.
"""

import re

from llm import chat
from research import sources_prompt_block
from skills import load_skill

DELIM = "---REVISED BRIEF---"
# Tolerate delimiter formatting drift: a line that is essentially "REVISED BRIEF",
# optionally wrapped in dashes/hashes/asterisks/quotes/colon.
_SPLIT = re.compile(r"(?im)^[\s>#*_\-]*revised brief[\s>#*_:\-]*$")


def review_and_revise(prose, sources):
    """Return (possibly-revised prose, report dict {verdict, issues}). Fail-safe: any
    error or unparseable output returns the original prose unchanged."""
    system = load_skill("fact-supervisor")
    user = _build_user(prose, sources)
    try:
        text, _model = chat(system, user, temperature=0.2)
    except Exception as e:  # never let the review break the run
        print(f"[supervisor] call failed ({e}); keeping original brief.")
        return prose, {"verdict": "ERROR", "issues": [str(e)]}

    parts = _SPLIT.split(text, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        verdict, issues = _parse_header(parts[0])
        revised = parts[1].strip()
        print(f"[supervisor] {verdict}; {len(issues)} issue(s) found.")
        for it in issues:
            print(f"    - {it}")
        return revised, {"verdict": verdict, "issues": issues}

    # No revised brief emitted. If the model said PASS, the original is fine.
    verdict, issues = _parse_header(text)
    if verdict.upper().startswith("PASS"):
        print(f"[supervisor] PASS; {len(issues)} note(s) — no changes.")
        return prose, {"verdict": "PASS", "issues": issues}

    print("[supervisor] output not parseable — keeping original brief.")
    return prose, {"verdict": "UNPARSED", "issues": issues}


def _build_user(prose, sources):
    if sources:
        src = sources_prompt_block(sources)
    else:
        src = "(no external sources were provided — the brief must contain no specific facts)"
    return (f"SOURCE MATERIAL:\n{src}\n\n"
            f"DRAFT BRIEF:\n{prose}\n\n"
            "Audit and revise per your instructions. Output VERDICT and ISSUES, then the "
            f"corrected brief after a line containing exactly {DELIM}")


def _parse_header(header):
    verdict = "REVISED"
    issues = []
    for line in header.splitlines():
        s = line.strip()
        if s.upper().startswith("VERDICT:"):
            verdict = s.split(":", 1)[1].strip() or verdict
        elif s.startswith("- ") and s[2:].strip().lower() != "none":
            issues.append(s[2:].strip())
    return verdict, issues
