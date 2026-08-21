from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import StatusPedidoEnum, TipoMovimentacaoEnum
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.relatorio import (
    RelatorioEstoqueItem,
    RelatorioEstoqueOut,
    RelatorioMetadados,
    RelatorioMovimentacoesOut,
    RelatorioPedidosOut,
    RelatorioVencimentoItem,
    RelatorioVencimentosOut,
)
from app.schemas.usuario import UsuarioMe


class RelatorioService:
    """Monta os dados + o cabeçalho institucional (`RelatorioMetadados`)
    de cada relatório — a exportação em PDF/Excel em si mora em
    `app/services/exportacao/`."""

    def __init__(self):
        self.pedido_repository = PedidoRepository()
        self.item_repository = ItemRepository()
        self.lote_repository = LoteRepository()
        self.movimentacao_repository = MovimentacaoRepository()

    def _metadados(self, usuario: UsuarioMe, titulo: str) -> RelatorioMetadados:
        return RelatorioMetadados(
            hospital=settings.HOSPITAL_NOME,
            organizacao=settings.HOSPITAL_ORGANIZACAO,
            titulo_relatorio=titulo,
            gerado_em=datetime.now(timezone.utc),
            gerado_por=usuario.nome,
        )

    def pedidos(
        self,
        db: Session,
        usuario: UsuarioMe,
        status_filtro: StatusPedidoEnum | None,
        setor_id: int | None,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> RelatorioPedidosOut:
        itens = self.pedido_repository.listar(db, status_filtro, setor_id, data_inicio, data_fim)

        return RelatorioPedidosOut(
            metadados=self._metadados(usuario, "Relatório de Pedidos"),
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            itens=itens,
        )

    def estoque(self, db: Session, usuario: UsuarioMe) -> RelatorioEstoqueOut:
        catalogo = self.item_repository.list(db)
        estoque_por_item = self.item_repository.somar_estoque_por_item(db)

        itens = [
            RelatorioEstoqueItem(
                item_id=item.id,
                codigo=item.codigo,
                nome=item.nome,
                categoria=item.categoria,
                estoque_atual=estoque_por_item.get(item.id, 0),
                estoque_minimo=item.estoque_minimo,
                critico=estoque_por_item.get(item.id, 0) < item.estoque_minimo,
            )
            for item in catalogo
            if item.ativo
        ]

        return RelatorioEstoqueOut(
            metadados=self._metadados(usuario, "Posição de Estoque"),
            itens=itens,
        )

    def vencimentos(self, db: Session, usuario: UsuarioMe, dias: int = 60) -> RelatorioVencimentosOut:
        """3 níveis: `vencido` (já passou da validade), `ate_30_dias`,
        `31_a_60_dias` — mesma janela já usada no projeto irmão
        (farmácia) para vencimento próximo."""
        lotes = self.lote_repository.listar_vencimento_proximo(db, dias)
        hoje = date.today()

        itens = []
        for lote in lotes:
            dias_para_vencer = (lote.data_validade - hoje).days

            if dias_para_vencer < 0:
                nivel = "vencido"
            elif dias_para_vencer <= 30:
                nivel = "ate_30_dias"
            else:
                nivel = "31_a_60_dias"

            itens.append(
                RelatorioVencimentoItem(
                    lote_id=lote.id,
                    item_id=lote.item_id,
                    item_nome=lote.item.nome,
                    numero_lote=lote.numero_lote,
                    data_validade=lote.data_validade,
                    quantidade_atual=lote.quantidade_atual,
                    dias_para_vencer=dias_para_vencer,
                    nivel=nivel,
                )
            )

        return RelatorioVencimentosOut(
            metadados=self._metadados(usuario, "Vencimentos Próximos"),
            dias_considerados=dias,
            itens=itens,
        )

    def movimentacoes(
        self,
        db: Session,
        usuario: UsuarioMe,
        tipo: TipoMovimentacaoEnum | None,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> RelatorioMovimentacoesOut:
        """Trilha de auditoria completa — só Coordenador (checado no
        router, `exigir_perfis(PerfilEnum.coordenador)`)."""
        itens = self.movimentacao_repository.listar(db, tipo, data_inicio, data_fim)

        return RelatorioMovimentacoesOut(
            metadados=self._metadados(usuario, "Trilha de Auditoria de Estoque"),
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            itens=itens,
        )
