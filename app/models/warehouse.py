from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WarehouseNodeType:
    """로봇 이동/작업과 관련된 창고 지점의 역할.

    맵 위에서 통로 경유 지점과 충전소·입고·적재·보관 구역을 구분해 표시하기
    위한 것으로, 경로 탐색 로직에는 영향을 주지 않는다.
    """

    AISLE = "AISLE"
    ENTRANCE = "ENTRANCE"
    LOADING = "LOADING"
    STORAGE = "STORAGE"
    CHARGING = "CHARGING"

    ALL = (AISLE, ENTRANCE, LOADING, STORAGE, CHARGING)


class WarehouseNode(Base):
    __tablename__ = "warehouse_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    node_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=WarehouseNodeType.AISLE,
        server_default=WarehouseNodeType.AISLE,
    )
    aisle: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)


class WarehouseEdge(Base):
    __tablename__ = "warehouse_edges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_node: Mapped[str] = mapped_column(ForeignKey("warehouse_nodes.id", ondelete="CASCADE"))
    to_node: Mapped[str] = mapped_column(ForeignKey("warehouse_nodes.id", ondelete="CASCADE"))
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    blocked: Mapped[bool] = mapped_column(default=False, nullable=False)
