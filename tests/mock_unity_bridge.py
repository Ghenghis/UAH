# tests/mock_unity_bridge.py — a fake Unity Editor that speaks the subset of
# the MCP protocol that the harness cares about. Used by integration tests to
# exercise domain reload, crash, hang, and license-cap scenarios without a
# real Editor.

import time


class MockUnityBridge:
    def __init__(self):
        self.scenes = []
        self.crashed = False
        self.hung = False
        self.reloading = False

    def open_scene(self, name: str) -> None:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        if name not in self.scenes:
            self.scenes.append(name)

    def list_open_scenes(self, timeout: float = 5.0) -> list[str]:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        if self.hung:
            # Simulate a hang by blocking past the timeout.
            time.sleep(timeout + 1.0)
            raise TimeoutError("Editor did not respond")
        if self.reloading:
            # Caller will retry after the reload completes.
            raise ConnectionError("Editor is reloading")
        return list(self.scenes)

    def create_gameobject(self, name: str) -> dict:
        if self.crashed:
            raise RuntimeError("Editor has crashed")
        return {"id": len(self.scenes) + 1, "name": name}

    # --- simulation controls ------------------------------------------------
    def simulate_crash(self) -> None:
        self.crashed = True

    def simulate_hang(self) -> None:
        self.hung = True

    def simulate_domain_reload(self) -> None:
        self.reloading = True
        time.sleep(0.1)  # brief reload window
        self.reloading = False

    def recover_from_crash(self) -> None:
        self.crashed = False
        self.hung = False
