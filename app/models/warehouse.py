from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WarehouseNode(Base):
    __tablename__ = "warehouse_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
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
