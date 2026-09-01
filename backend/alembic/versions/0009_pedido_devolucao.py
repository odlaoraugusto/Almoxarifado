"""tipo de pedido (entrega/devolução) + origem de lote 'devolucao'

Revision ID: 0009_pedido_devolucao
Revises: 0008_categoria_enxoval
Create Date: 2026-09-01

Pedido do cliente: o formulário público de pedido ganha uma opção
"Entrega" (padrão, comportamento de sempre — baixa estoque na
conferência) ou "Devolução" (o setor está devolvendo material ao
almoxarifado — a conferência CRIA lote(s) novo(s) em vez de baixar,
igual a uma Entrada, ver `PedidoService.conferir_item`).

Nova coluna `pedidos.tipo` (mesmo padrão VARCHAR + CHECK explícito das
migrações 0002/0003 — o Enum inline dentro de `create_table`/`add_column`
não confiavelmente cria a constraint sozinho) e novo valor `devolucao`
em `origem_enum` (coluna `lotes.origem`), para os lotes criados por essa
conferência."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0009_pedido_devolucao"
down_revision: Union[str, None] = "0008_categoria_enxoval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pedidos",
        sa.Column("tipo", sa.String(length=15), nullable=False, server_default="entrega"),
    )
    op.create_check_constraint(
        "tipo_pedido_enum",
        "pedidos",
        sa.column("tipo").in_(("entrega", "devolucao")),
    )

    op.drop_constraint("origem_enum", "lotes", type_="check")
    op.create_check_constraint(
        "origem_enum",
        "lotes",
        sa.column("origem").in_(("compra", "doacao", "emprestimo", "devolucao")),
    )


def downgrade() -> None:
    # Lotes já criados com origem='devolucao' (por uma conferência de
    # pedido tipo=devolucao) viram 'doacao' no downgrade — mais próximo
    # semanticamente (valor não pago) — ANTES de recriar a constraint de
    # 3 valores, senão a UPDATE abaixo violaria a constraint nova.
    op.execute("UPDATE lotes SET origem = 'doacao' WHERE origem = 'devolucao'")

    op.drop_constraint("origem_enum", "lotes", type_="check")
    op.create_check_constraint(
        "origem_enum",
        "lotes",
        sa.column("origem").in_(("compra", "doacao", "emprestimo")),
    )

    op.drop_constraint("tipo_pedido_enum", "pedidos", type_="check")
    op.drop_column("pedidos", "tipo")
