"""Persist linked What-If scenarios and proficiency-aware skill gaps.

Revision ID: 9e2d7c4a1f60
Revises: 6b4a747f80d9
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9e2d7c4a1f60"
down_revision: str | Sequence[str] | None = "6b4a747f80d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("simulations") as batch_op:
        batch_op.add_column(
            sa.Column("parent_simulation_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_simulations_parent_simulation_id_simulations",
            "simulations",
            ["parent_simulation_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_simulations_parent_simulation_id",
            ["parent_simulation_id"],
            unique=False,
        )
    op.add_column(
        "skill_gaps",
        sa.Column("current_proficiency", sa.Integer(), nullable=True),
    )
    op.add_column(
        "skill_gaps",
        sa.Column("required_proficiency", sa.Integer(), nullable=True),
    )
    op.add_column(
        "skill_gaps",
        sa.Column("importance_level", sa.Integer(), nullable=True),
    )
    op.add_column(
        "skill_gaps",
        sa.Column("is_mandatory", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("skill_gaps", "is_mandatory")
    op.drop_column("skill_gaps", "importance_level")
    op.drop_column("skill_gaps", "required_proficiency")
    op.drop_column("skill_gaps", "current_proficiency")
    with op.batch_alter_table("simulations") as batch_op:
        batch_op.drop_index("ix_simulations_parent_simulation_id")
        batch_op.drop_constraint(
            "fk_simulations_parent_simulation_id_simulations",
            type_="foreignkey",
        )
        batch_op.drop_column("parent_simulation_id")
