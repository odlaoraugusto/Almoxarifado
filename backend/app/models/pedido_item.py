from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class PedidoItem(Base):
    """Um item dentro de um pedido — conferido individualmente
    (docs/00_PROJETO_ALMOXARIFADO.md, seção 4). `quantidade_entregue`
    fica `None` até a conferência; a partir daí (mesmo que 0, quando o
    almoxarifado não tem o item para liberar) o item é considerado
    conferido — ver `PedidoService.conferir_item`."""

    __tablename__ = "pedido_itens"

    id = Column(Integer, primary_key=True)

    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)

    item_id_solicitado = Column(Integer, ForeignKey("itens.id"), nullable=False)
    quantidade_solicitada = Column(Integer, nullable=False)

    item_id_entregue = Column(Integer, ForeignKey("itens.id"), nullable=True)
    quantidade_entregue = Column(Integer, nullable=True)

    # Obrigatório (validado no service) quando item_id_entregue difere de
    # item_id_solicitado — registra por que o almoxarifado substituiu o
    # item pedido por outro do catálogo.
    motivo_substituicao = Column(Text, nullable=True)

    # lazy="selectin": mesmo cuidado documentado em app/models/lote.py —
    # item_id_entregue é opcional (nulo até a conferência).
    pedido = relationship("Pedido", back_populates="itens", lazy="selectin")
    item_solicitado = relationship(
        "Item", foreign_keys=[item_id_solicitado], lazy="selectin"
    )
    item_entregue = relationship(
        "Item", foreign_keys=[item_id_entregue], lazy="selectin"
    )

    # Movimentações de saída que baixaram este item de pedido (FEFO pode
    # consumir mais de um lote pra uma única conferência) — usado pelo
    # relatório de Pedidos para mostrar lote/validade do que foi
    # efetivamente entregue, sobretudo quando houve substituição
    # (2026-08-31, pedido do cliente). `viewonly=True`: é só leitura, a
    # gravação de Movimentacao continua pelo fluxo normal em
    # PedidoService/ConsumoFefoService.
    movimentacoes = relationship("Movimentacao", viewonly=True, lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "quantidade_solicitada > 0", name="ck_pedido_itens_quantidade_solicitada_positiva"
        ),
        CheckConstraint(
            "quantidade_entregue IS NULL OR quantidade_entregue >= 0",
            name="ck_pedido_itens_quantidade_entregue_nao_negativa",
        ),
    )
