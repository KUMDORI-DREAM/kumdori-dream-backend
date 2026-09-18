"""add robot name and warehouse node name/type"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("robots", sa.Column("name", sa.String(100), nullable=True))
    op.add_column("warehouse_nodes", sa.Column("name", sa.String(100), nullable=True))
    op.add_column(
        "warehouse_nodes",
        sa.Column("node_type", sa.String(16), nullable=False, server_default="AISLE"),
    )


def downgrade() -> None:
    op.drop_column("warehouse_nodes", "node_type")
    op.drop_column("warehouse_nodes", "name")
    op.drop_column("robots", "name")
