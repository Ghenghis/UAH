import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import license_helper  # noqa: E402


def test_activate_interactive_calls_subprocess():
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        rc = license_helper.activate(interactive=True, ulf_path=None)
    assert rc == 0
    run.assert_called_once()
    args = run.call_args[0][0]
    assert "unity-license-activate" in " ".join(map(str, args))


def test_activate_with_ulf_passes_path():
    with patch("subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        rc = license_helper.activate(interactive=False, ulf_path="C:/x.ulf")
    assert rc == 0
    cmd = run.call_args[0][0]
    assert any("C:/x.ulf" in str(a) for a in cmd)


def test_personal_tier_message_on_cap(capsys):
    msg = license_helper.personal_tier_message()
    assert "Personal" in msg
    assert "1 concurrent" in msg
