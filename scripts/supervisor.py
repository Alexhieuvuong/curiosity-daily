"""
supervisor.py — the fact-checking review pass (adapted from Supervisor-Skills'
pre-submission-reviewer). Audits a drafted brief against its sources and auto-revises
to remove unsupported/uncited claims before delivery.

Fail-safe by design: any error or unparseable output returns the ORIGINAL prose
unchanged, so a flaky review never breaks or blanks the daily run.
"""

from llm import chat
from skills import load_skill

DELIM = "---REVISED BRIEF---"


def review_and_revise(prose, sources):
    """Return (possibly-revised prose, report dict {verdict, issues})."""
    system = load_skill("fact-supervisor")
    user = _build_user(prose, sources)
    try:
        text, _model = chat(system, user, temperature=0.2)
    except Exception as e:  # never let the review break the run
        print(f"[supervisor] call failed ({e}); keeping original brief.")
        return prose, {"verdict": "ERROR", "issues": [str(e)]}

    if DELIM in text:
        header, revised = text.split(DELIM, 1)
        revised = revised.strip()
        verdict, issues = _parse_header(header)
        if revised:
            print(f"[supervisor] {verdict}; {len(issues)} issue(s) found.")
            for it in issues:
                print(f"    - {it}")
            return revised, {"verdict": verdict, "issues": issues}

    print("[supervisor] output not parseable — keeping original brief.")
    return prose, {"verdict": "UNPARSED", "issues": []}


def _build_user(prose, sources):
    if sources:
        src = "\n\n".join(
            f"[{i}] {s['title']} ({s['url']})\n{s['extract']}"
            for i, s in enumerate(sources, start=1)
        )
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
