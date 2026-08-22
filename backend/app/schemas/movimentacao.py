from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoMovimentacaoEnum
from app.schemas.lote import LoteDetalhadoOut
from app.schemas.usuario import UsuarioResumo


class AjusteCreate(BaseModel):
    """Ajuste de estoque — exclusivo do Coordenador. `quantidade_nova` é o
    saldo correto do lote depois de uma contagem física; o service
    calcula o delta contra o saldo atual, não o cliente (mesmo padrão da
    farmácia)."""

    lote_id: int
    quantidade_nova: int = Field(ge=0)
    motivo_ajuste: str


class MovimentacaoOut(BaseModel):
    id: int
    tipo: TipoMovimentacaoEnum
    lote_id: int
    quantidade: int
    pedido_item_id: int | None
    emprestimo_id: int | None
    motivo_ajuste: str | None
    usuario_id: int
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentacaoDetalhadaOut(MovimentacaoOut):
    lote: LoteDetalhadoOut
    usuario: UsuarioResumo

    model_config = ConfigDict(from_attributes=True)
