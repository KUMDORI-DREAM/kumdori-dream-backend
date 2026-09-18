import pytest
from pydantic import ValidationError

from app.schemas.route import WarehouseNodeIn


def test_warehouse_node_defaults_to_aisle_type():
    node = WarehouseNodeIn(id="A01", x=1.0, y=2.0)

    assert node.node_type == "AISLE"


@pytest.mark.parametrize("node_type", ["ENTRANCE", "LOADING", "STORAGE", "CHARGING"])
def test_warehouse_node_accepts_known_types(node_type):
    node = WarehouseNodeIn(id="A01", node_type=node_type, x=1.0, y=2.0)

    assert node.node_type == node_type


def test_warehouse_node_rejects_unknown_type():
    with pytest.raises(ValidationError, match="unsupported warehouse node type"):
        WarehouseNodeIn(id="A01", node_type="ROOFTOP", x=1.0, y=2.0)
