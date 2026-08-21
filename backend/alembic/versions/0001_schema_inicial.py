"""schema inicial — usuarios, setores, itens, lotes, pedidos, pedido_itens, movimentacoes

Revision ID: 0001_schema_inicial
Revises:
Create Date: 2026-08-21

Cria o schema completo descrito em docs/00_PROJETO_ALMOXARIFADO.md, seção 4.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_schema_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("login", sa.String(length=50), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "perfil",
            sa.Enum(
                "coordenador", "atendente", name="perfil_enum", native_enum=False, length=20
            ),
            nullable=False,
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "deve_trocar_senha", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("login", name="uq_usuarios_login"),
    )
    op.create_index("ix_usuarios_login", "usuarios", ["login"])

    op.create_table(
        "setores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("nome", name="uq_setores_nome"),
    )

    op.create_table(
        "itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=30), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("apresentacao", sa.String(length=100), nullable=False),
        sa.Column("categoria", sa.String(length=60), nullable=False),
        sa.Column("estoque_minimo", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("codigo", name="uq_itens_codigo"),
    )
    op.create_index("ix_itens_codigo", "itens", ["codigo"])

    op.create_table(
        "lotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("numero_lote", sa.String(length=50), nullable=True),
        sa.Column("data_validade", sa.Date(), nullable=True),
        sa.Column("quantidade_atual", sa.Integer(), nullable=False),
        sa.Column("valor_unitario", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "origem",
            sa.Enum("compra", "doacao", name="origem_enum", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("numero_nota_fiscal", sa.String(length=50), nullable=True),
        sa.Column(
            "data_entrada",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "usuario_entrada_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.CheckConstraint(
            "quantidade_atual >= 0", name="ck_lotes_quantidade_nao_negativa"
        ),
    )
    op.create_index("ix_lotes_item_id", "lotes", ["item_id"])

    op.create_table(
        "pedidos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("setor_id", sa.Integer(), sa.ForeignKey("setores.id"), nullable=False),
        sa.Column("responsavel_solicitante", sa.String(length=150), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column(
            "data_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pendente", "executado", name="status_pedido_enum", native_enum=False, length=15
            ),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column("data_execucao", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "usuario_execucao_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True
        ),
    )
    op.create_index("ix_pedidos_setor_id", "pedidos", ["setor_id"])
    op.create_index("ix_pedidos_status", "pedidos", ["status"])

    op.create_table(
        "pedido_itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pedido_id", sa.Integer(), sa.ForeignKey("pedidos.id"), nullable=False),
        sa.Column(
            "item_id_solicitado", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False
        ),
        sa.Column("quantidade_solicitada", sa.Integer(), nullable=False),
        sa.Column("item_id_entregue", sa.Integer(), sa.ForeignKey("itens.id"), nullable=True),
        sa.Column("quantidade_entregue", sa.Integer(), nullable=True),
        sa.Column("motivo_substituicao", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "quantidade_solicitada > 0", name="ck_pedido_itens_quantidade_solicitada_positiva"
        ),
        sa.CheckConstraint(
            "quantidade_entregue IS NULL OR quantidade_entregue >= 0",
            name="ck_pedido_itens_quantidade_entregue_nao_negativa",
        ),
    )
    op.create_index("ix_pedido_itens_pedido_id", "pedido_itens", ["pedido_id"])

    op.create_table(
        "movimentacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tipo",
            sa.Enum(
                "entrada", "saida", "ajuste", name="tipo_movimentacao_enum",
                native_enum=False, length=10,
            ),
            nullable=False,
        ),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lotes.id"), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column(
            "pedido_item_id", sa.Integer(), sa.ForeignKey("pedido_itens.id"), nullable=True
        ),
        sa.Column("motivo_ajuste", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column(
            "data_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index("ix_movimentacoes_tipo", "movimentacoes", ["tipo"])
    op.create_index("ix_movimentacoes_lote_id", "movimentacoes", ["lote_id"])


def downgrade() -> None:
    op.drop_index("ix_movimentacoes_lote_id", table_name="movimentacoes")
    op.drop_index("ix_movimentacoes_tipo", table_name="movimentacoes")
    op.drop_table("movimentacoes")

    op.drop_index("ix_pedido_itens_pedido_id", table_name="pedido_itens")
    op.drop_table("pedido_itens")

    op.drop_index("ix_pedidos_status", table_name="pedidos")
    op.drop_index("ix_pedidos_setor_id", table_name="pedidos")
    op.drop_table("pedidos")

    op.drop_index("ix_lotes_item_id", table_name="lotes")
    op.drop_table("lotes")

    op.drop_index("ix_itens_codigo", table_name="itens")
    op.drop_table("itens")

    op.drop_table("setores")

    op.drop_index("ix_usuarios_login", table_name="usuarios")
    op.drop_table("usuarios")
