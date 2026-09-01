from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.movimentacao import MovimentacaoDetalhadaOut
from app.schemas.pedido import PedidoDetalhadoOut


class RelatorioMetadados(BaseModel):
    """Cabeçalho institucional exigido em toda tela/exportação de
    relatório: hospital, organização, título, data/hora de geração e
    usuário."""

    hospital: str
    organizacao: str
    titulo_relatorio: str
    gerado_em: datetime
    gerado_por: str


class RelatorioPedidosOut(BaseModel):
    metadados: RelatorioMetadados
    periodo_inicio: date | None
    periodo_fim: date | None
    itens: list[PedidoDetalhadoOut]


class RelatorioEstoqueItem(BaseModel):
    """Uma linha por LOTE do item (2026-08-31, pedido do cliente: "mostre
    o lote também na posição de estoque") — item sem nenhum lote com
    saldo aparece como uma única linha com os campos de lote vazios, pra
    não sumir da lista (ex.: item crítico com prateleira zerada,
    exatamente o caso que mais importa destacar)."""

    item_id: int
    codigo: str
    nome: str
    categoria: str
    lote_id: int | None
    numero_lote: str | None
    data_validade: date | None
    quantidade_lote: int | None
    estoque_atual: int
    estoque_minimo: int
    critico: bool


class RelatorioEstoqueOut(BaseModel):
    metadados: RelatorioMetadados
    itens: list[RelatorioEstoqueItem]


class RelatorioVencimentoItem(BaseModel):
    """`nivel`: `vencido` | `ate_30_dias` | `31_a_60_dias` — mesmos 3
    níveis já usados na farmácia para vencimento próximo."""

    lote_id: int
    item_id: int
    item_nome: str
    numero_lote: str | None
    data_validade: date
    quantidade_atual: int
    dias_para_vencer: int
    nivel: str


class RelatorioVencimentosOut(BaseModel):
    metadados: RelatorioMetadados
    dias_considerados: int
    itens: list[RelatorioVencimentoItem]


class RelatorioMovimentacoesOut(BaseModel):
    """Trilha de auditoria completa — só Coordenador (matriz de permissões,
    docs/00_PROJETO_ALMOXARIFADO.md seção 3.3)."""

    metadados: RelatorioMetadados
    periodo_inicio: date | None
    periodo_fim: date | None
    itens: list[MovimentacaoDetalhadaOut]
