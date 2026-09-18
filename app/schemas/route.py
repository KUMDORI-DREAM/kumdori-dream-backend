from pydantic import BaseModel, field_validator


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
    name: str | None = None
    node_type: str = "AISLE"
    aisle: str | None = None
    x: float
    y: float

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, value: str) -> str:
        from app.models.warehouse import WarehouseNodeType

        if value not in WarehouseNodeType.ALL:
            raise ValueError(f"unsupported warehouse node type: {value}")
        return value


class WarehouseEdgeIn(BaseModel):
    from_node: str
    to_node: str
    cost: float
    blocked: bool = False
