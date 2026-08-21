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

    # Preenchido só quando tipo=saida — liga à liberação de um item de
    # pedido específico (conferência). Nulo em entrada/ajuste.
    pedido_item_id = Column(Integer, ForeignKey("pedido_itens.id"), nullable=True)

    # Obrigatório (validado no service) quando tipo=ajuste — motivo da
    # correção de saldo fora do fluxo normal (ex. divergência de
    # contagem física). Nulo para entrada/saida.
    motivo_ajuste = Column(Text, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    data_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # lazy="selectin": mesmo cuidado documentado em app/models/lote.py —
    # `pedido_item_id` é opcional.
    lote = relationship("Lote", lazy="selectin")
    pedido_item = relationship("PedidoItem", lazy="selectin")
    usuario = relationship("Usuario", foreign_keys=[usuario_id], lazy="selectin")
