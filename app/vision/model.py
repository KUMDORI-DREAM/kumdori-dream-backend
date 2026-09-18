import os
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image

DEFAULT_MODEL_PATH = os.environ.get("KUMDORI_VISION_MODEL", "webots/models/yolov8n.pt")
DEFAULT_CONFIDENCE = float(os.environ.get("KUMDORI_VISION_CONFIDENCE", "0.4"))

# 창고 안전 감지는 사전학습 YOLO(COCO 클래스) 중 사람 탐지만 우선 사용한다.
# box/pallet/obstacle 등 창고 전용 클래스는 파인튜닝된 모델로 교체될 때 추가한다.
TARGET_CLASSES = {"person"}


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2), 0~1로 정규화


class PersonDetector:
    def __init__(
        self, model_path: str = DEFAULT_MODEL_PATH, confidence: float = DEFAULT_CONFIDENCE
    ):
        from ultralytics import YOLO

        self._model = YOLO(model_path)
        self._confidence = confidence

    def detect(self, image: Image.Image) -> list[Detection]:
        width, height = image.size
        results = self._model.predict(image, conf=self._confidence, verbose=False)

        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                class_name = result.names[int(box.cls[0])]
                if class_name not in TARGET_CLASSES:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    Detection(
                        class_name=class_name,
                        confidence=float(box.conf[0]),
                        bbox=(x1 / width, y1 / height, x2 / width, y2 / height),
                    )
                )
        return detections


@lru_cache
def get_detector() -> PersonDetector:
    return PersonDetector()
