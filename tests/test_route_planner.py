import pytest

from app.route_planner import a_star


def test_a_star_returns_lowest_cost_route():
    graph = {
        "A": [("B", 4.0), ("C", 1.0)],
        "C": [("B", 1.0)],
        "B": [],
    }
    coordinates = {"A": (0.0, 0.0), "B": (4.0, 0.0), "C": (1.0, 0.0)}

    assert a_star(graph, coordinates, "A", "B") == ["A", "C", "B"]


def test_a_star_rejects_negative_cost():
    graph = {"A": [("B", -1.0)], "B": []}
    coordinates = {"A": (0.0, 0.0), "B": (1.0, 0.0)}

    with pytest.raises(ValueError, match="non-negative"):
        a_star(graph, coordinates, "A", "B")


def test_a_star_rejects_missing_neighbor_coordinates():
    graph = {"A": [("C", 1.0)], "B": []}
    coordinates = {"A": (0.0, 0.0), "B": (1.0, 0.0)}

    with pytest.raises(ValueError, match="must have coordinates"):
        a_star(graph, coordinates, "A", "B")
