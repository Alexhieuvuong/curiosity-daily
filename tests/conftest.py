"""Make the scripts/ modules importable from the test suite.

The project keeps its modules in scripts/ and runs them as top-level scripts
(imports like `from llm import chat`), so tests add scripts/ to sys.path rather
than turning it into a package.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
