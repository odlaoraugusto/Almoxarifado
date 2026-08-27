"""perfil 'admin' global + matriz de permissões configurável (coordenador/atendente)

Revision ID: 0005_admin_e_permissoes
Revises: 0004_categoria_item_fixa
Create Date: 2026-08-27

Pedido do cliente: um usuário Admin global que gerencia as permissões
dos outros dois perfis (Coordenador/Atendente) pela própria tela do
sistema, em vez de ficarem fixas no código (`permissoesDe` no frontend
antes tratava tudo como "exclusivo do Coordenador", hardcoded).

Duas frentes:

1. `usuarios.perfil` ganha o valor `admin`. Igual às migrações
   0002/0003 (ver notas lá), o Enum inline de `0001_schema_inicial`
   nunca gerou uma CHECK CONSTRAINT de verdade em Postgres real (só o
   `--sql` offline "finge" que geraria) — então não existe nada pra
   dropar aqui, só criar a constraint (primeira vez de verdade) já com
   os 3 valores.

2. Tabela nova `permissoes_perfil` — uma linha por perfil configurável
   (`coordenador`, `atendente`; o Admin é superusuário implícito, nunca
   tem linha aqui — ver `app/api/deps.py::exigir_permissao`), com um
   boolean por ação controlável. Semeada já com o comportamento que
   existia até aqui (Coordenador = tudo liberado, Atendente = tudo
   bloqueado) pra não mudar nada até o Admin mexer na tela /permissoes.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005_admin_e_permissoes"
down_revision: Union[str, None] = "0004_categoria_item_fixa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUNAS_PERMISSAO = (
    "ajustar_estoque",
    "gerenciar_itens",
    "gerenciar_setores",
    "gestao_usuarios",
    "relatorio_movimentacoes",
)


def upgrade() -> None:
    # --- 1. perfil 'admin' ------------------------------------------------
    op.create_check_constraint(
        "perfil_enum",
        "usuarios",
        sa.column("perfil").in_(("coordenador", "atendente", "admin")),
    )

    # --- 2. matriz de permissões configurável -----------------------------
    op.create_table(
        "permissoes_perfil",
        sa.Column(
            "perfil",
            sa.Enum(
                "coordenador", "atendente", "admin", name="perfil_enum",
                native_enum=False, length=20,
            ),
            primary_key=True,
        ),
        *(
            sa.Column(coluna, sa.Boolean(), nullable=False, server_default=sa.text("false"))
            for coluna in _COLUNAS_PERMISSAO
        ),
    )
    # Mesma pegadinha do Enum inline (ver nota no topo) — cria a CHECK
    # explícita mesmo assim, por consistência com o resto do projeto (a
    # PK sozinha não barra um valor fora da lista escrito via UPDATE
    # direto no banco).
    op.create_check_constraint(
        "permissoes_perfil_perfil_enum",
        "permissoes_perfil",
        sa.column("perfil").in_(("coordenador", "atendente", "admin")),
    )

    # Semente: replica o comportamento hardcoded que existia até aqui.
    permissoes_perfil = sa.table(
        "permissoes_perfil",
        sa.column("perfil", sa.String),
        *(sa.column(c, sa.Boolean) for c in _COLUNAS_PERMISSAO),
    )
    op.bulk_insert(
        permissoes_perfil,
        [
            {"perfil": "coordenador", **{c: True for c in _COLUNAS_PERMISSAO}},
            {"perfil": "atendente", **{c: False for c in _COLUNAS_PERMISSAO}},
        ],
    )


def downgrade() -> None:
    op.drop_table("permissoes_perfil")
    op.drop_constraint("perfil_enum", "usuarios", type_="check")
