from pydantic import BaseModel


class RoutePlanIn(BaseModel):
    graph: dict[str, list[tuple[str, float]]]
    coordinates: dict[str, tuple[float, float]]
    start: str
    goal: str


class RoutePlanOut(BaseModel):
    nodes: list[str]
    cost: float


class WarehouseNodeIn(BaseModel):
    id: str
    aisle: str | None = None
    x: float
    y: float


class WarehouseEdgeIn(BaseModel):
    from_node: str
    to_node: str
    cost: float
    blocked: bool = False
