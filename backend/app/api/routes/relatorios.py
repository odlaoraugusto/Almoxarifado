from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao, get_current_user
from app.api.exportacao_utils import exportar_relatorio
from app.database.session import get_db
from app.models.enums import StatusPedidoEnum, TipoMovimentacaoEnum
from app.schemas.exportacao import FormatoExportacao
from app.schemas.relatorio import (
    RelatorioEstoqueOut,
    RelatorioMovimentacoesOut,
    RelatorioPedidosOut,
    RelatorioVencimentosOut,
)
from app.schemas.usuario import UsuarioMe
from app.services.exportacao.relatorio_tabela_builder import (
    tabela_estoque,
    tabela_movimentacoes,
    tabela_pedidos,
    tabela_vencimentos,
)
from app.services.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

service = RelatorioService()

# Trilha de auditoria completa — controlada pela matriz de permissões
# (tela /permissoes, exclusiva do Admin — app/api/deps.py::exigir_permissao).
# Os demais relatórios são operacionais — Atendente e Coordenador têm
# acesso igual.
_PODE_VER_AUDITORIA = exigir_permissao("relatorio_movimentacoes")


@router.get("/pedidos", response_model=RelatorioPedidosOut)
def relatorio_pedidos(
    status: StatusPedidoEnum | None = None,
    setor_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    formato: FormatoExportacao | None = None,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """`formato` ausente (default) devolve o JSON de sempre. `formato=pdf`
    ou `formato=excel` devolve o arquivo pronto para download, com a
    mesma checagem de permissão e os mesmos filtros do endpoint JSON."""
    relatorio = service.pedidos(db, usuario, status, setor_id, data_inicio, data_fim)

    if formato is None:
        return relatorio

    return exportar_relatorio(formato, "pedidos", tabela_pedidos(relatorio))


@router.get("/estoque", response_model=RelatorioEstoqueOut)
def relatorio_estoque(
    formato: FormatoExportacao | None = None,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Posição atual de estoque (soma de lotes por item), com sinalização
    de item crítico (estoque_atual < estoque_minimo)."""
    relatorio = service.estoque(db, usuario)

    if formato is None:
        return relatorio

    return exportar_relatorio(formato, "estoque", tabela_estoque(relatorio))


@router.get("/vencimentos", response_model=RelatorioVencimentosOut)
def relatorio_vencimentos(
    dias: int = 60,
    formato: FormatoExportacao | None = None,
    usuario: UsuarioMe = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    relatorio = service.vencimentos(db, usuario, dias)

    if formato is None:
        return relatorio

    return exportar_relatorio(formato, "vencimentos", tabela_vencimentos(relatorio))


@router.get("/movimentacoes", response_model=RelatorioMovimentacoesOut)
def relatorio_movimentacoes(
    tipo: TipoMovimentacaoEnum | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    formato: FormatoExportacao | None = None,
    usuario: UsuarioMe = Depends(_PODE_VER_AUDITORIA),
    db: Session = Depends(get_db),
):
    """Trilha de auditoria completa — só Coordenador."""
    relatorio = service.movimentacoes(db, usuario, tipo, data_inicio, data_fim)

    if formato is None:
        return relatorio

    return exportar_relatorio(formato, "movimentacoes", tabela_movimentacoes(relatorio))
