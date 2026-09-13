from fastapi import APIRouter

from app.api.v1.endpoints.robots import router as robots_router

router = APIRouter()
router.include_router(robots_router)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
