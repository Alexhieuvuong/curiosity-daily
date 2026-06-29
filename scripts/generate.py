"""
generate.py — produce one daily curiosity brief + vocabulary, GROUNDED in real sources
(research.py) and FACT-CHECKED by a supervisor pass (supervisor.py) before delivery.

Flow:
1. Draft the brief with the `brief-writer` skill (system prompt) + dynamic data (user prompt).
2. Parse the TOPIC line and the trailing ```json vocab block (vocab is set aside — not a
   fabrication risk).
3. Run the `fact-supervisor` review pass on the prose: it audits every factual claim against
   the sources and auto-revises unsupported/uncited ones.
4. Inject the verified ## Sources list (real URLs, never model-written) before the Vocabulary
   Builder, add a footer.

generate() returns (topic_title, body_markdown, vocab_list).
"""

import json
import re

from llm import chat
from skills import load_skill
from supervisor import review_and_revise


def _sources_block(sources):
    return "\n\n".join(
        f"[{i}] {s['title']} ({s['url']})\n{s['extract']}"
        for i, s in enumerate(sources, start=1)
    )


def _build_user_prompt(area, recent_topics, date_str, sources):
    recent_block = "\n".join(f"- {t}" for t in recent_topics) or "(none yet)"
    if sources:
        grounding = (f'You have REAL reference material below. Choose ONE specific, '
                     f'curiosity-sparking angle within "{area}" that THIS material supports, '
                     f'and base all facts on it, citing [n].\n\n'
                     f'SOURCE MATERIAL:\n{_sources_block(sources)}')
    else:
        grounding = (f'No external sources were retrieved. Explain only from first principles '
                     f'within "{area}"; state no specific statistic, date, or named case as '
                     f'fact; label any example "Illustrative:".')

    return f"""Today is {date_str}. {grounding}

Your angle MUST be clearly different from every topic already covered:
{recent_block}

Write the brief now, following your instructions exactly: the TOPIC line first, then the
sections in order, then the JSON vocabulary block."""


def generate(area, recent_topics, date_str, sources):
    system = load_skill("brief-writer")
    user = _build_user_prompt(area, recent_topics, date_str, sources)
    # Grounded summarization, not free invention.
    raw, model = chat(system, user, temperature=0.6)

    topic, prose, vocab = _parse_raw(raw)
    prose, _report = review_and_revise(prose, sources)  # auto-revise unsupported claims
    body = _assemble(prose, sources, date_str, model)
    return topic, body, vocab


def _parse_raw(text):
    """Split raw model output into (topic, prose, vocab_list). Strips the JSON vocab block."""
    topic = "Untitled"
    lines = text.splitlines()
    if lines and lines[0].strip().upper().startswith("TOPIC:"):
        topic = lines[0].split(":", 1)[1].strip() or topic
        text = "\n".join(lines[1:]).strip()

    vocab = []
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, list):
                vocab = parsed
        except json.JSONDecodeError:
            print("  [warn] could not parse vocab JSON block — skipping vocab log.")
        text = text[: m.start()].rstrip()

    return topic, text, vocab


def _sources_section(sources):
    if not sources:
        return ("## Sources\n\n_No external sources were retrieved for this brief; it is "
                "reasoned from first principles only._\n")
    lines = ["## Sources", ""]
    for i, s in enumerate(sources, start=1):
        lines.append(f"[{i}] [{s['title']}]({s['url']})")
    return "\n".join(lines) + "\n"


def _assemble(prose, sources, date_str, model):
    """Inject the verified Sources list before Vocabulary Builder; add the footer."""
    sources_md = _sources_section(sources)
    vb = re.search(r"^##\s+Vocabulary Builder", prose, re.MULTILINE | re.IGNORECASE)
    if vb:
        prose = prose[: vb.start()].rstrip() + "\n\n" + sources_md + "\n" + prose[vb.start():]
    else:
        prose = prose.rstrip() + "\n\n" + sources_md
    return f"{prose}\n\n---\n*Curiosity Daily · {date_str} · grounded & fact-checked · {model}*\n"
