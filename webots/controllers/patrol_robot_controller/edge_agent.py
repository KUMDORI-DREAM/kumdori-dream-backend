from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request

DEFAULT_BACKEND_URL = os.environ.get("KUMDORI_BACKEND_URL", "http://localhost:8000")
DEFAULT_HEARTBEAT_INTERVAL_S = float(os.environ.get("KUMDORI_HEARTBEAT_INTERVAL_S", "1.0"))
REQUEST_TIMEOUT_S = 0.5


class EdgeAgent:
    """Sends robot position/status heartbeats from the Webots controller to the backend.

    Runs each request on a background thread so a slow or unreachable backend
    never stalls the Webots simulation step.
    """

    def __init__(
        self,
        robot_id: str,
        backend_url: str = DEFAULT_BACKEND_URL,
        interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S,
    ) -> None:
        self.robot_id = robot_id
        self.backend_url = backend_url.rstrip("/")
        self.interval_s = interval_s
        self._last_sent_s = float("-inf")

    def send_heartbeat(
        self, now_s: float, x: float, y: float, status: str, battery: float | None = None
    ) -> None:
        if now_s - self._last_sent_s < self.interval_s:
            return
        self._last_sent_s = now_s

        payload = {"x": x, "y": y, "status": status, "battery": battery}
        thread = threading.Thread(target=self._post_heartbeat, args=(payload,), daemon=True)
        thread.start()

    def _post_heartbeat(self, payload: dict) -> None:
        url = f"{self.backend_url}/api/v1/robots/{self.robot_id}/heartbeat"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S)
        except (urllib.error.URLError, OSError) as exc:
            print(f"[edge-agent:{self.robot_id}] heartbeat failed: {exc}")
