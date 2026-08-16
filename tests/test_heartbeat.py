import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from heartbeat import Heartbeat, HeartbeatMissing  # noqa: E402


def test_heartbeat_written_and_checked(tmp_path):
    hb_dir = tmp_path / "heartbeat"
    hb = Heartbeat(hb_dir, name="editor", interval=0.05)
    hb.start()
    time.sleep(0.1)
    assert hb.is_alive(max_age=1.0) is True
    hb.stop()


def test_missing_heartbeat_detected(tmp_path):
    hb = Heartbeat(tmp_path / "heartbeat", name="editor")
    try:
        hb.is_alive(max_age=0.1)
    except HeartbeatMissing:
        pass
    else:
        raise AssertionError("expected HeartbeatMissing")
