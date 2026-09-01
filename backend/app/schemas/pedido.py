from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import StatusPedidoEnum, TipoPedidoEnum
from app.schemas.item import ItemResumoOut
from app.schemas.setor import SetorPublicoOut
from app.schemas.usuario import UsuarioResumo


class PedidoItemCreate(BaseModel):
    item_id: int
    quantidade: int = Field(gt=0)


class PedidoCreate(BaseModel):
    """Criação pública (sem login) — o setor pede um ou mais itens de uma
    vez só. `tipo=entrega` (padrão) é o pedido de sempre; `tipo=devolucao`
    (2026-09-01, pedido do cliente) inverte o sentido — o setor está
    devolvendo material ao almoxarifado, não pedindo."""

    setor_id: int
    responsavel_solicitante: str
    observacao: str | None = None
    tipo: TipoPedidoEnum = TipoPedidoEnum.entrega
    itens: list[PedidoItemCreate] = Field(min_length=1)


class PedidoItemConferirCreate(BaseModel):
    """Conferência de UM item do pedido. `quantidade_entregue=0` registra
    "não atendido" (pedido) ou "não recebido de volta" (devolução), sem
    tocar em estoque; menor que `quantidade_solicitada` deixa o pedido
    como "parcial"; não pode ser maior que a solicitada.

    `item_id_entregue` é opcional — omitido (ou igual ao item
    solicitado), sem substituição. Preenchido com outro item do catálogo,
    registra uma substituição (ex.: pediram seringa com rosca, só tem com
    bico — ou, numa devolução, o setor trouxe de volta um item diferente
    do que declarou) — nesse caso `motivo_substituicao` é obrigatório
    (validado em `PedidoService.conferir_item`).

    `numero_lote`/`data_validade`/`valor_unitario` (2026-09-01, pedido do
    cliente) só se aplicam quando o PEDIDO é `tipo=devolucao` — describem
    o lote NOVO criado pela devolução (mesmos campos opcionais de
    `Lote`, nem todo material tem lote formal ou vencimento). Ignorados
    (sem efeito) numa conferência de `tipo=entrega`, que continua dando
    baixa via FEFO como sempre."""

    quantidade_entregue: int = Field(ge=0)
    item_id_entregue: int | None = None
    motivo_substituicao: str | None = None
    numero_lote: str | None = None
    data_validade: date | None = None
    valor_unitario: Decimal | None = None


class PedidoItemOut(BaseModel):
    id: int
    pedido_id: int
    item_id_solicitado: int
    quantidade_solicitada: int
    item_id_entregue: int | None
    quantidade_entregue: int | None
    motivo_substituicao: str | None

    model_config = ConfigDict(from_attributes=True)


class LoteConsumoOut(BaseModel):
    """Um lote consumido (FEFO) para dar baixa neste item de pedido — pode
    haver mais de um por item se o saldo de um lote só não bastou.
    Sobretudo importante quando houve substituição (`item_id_entregue`
    diferente de `item_id_solicitado`): mostra de qual lote/validade do
    item ENTREGUE saiu a baixa (2026-08-31, pedido do cliente)."""

    lote_id: int
    numero_lote: str | None
    data_validade: date | None
    quantidade: int


class PedidoItemDetalhadoOut(PedidoItemOut):
    item_solicitado: ItemResumoOut
    item_entregue: ItemResumoOut | None
    lotes_consumidos: list[LoteConsumoOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _computar_lotes_consumidos(cls, dados):
        """`lotes_consumidos` não é uma coluna do model `PedidoItem` — é
        agregado aqui a partir de `PedidoItem.movimentacoes` (as saídas
        ligadas a este item, uma por lote consumido via FEFO; pode haver
        mais de uma se o saldo de um lote só não bastou). Roda pra
        QUALQUER lugar que valide `PedidoItemDetalhadoOut` a partir do
        model ORM — a tela de conferência (`GET/PATCH /pedidos/...`) e o
        relatório de Pedidos — sem duplicar essa lógica nos dois lugares
        (2026-08-31, pedido do cliente: precisa aparecer na tela de
        "conferir e liberar", não só no relatório).

        Só entra em ação quando `dados` é o objeto ORM de verdade (tem
        `.movimentacoes`); construção direta via kwargs (usada em
        `RelatorioService`, que já monta `lotes_consumidos` manualmente
        antes de agrupar por pedido) passa um dict e sai no primeiro
        `return dados` — pydantic trata `Model(**kwargs)` como validação
        de um dict também, não só `model_validate(orm_obj)`."""
        if isinstance(dados, dict) or not hasattr(dados, "movimentacoes"):
            return dados

        agregados: dict[int, dict] = {}
        for mov in dados.movimentacoes:
            agregado = agregados.setdefault(
                mov.lote_id,
                {"numero_lote": mov.lote.numero_lote, "data_validade": mov.lote.data_validade, "quantidade": 0},
            )
            agregado["quantidade"] += mov.quantidade

        return {
            "id": dados.id,
            "pedido_id": dados.pedido_id,
            "item_id_solicitado": dados.item_id_solicitado,
            "quantidade_solicitada": dados.quantidade_solicitada,
            "item_id_entregue": dados.item_id_entregue,
            "quantidade_entregue": dados.quantidade_entregue,
            "motivo_substituicao": dados.motivo_substituicao,
            "item_solicitado": dados.item_solicitado,
            "item_entregue": dados.item_entregue,
            "lotes_consumidos": [
                LoteConsumoOut(lote_id=lote_id, **valores) for lote_id, valores in agregados.items()
            ],
        }


class PedidoOut(BaseModel):
    id: int
    setor_id: int
    responsavel_solicitante: str
    observacao: str | None
    tipo: TipoPedidoEnum
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
