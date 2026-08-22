"""categoria de item vira lista fechada (Material Médico/EPI/Higienização/Expediente)

Revision ID: 0004_categoria_item_fixa
Revises: 0003_emprestimos_numero_afm
Create Date: 2026-08-23

Pedido do cliente: `itens.categoria` era texto livre (o Coordenador
digitava qualquer coisa, ex. "Mat. Med.", "EPI/SIAST", "Higienização" —
dados de teste já cadastrados assim). Vira lista fechada de 4 valores.

Backfill dos dados de teste conhecidos antes de travar a coluna com a
CHECK CONSTRAINT (mesmo padrão já usado no projeto irmão da farmácia
pra esse tipo de migração — normaliza o que já existe, senão o
`ALTER COLUMN`/constraint nova rejeitaria linha existente fora do enum
novo). Qualquer outro valor não mapeado cai em "expediente" (categoria
"outros" mais genérica) — comportamento esperado só em dados de teste,
não deveria acontecer numa instalação real que já nasce com a lista
fechada.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0004_categoria_item_fixa"
down_revision: Union[str, None] = "0003_emprestimos_numero_afm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATEGORIAS = ("material_medico", "epi", "higienizacao", "expediente")

_BACKFILL = {
    "material_medico": ["Mat. Med.", "Material Médico", "Material Medico"],
    "epi": ["EPI/SIAST", "EPI"],
    "higienizacao": ["Higienização", "Higienizacao", "Higiene"],
}


def upgrade() -> None:
    for categoria_nova, valores_antigos in _BACKFILL.items():
        lista = ", ".join(repr(v) for v in valores_antigos)
        op.execute(f"UPDATE itens SET categoria = '{categoria_nova}' WHERE categoria IN ({lista})")

    # Qualquer coisa que sobrou fora da lista nova (incluindo já estar
    # certo, o que essa condição também cobre sem problema) cai em
    # "expediente" — só afeta dados de teste com categoria digitada à
    # mão fora do padrão dos três mapeamentos acima.
    lista_nova = ", ".join(repr(v) for v in _CATEGORIAS)
    op.execute(f"UPDATE itens SET categoria = 'expediente' WHERE categoria NOT IN ({lista_nova})")

    op.alter_column("itens", "categoria", type_=sa.String(length=20), existing_type=sa.String(length=60))
    op.create_check_constraint("categoria_item_enum", "itens", sa.column("categoria").in_(_CATEGORIAS))


def downgrade() -> None:
    op.drop_constraint("categoria_item_enum", "itens", type_="check")
    op.alter_column("itens", "categoria", type_=sa.String(length=60), existing_type=sa.String(length=20))
