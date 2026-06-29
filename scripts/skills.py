"""
skills.py — load modular skill prompts from skills/<name>/SKILL.md.

Each SKILL.md holds the *static method* for one task (role, procedure, rubric, output
format) and is used as the LLM system prompt; dynamic data (sources, area, word list)
is injected by the caller in the user prompt. Pattern adapted from HKUSTDial/Supervisor-Skills.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, "skills")

_FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n(.*)$", re.DOTALL)


def load_skill(name):
    """Return the instruction body of skills/<name>/SKILL.md (YAML frontmatter stripped)."""
    path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = _FRONTMATTER.match(text)
    return (m.group(1) if m else text).strip()
