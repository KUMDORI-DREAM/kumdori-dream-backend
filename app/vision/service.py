from fastapi import Depends, FastAPI, HTTPException, Query, Request
from PIL import Image

from app.vision.model import PersonDetector, get_detector

app = FastAPI(title="kumdori-vision-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/detect")
async def detect(
    request: Request,
    width: int = Query(gt=0),
    height: int = Query(gt=0),
    detector: PersonDetector = Depends(get_detector),
) -> dict:
    body = await request.body()
    # Webots Camera.getImage()는 BGRA raw 픽셀을 반환한다.
    expected_size = width * height * 4
    if len(body) != expected_size:
        raise HTTPException(
            status_code=400, detail="이미지 바이트 크기가 width/height와 일치하지 않습니다"
        )

    image = Image.frombytes("RGBA", (width, height), body, "raw", "BGRA").convert("RGB")
    detections = detector.detect(image)
    return {
        "detections": [
            {"class_name": d.class_name, "confidence": d.confidence, "bbox": list(d.bbox)}
            for d in detections
        ]
    }
