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
    """`pendente`: nenhum item conferido ainda. `parcial`: pelo menos um
    item conferido, mas nem todos (fila em aberto) OU todos conferidos
    porém algum entregue em quantidade menor que a solicitada.
    `executado`: todos os itens conferidos com quantidade_entregue ==
    quantidade_solicitada. Ver `PedidoService._atualizar_status_pedido`."""

    pendente = "pendente"
    parcial = "parcial"
    executado = "executado"


class TipoMovimentacaoEnum(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"
