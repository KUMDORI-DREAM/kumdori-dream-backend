from pathlib import Path

# 기존 순찰 컨트롤러와 창고 컨트롤러가 동일한 구현을 사용하도록 한다.
exec(
    (Path(__file__).parents[1] / "patrol_robot_controller" / "edge_agent.py").read_text(
        encoding="utf-8"
    )
)
