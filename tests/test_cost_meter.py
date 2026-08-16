import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from cost_meter import parse_claude_code_line, parse_codex_line, log_entry  # noqa: E402


def test_parses_claude_code_line():
    # Real Claude Code log lines look like: "tokens: 1234 in, 567 out"
    entry = parse_claude_code_line("tokens: 1234 in, 567 out")
    assert entry == {"runtime": "claude_code", "in": 1234, "out": 567}


def test_parses_codex_line():
    entry = parse_codex_line("usage: prompt=900 completion=80 total=980")
    assert entry == {"runtime": "codex", "in": 900, "out": 80}


def test_log_entry_format(tmp_path):
    path = log_entry(tmp_path, {"runtime": "claude_code", "in": 1, "out": 2})
    text = path.read_text()
    assert "claude_code" in text
    assert '"in": 1' in text
