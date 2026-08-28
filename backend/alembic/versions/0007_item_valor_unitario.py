"""valor_unitario (opcional) no cadastro de item

Revision ID: 0007_item_valor_unitario
Revises: 0006_item_fabricante
Create Date: 2026-08-28

Pedido do cliente: preço de REFERÊNCIA do item no catálogo — opcional,
independente do `Lote.valor_unitario` de cada compra (que varia por
nota fiscal). Não é o mesmo dado, é só mais um campo editável no
cadastro do item, igual a `fabricante` (migration 0006).
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0007_item_valor_unitario"
down_revision: Union[str, None] = "0006_item_fabricante"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("itens", sa.Column("valor_unitario", sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column("itens", "valor_unitario")
