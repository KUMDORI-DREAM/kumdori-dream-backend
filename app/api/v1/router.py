from fastapi import APIRouter

from app.api.v1.endpoints.robots import router as robots_router
from app.api.v1.endpoints.routes import router as routes_router
from app.api.v1.endpoints.warehouse import router as warehouse_router

router = APIRouter()
router.include_router(robots_router)
router.include_router(routes_router)
router.include_router(warehouse_router)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
