"""Converte cada um dos `*Out` de `app/schemas/relatorio.py` (já
validados/preenchidos pelo `RelatorioService`) numa `TabelaRelatorio`,
pronta para os exportadores (PDF/Excel) desenharem."""

from app.models.enums import CategoriaItemEnum, OrigemEnum, StatusPedidoEnum
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

_CATEGORIA_ITEM_LABEL = {
    CategoriaItemEnum.material_medico: "Material Médico",
    CategoriaItemEnum.epi: "EPI",
    CategoriaItemEnum.higienizacao: "Higienização",
    CategoriaItemEnum.expediente: "Material de Expediente",
    CategoriaItemEnum.enxoval: "Enxoval",
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
    """Uma linha por ITEM de pedido (não por pedido) — item solicitado,
    quantidade solicitada e quantidade dispensada em colunas separadas,
    pra dar pra somar/filtrar por item na planilha em vez de precisar
    ler um resumo em texto corrido. Pedidos com N itens geram N linhas,
    repetindo os dados do cabeçalho do pedido em cada uma."""
    colunas = [
        "Pedido",
        "Setor",
        "Responsável",
        "Status",
        "Item",
        "Qtd. Solicitada",
        "Qtd. Dispensada",
        "Data/Hora",
        "Executado Por",
    ]
    linhas = []
    for pedido in relatorio.itens:
        status_label = _STATUS_PEDIDO_LABEL.get(pedido.status, pedido.status.value)
        executado_por = pedido.usuario_execucao.nome if pedido.usuario_execucao else ""
        data_hora = formatar_data_hora(pedido.data_hora)
        for item in pedido.itens:
            dispensada = "" if item.quantidade_entregue is None else str(item.quantidade_entregue)
            linhas.append(
                [
                    str(pedido.id),
                    pedido.setor.nome,
                    pedido.responsavel_solicitante,
                    status_label,
                    item.item_solicitado.nome,
                    str(item.quantidade_solicitada),
                    dispensada,
                    data_hora,
                    executado_por,
                ]
            )

    return TabelaRelatorio(
        metadados=relatorio.metadados,
        colunas=colunas,
        linhas=linhas,
        informacoes_extra=_periodo_extra(relatorio.periodo_inicio, relatorio.periodo_fim),
        larguras_relativas=[0.5, 1.0, 1.1, 0.8, 1.8, 0.9, 0.9, 1.1, 1.0],
    )


def tabela_estoque(relatorio: RelatorioEstoqueOut) -> TabelaRelatorio:
    colunas = ["Código", "Item", "Categoria", "Estoque Atual", "Estoque Mínimo", "Situação"]
    linhas = [
        [
            item.codigo,
            item.nome,
            _CATEGORIA_ITEM_LABEL.get(item.categoria, str(item.categoria)),
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
