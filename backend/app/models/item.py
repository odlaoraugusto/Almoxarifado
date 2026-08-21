from sqlalchemy import Boolean, Column, Integer, String

from app.database.database import Base


class Item(Base):
    """Catálogo de materiais do almoxarifado — cadastro geral, NÃO é o
    saldo em si (o saldo físico mora em `Lote`, docs/00_PROJETO_ALMOXARIFADO.md
    seção 4). `apresentacao`/`categoria` são texto livre (não enum): a
    lista de categorias é definida pelo Coordenador na prática (ex. "Mat.
    Med.", "EPI/SIAST", "Higienização" — ver docs/prototipo_formulario_publico.html)
    e pode crescer sem exigir migração, mesmo raciocínio já documentado no
    projeto irmão para evitar `ALTER TYPE`."""

    __tablename__ = "itens"

    id = Column(Integer, primary_key=True)

    codigo = Column(String(30), unique=True, nullable=False, index=True)
    nome = Column(String(200), nullable=False)
    apresentacao = Column(String(100), nullable=False)
    categoria = Column(String(60), nullable=False)

    estoque_minimo = Column(Integer, nullable=False, default=0, server_default="0")

    # Não faz parte da lista literal da seção 4 do doc, mas evita exclusão
    # física do cadastro (que quebraria FK de lotes/pedido_itens
    # históricos) — descontinuar um item vira "inativo" em vez de DELETE,
    # mesmo precedente já adotado no projeto irmão (farmácia).
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
