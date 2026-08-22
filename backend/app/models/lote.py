from sqlalchemy import CheckConstraint, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base
from app.models.enums import OrigemEnum


class Lote(Base):
    """Estoque físico de verdade — cada lote pertence a UM item do
    catálogo. Sem `unidade_id`/`status_transferencia` (diferente da
    farmácia): o almoxarifado tem um único estoque central, sem
    transferência entre unidades (docs/00_PROJETO_ALMOXARIFADO.md,
    seção 4).

    `numero_lote`/`data_validade`/`valor_unitario` são opcionais — nem
    todo material de almoxarifado tem lote formal ou vencimento (ex.
    material de expediente)."""

    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True)

    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False, index=True)

    numero_lote = Column(String(50), nullable=True)
    data_validade = Column(Date, nullable=True)

    quantidade_atual = Column(Integer, nullable=False)
    valor_unitario = Column(Numeric(12, 2), nullable=True)

    origem = Column(
        Enum(OrigemEnum, name="origem_enum", native_enum=False, length=10),
        nullable=False,
    )
    numero_nota_fiscal = Column(String(50), nullable=True)
    # Número de autorização usado em compras (mesmo conceito do projeto
    # irmão da farmácia) — opcional, não confundir com numero_nota_fiscal.
    numero_afm = Column(String(50), nullable=True)

    # Preenchido só quando o lote nasceu de uma entrada via
    # empréstimo/permuta (origem='emprestimo') — nulo para compra/doação.
    emprestimo_id = Column(Integer, ForeignKey("emprestimos.id"), nullable=True)

    data_entrada = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario_entrada_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # lazy="selectin" (não "joined"/padrão implícito de eager loading):
    # `get_by_id_for_update()` usa `SELECT ... FOR UPDATE`, que o Postgres
    # recusa quando a query tem LEFT OUTER JOIN em FK opcional — mesmo
    # cuidado documentado no projeto irmão (app/models/lote.py da
    # farmácia), reaplicado aqui porque `usuario_entrada_id`/`item_id`/
    # `emprestimo_id` participariam de um JOIN se o lazy padrão fosse
    # usado num relacionamento eager.
    item = relationship("Item", lazy="selectin")
    usuario_entrada = relationship("Usuario", foreign_keys=[usuario_entrada_id], lazy="selectin")
    emprestimo = relationship(
        "RegistroEmprestimo", back_populates="lotes_criados", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("quantidade_atual >= 0", name="ck_lotes_quantidade_nao_negativa"),
    )
