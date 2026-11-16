"""Eventos documentados también en inglés (título y descripción).

Revision ID: b7e1f0a2c3d4
Revises: dca3e6477a3d
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e1f0a2c3d4"
down_revision: str | None = "dca3e6477a3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("eventos_documentados") as t:
        t.add_column(sa.Column("titulo_en", sa.String(200), nullable=True))
        t.add_column(sa.Column("descripcion_en", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("eventos_documentados") as t:
        t.drop_column("descripcion_en")
        t.drop_column("titulo_en")
