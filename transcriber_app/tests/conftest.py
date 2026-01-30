# transcriber_app/tests/conftest.py
"""Test configuration helpers.

Ensure the repository root is on sys.path so imports like
`from transcriber_app.modules import ...` work in CI and local runs.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1].parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
