"""Enums compartilhados entre models e schemas (docs/00_PROJETO_ALMOXARIFADO.md,
seção 4)."""

import enum


class PerfilEnum(str, enum.Enum):
    coordenador = "coordenador"
    atendente = "atendente"


class OrigemEnum(str, enum.Enum):
    compra = "compra"
    doacao = "doacao"


class StatusPedidoEnum(str, enum.Enum):
    """`executado` só é atingido quando TODOS os itens do pedido já
    passaram por conferência (`PedidoItem.quantidade_entregue is not
    None`) — ver `PedidoService.conferir_item`."""

    pendente = "pendente"
    executado = "executado"


class TipoMovimentacaoEnum(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"
