"""adiciona status 'parcial' aos pedidos

Revision ID: 0002_status_pedido_parcial
Revises: 0001_schema_inicial
Create Date: 2026-08-23

Pedido do cliente: quando o pedido não for entregue na totalidade
(ex.: pediu 2, entregou 1), o status deve refletir isso como "parcial"
em vez de aparecer como "executado". `pedidos.status` era
VARCHAR + CHECK CONSTRAINT (native_enum=False, mesmo padrão da
farmácia — evita ALTER TYPE), então basta trocar a constraint pra
aceitar o valor novo, sem tocar em dado existente.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_status_pedido_parcial"
down_revision: Union[str, None] = "0001_schema_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("status_pedido_enum", "pedidos", type_="check")
    op.create_check_constraint(
        "status_pedido_enum",
        "pedidos",
        sa.column("status").in_(("pendente", "parcial", "executado")),
    )


def downgrade() -> None:
    # Pedidos já marcados como "parcial" viram "pendente" no downgrade —
    # não existe outro valor do enum antigo que represente "entregue só
    # em parte" com segurança (virar "executado" mentiria sobre a
    # entrega completa).
    op.execute("UPDATE pedidos SET status = 'pendente' WHERE status = 'parcial'")
    op.drop_constraint("status_pedido_enum", "pedidos", type_="check")
    op.create_check_constraint(
        "status_pedido_enum",
        "pedidos",
        sa.column("status").in_(("pendente", "executado")),
    )
