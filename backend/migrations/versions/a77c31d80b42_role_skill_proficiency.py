"""Store explicit target proficiency in career catalog requirements.

Revision ID: a77c31d80b42
Revises: 9e2d7c4a1f60
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a77c31d80b42"
down_revision: str | Sequence[str] | None = "9e2d7c4a1f60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("role_skill_requirements") as batch_op:
        batch_op.add_column(
            sa.Column("required_proficiency", sa.Integer(), nullable=True)
        )
    op.execute(
        """
        UPDATE role_skill_requirements
        SET required_proficiency = CASE
            WHEN importance_level >= 5 THEN 4
            WHEN importance_level >= 3 THEN 3
            WHEN importance_level = 2 THEN 2
            ELSE 1
        END
        """
    )
    with op.batch_alter_table("role_skill_requirements") as batch_op:
        batch_op.alter_column("required_proficiency", nullable=False)
        batch_op.create_check_constraint(
            "ck_role_skill_required_proficiency",
            "required_proficiency BETWEEN 1 AND 5",
        )


def downgrade() -> None:
    with op.batch_alter_table("role_skill_requirements") as batch_op:
        batch_op.drop_constraint(
            "ck_role_skill_required_proficiency",
            type_="check",
        )
        batch_op.drop_column("required_proficiency")
