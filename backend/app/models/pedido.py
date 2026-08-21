from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base
from app.models.enums import StatusPedidoEnum


class Pedido(Base):
    """Solicitação de material feita pelo setor — criada pelo formulário
    PÚBLICO (sem login) e executada pela equipe do almoxarifado."""

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True)

    setor_id = Column(Integer, ForeignKey("setores.id"), nullable=False, index=True)
    responsavel_solicitante = Column(String(150), nullable=False)
    observacao = Column(Text, nullable=True)

    data_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    status = Column(
        Enum(StatusPedidoEnum, name="status_pedido_enum", native_enum=False, length=15),
        nullable=False,
        default=StatusPedidoEnum.pendente,
        server_default=StatusPedidoEnum.pendente.value,
        index=True,
    )
    data_execucao = Column(DateTime(timezone=True), nullable=True)
    usuario_execucao_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # lazy="selectin": mesmo cuidado documentado em app/models/lote.py —
    # `setor_id` é obrigatório, mas `usuario_execucao_id` é opcional
    # (só preenchido quando o pedido é finalizado).
    setor = relationship("Setor", lazy="selectin")
    usuario_execucao = relationship(
        "Usuario", foreign_keys=[usuario_execucao_id], lazy="selectin"
    )
    itens = relationship(
        "PedidoItem",
        back_populates="pedido",
        lazy="selectin",
        order_by="PedidoItem.id",
    )
