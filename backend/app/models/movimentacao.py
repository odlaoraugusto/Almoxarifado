from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base
from app.models.enums import TipoMovimentacaoEnum


class Movimentacao(Base):
    """Trilha de auditoria de estoque — nunca se apaga uma linha desta
    tabela.

    `quantidade`: magnitude sempre positiva em `entrada`/`saida`; em
    `ajuste` guarda o DELTA com sinal (positivo = aumento, negativo =
    redução) — mesmo padrão já resolvido na farmácia
    (`app/models/movimentacao.py` de lá), por isso não há CHECK de
    "sempre positivo" aqui."""

    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True)

    tipo = Column(
        Enum(TipoMovimentacaoEnum, name="tipo_movimentacao_enum", native_enum=False, length=10),
        nullable=False,
        index=True,
    )

    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)

    # Liga à conferência de um item de pedido específico — preenchido em
    # tipo=saida (pedido comum, `Pedido.tipo=entrega`, baixa via FEFO) OU
    # tipo=entrada (pedido `Pedido.tipo=devolucao`, 2026-09-01: o setor
    # devolveu material, a conferência criou um lote novo). Nulo em
    # ajuste, e nulo também quando a movimentação veio de um empréstimo
    # (ver emprestimo_id abaixo) — os dois são mutuamente opcionais,
    # nunca preenchidos ao mesmo tempo na prática.
    pedido_item_id = Column(Integer, ForeignKey("pedido_itens.id"), nullable=True)

    # Preenchido só quando tipo=saida e a baixa veio de um empréstimo
    # enviado (direcao=saida) — paralelo a pedido_item_id. Nulo em
    # entrada/ajuste e nas saídas de pedido.
    emprestimo_id = Column(Integer, ForeignKey("emprestimos.id"), nullable=True)

    # Obrigatório (validado no service) quando tipo=ajuste — motivo da
    # correção de saldo fora do fluxo normal (ex. divergência de
    # contagem física). Nulo para entrada/saida.
    motivo_ajuste = Column(Text, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    data_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # lazy="selectin": mesmo cuidado documentado em app/models/lote.py —
    # `pedido_item_id`/`emprestimo_id` são opcionais.
    lote = relationship("Lote", lazy="selectin")
    pedido_item = relationship("PedidoItem", lazy="selectin")
    emprestimo = relationship(
        "RegistroEmprestimo", back_populates="movimentacoes", lazy="selectin"
    )
    usuario = relationship("Usuario", foreign_keys=[usuario_id], lazy="selectin")
