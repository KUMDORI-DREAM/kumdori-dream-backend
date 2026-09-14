from pathlib import Path

# Keep one implementation for both the legacy patrol controller and the warehouse controller.
exec((Path(__file__).parents[1] / "patrol_robot_controller" / "edge_agent.py").read_text())
