"""baixa de lote por vencimento (descarte)

Revision ID: 0010_descarte_vencimento
Revises: 0009_pedido_devolucao
Create Date: 2026-09-02

Pedido do cliente: uma forma dedicada de dar baixa num lote vencido —
antes só existia o Ajuste (correção de contagem física, aceita saldo
pra cima ou pra baixo), sem segregar "perdi isso porque venceu" da
trilha de divergência normal.

`movimentacoes.motivo_descarte` (paralelo a `motivo_ajuste`, já
existente) guarda o motivo obrigatório quando `tipo=descarte` (novo
valor de `TipoMovimentacaoEnum`, coluna já é VARCHAR/native_enum=False,
não precisa de migração própria pro enum em si).

`permissoes_perfil.descarte_vencimento` — nova chave configurável na
matriz (`/permissoes`, exclusiva do Admin), mesmo padrão de
`ajustar_estoque`. Nasce `false` pros dois perfis configuráveis
(Coordenador/Atendente) — Admin libera depois pela tela."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0010_descarte_vencimento"
down_revision: Union[str, None] = "0009_pedido_devolucao"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("movimentacoes", sa.Column("motivo_descarte", sa.Text(), nullable=True))
    op.add_column(
        "permissoes_perfil",
        sa.Column("descarte_vencimento", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("permissoes_perfil", "descarte_vencimento")
    op.drop_column("movimentacoes", "motivo_descarte")
