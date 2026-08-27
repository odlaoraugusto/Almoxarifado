"""fabricante (opcional) no cadastro de item

Revision ID: 0006_item_fabricante
Revises: 0005_admin_e_permissoes
Create Date: 2026-08-27

Pedido do cliente: dado de cadastro novo no catálogo de itens — não
obrigatório (nem todo item tem um fabricante identificável, ex. material
de expediente genérico), mas precisa existir no schema pra quem tem.
Texto livre, sem CHECK CONSTRAINT (não é uma lista fechada como
`categoria`).
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0006_item_fabricante"
down_revision: Union[str, None] = "0005_admin_e_permissoes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("itens", sa.Column("fabricante", sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column("itens", "fabricante")
