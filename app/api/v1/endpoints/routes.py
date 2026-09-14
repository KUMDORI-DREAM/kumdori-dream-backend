from fastapi import APIRouter, HTTPException

from app.route_planner import a_star
from app.schemas.route import RoutePlanIn, RoutePlanOut

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/plan", response_model=RoutePlanOut)
async def plan_route(payload: RoutePlanIn) -> RoutePlanOut:
    try:
        nodes = a_star(payload.graph, payload.coordinates, payload.start, payload.goal)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    cost = sum(
        next(cost for neighbor, cost in payload.graph[node] if neighbor == following)
        for node, following in zip(nodes, nodes[1:], strict=False)
    )
    return RoutePlanOut(nodes=nodes, cost=cost)
