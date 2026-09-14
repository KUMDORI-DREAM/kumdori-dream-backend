"""add warehouse graph, route state, and safety events"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("robots", sa.Column("current_node", sa.String(64), nullable=True))
    op.add_column("robots", sa.Column("target_node", sa.String(64), nullable=True))
    op.create_table(
        "warehouse_nodes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("aisle", sa.String(64), nullable=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
    )
    op.create_index("ix_warehouse_nodes_aisle", "warehouse_nodes", ["aisle"])
    op.create_table(
        "warehouse_edges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("from_node", sa.String(64), nullable=False),
        sa.Column("to_node", sa.String(64), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["from_node"], ["warehouse_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_node"], ["warehouse_nodes.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "safety_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("robot_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="WARNING"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("x", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["robot_id"], ["robots.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_safety_events_robot_id", "safety_events", ["robot_id"])
    op.create_index("ix_safety_events_event_type", "safety_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("safety_events")
    op.drop_table("warehouse_edges")
    op.drop_index("ix_warehouse_nodes_aisle", table_name="warehouse_nodes")
    op.drop_table("warehouse_nodes")
    op.drop_column("robots", "target_node")
    op.drop_column("robots", "current_node")
