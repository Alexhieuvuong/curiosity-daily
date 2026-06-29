"""
generate.py — produce one daily curiosity brief + vocabulary, GROUNDED in real
sources (see research.py) rather than invented from the model's memory.

Anti-fabrication design:
- The brief must base every factual claim on the SOURCE MATERIAL passed in, and cite
  it inline as [1], [2], ...
- Anything illustrative/hypothetical must be prefixed "Illustrative:".
- The ## Sources list is injected here from the real retrieval result, so the URLs
  cannot be fabricated by the model.
- If no sources were retrieved, a fallback prompt forbids specific facts entirely.

The model returns:
  TOPIC: <specific title>                 (first line)
  # <title> ... brief (first principles -> adjacent fields -> real-world case) ...
  ## Vocabulary Builder ...
  ```json [ {word, pos, ipa, definition, example}, ... ] ```

generate() returns (topic_title, body_markdown, vocab_list).
"""

import json
import re

from llm import chat

SYSTEM_PROMPT = """You are a sharp research analyst and patient teacher who writes a \
short daily brief that sparks curiosity AND teaches the reader how to think about a topic.

You are NOT a creative writer inventing facts. You work like a careful explainer:
- Every factual claim — definitions, statistics, dates, named people/places/events/cases \
— must come from the SOURCE MATERIAL you are given, and you cite it inline as [1], [2], ...
- You may add ANALYSIS and INTERPRETATION (incentives, second-order effects, connections \
to other fields), but it must clearly follow from the sourced facts and be framed as your \
reasoning, not asserted as established fact.
- If you use a simplified or hypothetical example that is NOT in the sources, you MUST \
prefix it with "Illustrative:" so the reader knows it is not a verified fact.
- Never invent specific numbers, dates, or named cases. If the sources do not support a \
specific, reason qualitatively instead. It is better to say less than to fabricate.
- Write in clear, advanced-but-readable English (a learner reads this to grow vocabulary)."""


def _sources_block(sources):
    parts = []
    for i, s in enumerate(sources, start=1):
        parts.append(f"[{i}] {s['title']} ({s['url']})\n{s['extract']}")
    return "\n\n".join(parts)


def _build_user_prompt(area, recent_topics, date_str, sources):
    recent_block = "\n".join(f"- {t}" for t in recent_topics) or "(none yet)"

    if sources:
        grounding = f"""You have been given REAL reference material below. Choose ONE \
specific, curiosity-sparking angle within "{area}" that THIS material actually supports \
— narrow enough to dig into deeply. Base all facts on the sources and cite them as [n].

SOURCE MATERIAL (cite these; do not invent beyond them):
{_sources_block(sources)}"""
    else:
        grounding = f"""No external sources were retrieved this time. Therefore explain \
ONLY from first principles and broadly established concepts within "{area}". Do NOT state \
any specific statistic, date, named program, or named case as fact. If you use an example, \
prefix it with "Illustrative:". Keep every claim qualitative and clearly reasoned."""

    return f"""Today is {date_str}. {grounding}

Your angle MUST be clearly different from every topic already covered:
{recent_block}

Write the brief in EXACTLY this structure and order, in Markdown. Keep each section tight.

TOPIC: <a short, specific title — just the title text, on the very first line>

# <the same title>

> <one-line hook that makes the reader curious>

## Why this is interesting
<2–4 sentences.>

## First principles
<Build the idea from the ground up — the irreducible mechanic, explained plainly. Cite [n].>

## Break it into pieces
<3–5 bullets: the sub-questions or tensions worth pulling apart.>

## Follow the incentives
<Who pays, who profits, who bears the risk, and why each acts as they do. Cite [n] for facts.>

## How it echoes elsewhere
<Connect the core mechanic to 1–2 ADJACENT fields or domains where the same pattern appears.>

## A real-world case
<One concrete case grounded in the sources, cited [n]. If the sources lack a specific case, \
give an "Illustrative:" simplified scenario instead — clearly labeled.>

## Second-order effects
<The non-obvious downstream consequences. Your analysis, following from the sourced facts.>

## A question to sit with
<ONE genuinely open question, left deliberately unresolved.>

## Go deeper
<2–3 concrete threads or angles the reader could explore or discuss next.>

## Vocabulary Builder
<8–12 useful or advanced words/phrases that appear in (or are natural to) this brief.
Format each as a numbered list item exactly like:
1. **word** — (part of speech, /IPA/) — concise definition. _Example: a sentence using it in this topic's context._>

Do NOT write a "Sources" section yourself — a verified one is appended automatically.

Finally, AFTER the brief, output the SAME vocabulary as one fenced JSON code block
(parsed by a program — keep keys exactly as shown, valid JSON, no comments):

```json
[
  {{"word": "...", "pos": "...", "ipa": "...", "definition": "...", "example": "..."}}
]
```"""


def generate(area, recent_topics, date_str, sources):
    user_prompt = _build_user_prompt(area, recent_topics, date_str, sources)
    # Lower temperature than before — grounded summarization, not free invention.
    text, model = chat(SYSTEM_PROMPT, user_prompt, temperature=0.6)
    return _parse(text, model, date_str, sources)


def _sources_section(sources):
    if not sources:
        return ("## Sources\n\n_No external sources were retrieved for this brief; it is "
                "reasoned from first principles only._\n")
    lines = ["## Sources", ""]
    for i, s in enumerate(sources, start=1):
        lines.append(f"[{i}] [{s['title']}]({s['url']})")
    return "\n".join(lines) + "\n"


def _parse(text, model, date_str, sources):
    """Split model output into (topic, body_markdown, vocab_list)."""
    topic = "Untitled"
    lines = text.splitlines()
    if lines and lines[0].strip().upper().startswith("TOPIC:"):
        topic = lines[0].split(":", 1)[1].strip() or topic
        text = "\n".join(lines[1:]).strip()

    # Pull out the trailing machine-readable JSON block and remove it from the body.
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

    # Inject the verified Sources list just before the Vocabulary Builder (or at the end).
    sources_md = _sources_section(sources)
    vb = re.search(r"^##\s+Vocabulary Builder", text, re.MULTILINE | re.IGNORECASE)
    if vb:
        text = text[: vb.start()].rstrip() + "\n\n" + sources_md + "\n" + text[vb.start():]
    else:
        text = text.rstrip() + "\n\n" + sources_md

    body = f"{text}\n\n---\n*Curiosity Daily · {date_str} · grounded summary via {model}*\n"
    return topic, body, vocab
