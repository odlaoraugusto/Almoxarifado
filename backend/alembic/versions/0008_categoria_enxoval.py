"""adiciona categoria 'enxoval'

Revision ID: 0008_categoria_enxoval
Revises: 0007_item_valor_unitario
Create Date: 2026-08-28

Pedido do cliente: 5ª categoria fixa de item — roupa de cama/hospitalar
(lençol, fronha, avental de tecido, etc.), que não se encaixava direito
em nenhuma das 4 anteriores.

Diferente das migrações 0002/0003/0005 (Enum inline que nunca criou
CHECK CONSTRAINT de verdade), a constraint `categoria_item_enum` desta
coluna FOI criada explicitamente na migração 0004
(`op.create_check_constraint`, fora do `create_table`) — então essa
aqui é uma correção real: precisa DROPAR a constraint de 4 valores
antes de criar a nova de 5, a mesma pegadinha não se aplica.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0008_categoria_enxoval"
down_revision: Union[str, None] = "0007_item_valor_unitario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATEGORIAS_ANTIGAS = ("material_medico", "epi", "higienizacao", "expediente")
_CATEGORIAS_NOVAS = (*_CATEGORIAS_ANTIGAS, "enxoval")


def upgrade() -> None:
    op.drop_constraint("categoria_item_enum", "itens", type_="check")
    op.create_check_constraint("categoria_item_enum", "itens", sa.column("categoria").in_(_CATEGORIAS_NOVAS))


def downgrade() -> None:
    # Itens já cadastrados como "enxoval" caem em "expediente" (categoria
    # "outros" mais genérica) — mesmo critério do backfill da 0004.
    op.execute("UPDATE itens SET categoria = 'expediente' WHERE categoria = 'enxoval'")
    op.drop_constraint("categoria_item_enum", "itens", type_="check")
    op.create_check_constraint("categoria_item_enum", "itens", sa.column("categoria").in_(_CATEGORIAS_ANTIGAS))
