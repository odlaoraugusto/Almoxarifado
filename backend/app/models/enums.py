"""Enums compartilhados entre models e schemas (docs/00_PROJETO_ALMOXARIFADO.md,
seção 4)."""

import enum


class PerfilEnum(str, enum.Enum):
    """`admin` é global e superusuário implícito — não entra na matriz
    configurável de `permissoes_perfil` (ver `app/api/deps.py::exigir_permissao`
    e `app/models/permissao_perfil.py`), sempre passa em qualquer checagem."""

    coordenador = "coordenador"
    atendente = "atendente"
    admin = "admin"


class OrigemEnum(str, enum.Enum):
    compra = "compra"
    doacao = "doacao"
    emprestimo = "emprestimo"
    # 2026-09-01, pedido do cliente: lote criado pela conferência de um
    # Pedido tipo=devolucao (ver TipoPedidoEnum) — o setor está devolvendo
    # material ao almoxarifado, não comprando/doando/emprestando.
    devolucao = "devolucao"


class CategoriaItemEnum(str, enum.Enum):
    """Lista fechada (pedido do cliente) — antes era texto livre. Rótulos
    de exibição em `app/services/exportacao/relatorio_tabela_builder.py`
    e no frontend (`src/lib/formato.ts`)."""

    material_medico = "material_medico"
    epi = "epi"
    higienizacao = "higienizacao"
    expediente = "expediente"
    enxoval = "enxoval"


class DirecaoEmprestimoEnum(str, enum.Enum):
    """`saida`: a gente empresta material pra uma unidade externa — baixa
    real de estoque via FEFO (`app.services.consumo_fefo`). `entrada`: a
    gente recebe de volta (devolução) ou recebe em permuta — cria
    lote(s) novo(s), `origem='emprestimo'`, igual à Entrada por compra/
    doação."""

    entrada = "entrada"
    saida = "saida"


class StatusPedidoEnum(str, enum.Enum):
    """`pendente`: nenhum item conferido ainda. `parcial`: pelo menos um
    item conferido, mas nem todos (fila em aberto) OU todos conferidos
    porém algum entregue em quantidade menor que a solicitada.
    `executado`: todos os itens conferidos com quantidade_entregue ==
    quantidade_solicitada. Ver `PedidoService._atualizar_status_pedido`."""

    pendente = "pendente"
    parcial = "parcial"
    executado = "executado"


class TipoPedidoEnum(str, enum.Enum):
    """`entrega` (padrão): o setor está pedindo material do almoxarifado —
    a conferência dá baixa real de estoque via FEFO, igual sempre foi.
    `devolucao` (2026-09-01, pedido do cliente): o setor está devolvendo
    material ao almoxarifado — a conferência cria lote(s) novo(s) em vez
    de baixar estoque, igual a uma Entrada (ver
    `PedidoService.conferir_item`)."""

    entrega = "entrega"
    devolucao = "devolucao"


class TipoMovimentacaoEnum(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"
    # Baixa de lote vencido (2026-09-02, pedido do cliente) — trilha
    # própria, separada de `ajuste` (que é correção de contagem física,
    # pode ir pra cima ou pra baixo). Descarte SEMPRE reduz, sempre com
    # `motivo_descarte` preenchido (ver DescarteService.descartar).
    descarte = "descarte"
