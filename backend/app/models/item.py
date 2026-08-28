from sqlalchemy import Boolean, Column, Enum, Integer, Numeric, String

from app.database.database import Base
from app.models.enums import CategoriaItemEnum


class Item(Base):
    """Catálogo de materiais do almoxarifado — cadastro geral, NÃO é o
    saldo em si (o saldo físico mora em `Lote`, docs/00_PROJETO_ALMOXARIFADO.md
    seção 4). `apresentacao` continua texto livre; `categoria` é lista
    fechada (`CategoriaItemEnum`, pedido do cliente — antes era texto
    livre tipo "Mat. Med."/"EPI/SIAST", ver migration 0004)."""

    __tablename__ = "itens"

    id = Column(Integer, primary_key=True)

    codigo = Column(String(30), unique=True, nullable=False, index=True)
    nome = Column(String(200), nullable=False)
    apresentacao = Column(String(100), nullable=False)
    categoria = Column(
        Enum(CategoriaItemEnum, name="categoria_item_enum", native_enum=False, length=20),
        nullable=False,
    )

    estoque_minimo = Column(Integer, nullable=False, default=0, server_default="0")

    # Opcional — nem todo item tem um fabricante identificável (ex.
    # material de expediente genérico), mas o campo precisa existir pra
    # quem tem (pedido do cliente).
    fabricante = Column(String(150), nullable=True)

    # Preço de REFERÊNCIA do item no catálogo — opcional, independente do
    # `Lote.valor_unitario` de cada compra (que varia por nota fiscal).
    # Pedido do cliente: um valor editável a qualquer momento pelo
    # cadastro do item, sem precisar existir lote nenhum.
    valor_unitario = Column(Numeric(12, 2), nullable=True)

    # Não faz parte da lista literal da seção 4 do doc, mas evita exclusão
    # física do cadastro (que quebraria FK de lotes/pedido_itens
    # históricos) — descontinuar um item vira "inativo" em vez de DELETE,
    # mesmo precedente já adotado no projeto irmão (farmácia).
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
