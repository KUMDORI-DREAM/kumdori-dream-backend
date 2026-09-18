from fastapi.testclient import TestClient

from app.vision.model import Detection, get_detector
from app.vision.service import app


class FakeDetector:
    def detect(self, image):
        return [Detection(class_name="person", confidence=0.9, bbox=(0.4, 0.2, 0.6, 0.8))]


def test_detect_returns_person_detections():
    app.dependency_overrides[get_detector] = lambda: FakeDetector()
    try:
        client = TestClient(app)
        width, height = 4, 3
        image_bytes = bytes([0, 0, 0, 255]) * (width * height)

        response = client.post(f"/detect?width={width}&height={height}", content=image_bytes)

        assert response.status_code == 200
        assert response.json() == {
            "detections": [
                {"class_name": "person", "confidence": 0.9, "bbox": [0.4, 0.2, 0.6, 0.8]}
            ]
        }
    finally:
        app.dependency_overrides.clear()


def test_detect_rejects_body_size_mismatch():
    client = TestClient(app)

    response = client.post("/detect?width=4&height=3", content=b"\x00" * 5)

    assert response.status_code == 400


def test_health_check():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
