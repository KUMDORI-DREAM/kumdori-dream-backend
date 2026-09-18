from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request

DEFAULT_VISION_URL = os.environ.get("KUMDORI_VISION_URL", "http://localhost:8100")
REQUEST_TIMEOUT_S = 0.8

# 사람이 카메라 프레임 가로 중심 구간(경로 정면)에 있을 때만 "경로상 사람"으로 간주한다.
PATH_BAND = (0.30, 0.70)
# 오탐을 줄이기 위해 연속으로 이만큼 감지되어야 이벤트를 발생시킨다.
PERSIST_COUNT = 3
# 같은 상황에 대해 이벤트를 반복 전송하지 않도록 최소 간격을 둔다.
COOLDOWN_S = 5.0


class PersonPathDetector:
    """카메라 프레임을 별도 비전 추론 서비스로 보내 사람 감지를 확인한다.

    비전 서비스 호출은 백그라운드 스레드에서 수행하므로 Webots 시뮬레이션
    스텝(물리 루프)을 막지 않는다. 최근 판단 결과는 다음 호출에서 이어서
    누적하므로, 여러 프레임에 걸쳐 경로상에서 사람이 유지될 때만 콜백을
    호출한다.
    """

    def __init__(self, on_person_in_path, vision_url: str = DEFAULT_VISION_URL) -> None:
        self._on_person_in_path = on_person_in_path
        self.vision_url = vision_url.rstrip("/")
        self._consecutive_hits = 0
        self._last_event_s = float("-inf")

    def submit_frame(
        self, now_s: float, image_bytes: bytes, width: int, height: int, x: float, y: float
    ) -> None:
        thread = threading.Thread(
            target=self._detect_and_evaluate,
            args=(image_bytes, width, height, now_s, x, y),
            daemon=True,
        )
        thread.start()

    def _detect_and_evaluate(
        self, image_bytes: bytes, width: int, height: int, now_s: float, x: float, y: float
    ) -> None:
        detections = self._request_detections(image_bytes, width, height)
        person_in_path = any(
            detection["class_name"] == "person"
            and PATH_BAND[0] <= (detection["bbox"][0] + detection["bbox"][2]) / 2 <= PATH_BAND[1]
            for detection in detections
        )
        if not person_in_path:
            self._consecutive_hits = 0
            return

        self._consecutive_hits += 1
        if self._consecutive_hits < PERSIST_COUNT:
            return
        if now_s - self._last_event_s < COOLDOWN_S:
            return
        self._last_event_s = now_s
        self._on_person_in_path(x, y)

    def _request_detections(self, image_bytes: bytes, width: int, height: int) -> list[dict]:
        url = f"{self.vision_url}/detect?width={width}&height={height}"
        request = urllib.request.Request(
            url,
            data=image_bytes,
            headers={"Content-Type": "application/octet-stream"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
                return json.loads(response.read().decode("utf-8"))["detections"]
        except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
            print(f"[vision-client] detect failed: {exc}")
            return []
