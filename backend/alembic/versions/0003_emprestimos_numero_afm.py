"""numero_afm em lotes + módulo de Empréstimos e Permutas

Revision ID: 0003_emprestimos_numero_afm
Revises: 0002_status_pedido_parcial
Create Date: 2026-08-22

Duas frentes independentes nesta migração:

1. `lotes.numero_afm` — número de autorização usado em compras
   (opcional, mesmo conceito do projeto irmão da farmácia), ao lado de
   `numero_nota_fiscal`.

2. Empréstimo/permuta com unidade EXTERNA (fora do catálogo de
   `setores`): tabela `emprestimos` nova + `emprestimo_id` (FK opcional)
   em `lotes` e `movimentacoes`, e o enum de `origem` em `lotes` ganha o
   valor `emprestimo`.

Nota sobre CHECK CONSTRAINT de enum (mesma pegadinha já documentada em
`0002_status_pedido_parcial`): `sa.Enum(..., native_enum=False)` inline
dentro de `sa.Column(...)` dentro de `op.create_table(...)` NÃO gera a
CHECK CONSTRAINT de verdade quando a migração roda contra um Postgres
real (só o `--sql` offline "finge" que geraria) — é uma limitação real
do Alembic com Enum instanciado inline, não reproduzida em isolamento.
Por isso:

- A tabela `emprestimos` é criada com o tipo da coluna `direcao` via
  Enum inline (só para gerar VARCHAR(10) com o comprimento certo), e a
  CHECK CONSTRAINT é criada numa chamada própria e explícita logo em
  seguida (`op.create_check_constraint`), nunca confiando que o
  `create_table` já criou.
- Aproveitando que `origem_enum` (coluna `lotes.origem`, criada em
  `0001_schema_inicial` do mesmíssimo jeito problemático) muito
  provavelmente também NUNCA teve CHECK CONSTRAINT de verdade em
  produção — não foi possível confirmar com `\\d lotes` direto no
  Postgres da VPS nesta rodada (sem acesso), então fica registrada aqui
  como suposição, no mesmo espírito de `0002` — esta migração cria (não
  substitui) a constraint de `origem`, já com os 3 valores válidos
  (`compra`, `doacao`, `emprestimo`). Se por acaso a constraint antiga
  já existir com nome diferente, `create_check_constraint` falha alto e
  visível em vez de mascarar o problema.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003_emprestimos_numero_afm"
down_revision: Union[str, None] = "0002_status_pedido_parcial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. numero_afm em lotes ---------------------------------------
    op.add_column("lotes", sa.Column("numero_afm", sa.String(length=50), nullable=True))

    # --- 2. tabela emprestimos -----------------------------------------
    op.create_table(
        "emprestimos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "direcao",
            sa.Enum(
                "entrada", "saida", name="direcao_emprestimo_enum",
                native_enum=False, length=10,
            ),
            nullable=False,
        ),
        sa.Column("unidade_origem", sa.String(length=150), nullable=False),
        sa.Column("numero_oficio", sa.String(length=50), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column(
            "data_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    # Enum inline em create_table não gera a CHECK de verdade (ver nota no
    # topo do arquivo) — cria explicitamente.
    op.create_check_constraint(
        "direcao_emprestimo_enum",
        "emprestimos",
        sa.column("direcao").in_(("entrada", "saida")),
    )

    # --- 3. emprestimo_id (FK opcional) em lotes e movimentacoes -------
    op.add_column(
        "lotes",
        sa.Column("emprestimo_id", sa.Integer(), sa.ForeignKey("emprestimos.id"), nullable=True),
    )
    op.create_index("ix_lotes_emprestimo_id", "lotes", ["emprestimo_id"])

    op.add_column(
        "movimentacoes",
        sa.Column("emprestimo_id", sa.Integer(), sa.ForeignKey("emprestimos.id"), nullable=True),
    )
    op.create_index("ix_movimentacoes_emprestimo_id", "movimentacoes", ["emprestimo_id"])

    # --- 4. amplia (e cria de verdade) a CHECK de lotes.origem ----------
    op.create_check_constraint(
        "origem_enum",
        "lotes",
        sa.column("origem").in_(("compra", "doacao", "emprestimo")),
    )


def downgrade() -> None:
    op.drop_constraint("origem_enum", "lotes", type_="check")

    op.drop_index("ix_movimentacoes_emprestimo_id", table_name="movimentacoes")
    op.drop_column("movimentacoes", "emprestimo_id")

    op.drop_index("ix_lotes_emprestimo_id", table_name="lotes")
    op.drop_column("lotes", "emprestimo_id")

    op.drop_constraint("direcao_emprestimo_enum", "emprestimos", type_="check")
    op.drop_table("emprestimos")

    op.drop_column("lotes", "numero_afm")
