"""adiciona status 'parcial' aos pedidos

Revision ID: 0002_status_pedido_parcial
Revises: 0001_schema_inicial
Create Date: 2026-08-23

Pedido do cliente: quando o pedido não for entregue na totalidade
(ex.: pediu 2, entregou 1), o status deve refletir isso como "parcial"
em vez de aparecer como "executado".

Nota: apesar de `pedidos.status` usar `sa.Enum(..., native_enum=False)`
no model (mesmo padrão "VARCHAR + CHECK" da farmácia, pra evitar
ALTER TYPE), conferido direto no banco da instalação real (`\d pedidos`)
não existe NENHUMA CHECK CONSTRAINT na coluna — é só VARCHAR(15) livre.
Aparentemente o Enum inline dentro de `op.create_table` não emitiu a
constraint em `0001_schema_inicial` (limitação do Alembic com o tipo
instanciado ali, não reproduzida ao gerar `--sql` offline em isolamento
— só percebida ao rodar de verdade). Por isso esta migração não tenta
`drop_constraint` de algo que não existe — só cria a constraint (agora
sim, valendo pra frente) já com os 3 valores.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_status_pedido_parcial"
down_revision: Union[str, None] = "0001_schema_inicial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
