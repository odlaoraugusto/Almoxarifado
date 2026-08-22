"""Converte cada um dos `*Out` de `app/schemas/relatorio.py` (já
validados/preenchidos pelo `RelatorioService`) numa `TabelaRelatorio`,
pronta para os exportadores (PDF/Excel) desenharem."""

from app.models.enums import OrigemEnum, StatusPedidoEnum
from app.schemas.relatorio import (
    RelatorioEstoqueOut,
    RelatorioMovimentacoesOut,
    RelatorioPedidosOut,
    RelatorioVencimentosOut,
)
from app.services.exportacao.formatacao import formatar_data, formatar_data_hora
from app.services.exportacao.tabela import TabelaRelatorio

_ORIGEM_LABEL = {
    OrigemEnum.compra: "Compra",
    OrigemEnum.doacao: "Doação",
}

_STATUS_PEDIDO_LABEL = {
    StatusPedidoEnum.pendente: "Pendente",
    StatusPedidoEnum.parcial: "Parcial",
    StatusPedidoEnum.executado: "Executado",
}


def _texto(valor) -> str:
    return "" if valor is None else str(valor)


def _periodo_extra(periodo_inicio, periodo_fim) -> list[str]:
    if not periodo_inicio and not periodo_fim:
        return []

    inicio = formatar_data(periodo_inicio) or "início do histórico"
    fim = formatar_data(periodo_fim) or "hoje"
    return [f"Período considerado: {inicio} até {fim}"]


def tabela_pedidos(relatorio: RelatorioPedidosOut) -> TabelaRelatorio:
    colunas = [
        "Pedido",
        "Setor",
        "Responsável",
        "Status",
        "Itens (solicitado -> entregue)",
        "Data/Hora",
        "Executado Por",
    ]
    linhas = []
    for pedido in relatorio.itens:
        resumo_itens = "; ".join(
            f"{item.item_solicitado.nome} (pediu {item.quantidade_solicitada}"
            + (
                f", entregou {item.quantidade_entregue}"
                + (
                    f" de {item.item_entregue.nome}"
                    if item.item_entregue and item.item_entregue.id != item.item_solicitado.id
                    else ""
                )
                if item.quantidade_entregue is not None
                else ", aguardando conferência"
            )
            + ")"
            for item in pedido.itens
        )
        linhas.append(
            [
                str(pedido.id),
                pedido.setor.nome,
                pedido.responsavel_solicitante,
                _STATUS_PEDIDO_LABEL.get(pedido.status, pedido.status.value),
                resumo_itens,
                formatar_data_hora(pedido.data_hora),
                pedido.usuario_execucao.nome if pedido.usuario_execucao else "",
            ]
        )

    return TabelaRelatorio(
        metadados=relatorio.metadados,
        colunas=colunas,
        linhas=linhas,
        informacoes_extra=_periodo_extra(relatorio.periodo_inicio, relatorio.periodo_fim),
        larguras_relativas=[0.6, 1.1, 1.2, 0.9, 2.6, 1.1, 1.1],
    )


def tabela_estoque(relatorio: RelatorioEstoqueOut) -> TabelaRelatorio:
    colunas = ["Código", "Item", "Categoria", "Estoque Atual", "Estoque Mínimo", "Situação"]
    linhas = [
        [
            item.codigo,
            item.nome,
            item.categoria,
            str(item.estoque_atual),
            str(item.estoque_minimo),
            "CRÍTICO" if item.critico else "OK",
        ]
        for item in relatorio.itens
    ]

    return TabelaRelatorio(
        metadados=relatorio.metadados,
        colunas=colunas,
        linhas=linhas,
        larguras_relativas=[0.9, 2.0, 1.2, 1.0, 1.0, 0.9],
    )


def tabela_vencimentos(relatorio: RelatorioVencimentosOut) -> TabelaRelatorio:
    colunas = ["Item", "Nº Lote", "Validade", "Qtd. Atual", "Dias p/ Vencer", "Situação"]
    linhas = [
        [
            item.item_nome,
            _texto(item.numero_lote),
            formatar_data(item.data_validade),
            str(item.quantidade_atual),
            str(item.dias_para_vencer),
            item.nivel.replace("_", " ").upper(),
        ]
        for item in relatorio.itens
    ]

    return TabelaRelatorio(
        metadados=relatorio.metadados,
        colunas=colunas,
        linhas=linhas,
        informacoes_extra=[
            f"Considerando lotes que vencem nos próximos {relatorio.dias_considerados} dias "
            "(ou já vencidos)"
        ],
        larguras_relativas=[1.8, 1.0, 1.0, 0.9, 1.1, 1.1],
    )


def tabela_movimentacoes(relatorio: RelatorioMovimentacoesOut) -> TabelaRelatorio:
    colunas = ["Data/Hora", "Tipo", "Item", "Nº Lote", "Quantidade", "Motivo Ajuste", "Usuário"]
    linhas = [
        [
            formatar_data_hora(m.data_hora),
            m.tipo.value.upper(),
            m.lote.item.nome,
            _texto(m.lote.numero_lote),
            str(m.quantidade),
            _texto(m.motivo_ajuste),
            m.usuario.nome,
        ]
        for m in relatorio.itens
    ]

    return TabelaRelatorio(
        metadados=relatorio.metadados,
        colunas=colunas,
        linhas=linhas,
        informacoes_extra=_periodo_extra(relatorio.periodo_inicio, relatorio.periodo_fim),
        larguras_relativas=[1.3, 0.8, 1.8, 0.9, 0.9, 1.6, 1.1],
    )
