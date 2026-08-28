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
    """Conferência de UM item do pedido. `quantidade_entregue=0` registra
    "não atendido" sem dar baixa em estoque; menor que
    `quantidade_solicitada` deixa o pedido como "parcial"; não pode ser
    maior que a solicitada.

    `item_id_entregue` é opcional — omitido (ou igual ao item
    solicitado), entrega normal, sem substituição. Preenchido com outro
    item do catálogo, registra uma substituição (ex.: pediram seringa
    com rosca, só tem com bico) — nesse caso `motivo_substituicao` é
    obrigatório (validado em `PedidoService.conferir_item`), e a baixa
    de estoque (FEFO) sai do item ENTREGUE, não do solicitado."""

    quantidade_entregue: int = Field(ge=0)
    item_id_entregue: int | None = None
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
