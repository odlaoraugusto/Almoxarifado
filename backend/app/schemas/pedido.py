from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusPedidoEnum
from app.schemas.item import ItemResumoOut
from app.schemas.setor import SetorPublicoOut
from app.schemas.usuario import UsuarioResumo


class PedidoItemCreate(BaseModel):
    item_id: int
    quantidade: int = Field(gt=0)


class PedidoCreate(BaseModel):
    """Criação pública (sem login) — o setor pede um ou mais itens de uma
    vez só."""

    setor_id: int
    responsavel_solicitante: str
    observacao: str | None = None
    itens: list[PedidoItemCreate] = Field(min_length=1)


class PedidoItemConferirCreate(BaseModel):
    """Conferência de UM item do pedido. `item_id_entregue` omitido =
    entrega o próprio item solicitado; informado e diferente do
    solicitado = substituição (exige `motivo_substituicao`).
    `quantidade_entregue=0` registra "não atendido" sem dar baixa em
    estoque."""

    item_id_entregue: int | None = None
    quantidade_entregue: int = Field(ge=0)
    motivo_substituicao: str | None = None


class PedidoItemOut(BaseModel):
    id: int
    pedido_id: int
    item_id_solicitado: int
    quantidade_solicitada: int
    item_id_entregue: int | None
    quantidade_entregue: int | None
    motivo_substituicao: str | None

    model_config = ConfigDict(from_attributes=True)


class PedidoItemDetalhadoOut(PedidoItemOut):
    item_solicitado: ItemResumoOut
    item_entregue: ItemResumoOut | None

    model_config = ConfigDict(from_attributes=True)


class PedidoOut(BaseModel):
    id: int
    setor_id: int
    responsavel_solicitante: str
    observacao: str | None
    data_hora: datetime
    status: StatusPedidoEnum
    data_execucao: datetime | None
    usuario_execucao_id: int | None

    model_config = ConfigDict(from_attributes=True)


class PedidoDetalhadoOut(PedidoOut):
    setor: SetorPublicoOut
    usuario_execucao: UsuarioResumo | None
    itens: list[PedidoItemDetalhadoOut]

    model_config = ConfigDict(from_attributes=True)
