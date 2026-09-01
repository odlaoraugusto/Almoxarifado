from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import StatusPedidoEnum, TipoMovimentacaoEnum
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.item import ItemResumoOut
from app.schemas.pedido import (
    LoteConsumoOut,
    PedidoDetalhadoOut,
    PedidoItemDetalhadoOut,
)
from app.schemas.relatorio import (
    RelatorioEstoqueItem,
    RelatorioEstoqueOut,
    RelatorioMetadados,
    RelatorioMovimentacoesOut,
    RelatorioPedidosOut,
    RelatorioVencimentoItem,
    RelatorioVencimentosOut,
)
from app.schemas.setor import SetorPublicoOut
from app.schemas.usuario import UsuarioMe, UsuarioResumo


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
        pedidos_orm = self.pedido_repository.listar(db, status_filtro, setor_id, data_inicio, data_fim)
        itens = [self._montar_pedido_detalhado(p) for p in pedidos_orm]

        return RelatorioPedidosOut(
            metadados=self._metadados(usuario, "Relatório de Pedidos"),
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            itens=itens,
        )

    @staticmethod
    def _montar_pedido_detalhado(pedido) -> PedidoDetalhadoOut:
        """Construção manual (em vez de `model_validate` direto no ORM) —
        `lotes_consumidos` não é um atributo simples do model, precisa ser
        agregado a partir de `PedidoItem.movimentacoes` (ver método
        abaixo)."""
        return PedidoDetalhadoOut(
            id=pedido.id,
            setor_id=pedido.setor_id,
            responsavel_solicitante=pedido.responsavel_solicitante,
            observacao=pedido.observacao,
            tipo=pedido.tipo,
            data_hora=pedido.data_hora,
            status=pedido.status,
            data_execucao=pedido.data_execucao,
            usuario_execucao_id=pedido.usuario_execucao_id,
            setor=SetorPublicoOut.model_validate(pedido.setor),
            usuario_execucao=(
                UsuarioResumo.model_validate(pedido.usuario_execucao)
                if pedido.usuario_execucao
                else None
            ),
            itens=[RelatorioService._montar_pedido_item_detalhado(pi) for pi in pedido.itens],
        )

    @staticmethod
    def _montar_pedido_item_detalhado(pedido_item) -> PedidoItemDetalhadoOut:
        """`lotes_consumidos`: agrega as movimentações de saída ligadas a
        este item de pedido por lote (FEFO pode ter consumido mais de um
        lote) — sobretudo importante quando houve substituição
        (`item_id_entregue` != `item_id_solicitado`), pra mostrar de qual
        lote/validade do item ENTREGUE saiu a baixa (2026-08-31, pedido
        do cliente)."""
        agregados: dict[int, dict] = {}
        for mov in pedido_item.movimentacoes:
            agregado = agregados.setdefault(
                mov.lote_id,
                {"numero_lote": mov.lote.numero_lote, "data_validade": mov.lote.data_validade, "quantidade": 0},
            )
            agregado["quantidade"] += mov.quantidade

        lotes_consumidos = [
            LoteConsumoOut(lote_id=lote_id, **dados) for lote_id, dados in agregados.items()
        ]

        return PedidoItemDetalhadoOut(
            id=pedido_item.id,
            pedido_id=pedido_item.pedido_id,
            item_id_solicitado=pedido_item.item_id_solicitado,
            quantidade_solicitada=pedido_item.quantidade_solicitada,
            item_id_entregue=pedido_item.item_id_entregue,
            quantidade_entregue=pedido_item.quantidade_entregue,
            motivo_substituicao=pedido_item.motivo_substituicao,
            item_solicitado=ItemResumoOut.model_validate(pedido_item.item_solicitado),
            item_entregue=(
                ItemResumoOut.model_validate(pedido_item.item_entregue)
                if pedido_item.item_entregue
                else None
            ),
            lotes_consumidos=lotes_consumidos,
        )

    def estoque(self, db: Session, usuario: UsuarioMe) -> RelatorioEstoqueOut:
        """Uma linha por lote com saldo (2026-08-31, pedido do cliente) —
        item sem nenhum lote de saldo vira uma linha só, com os campos de
        lote vazios, pra continuar aparecendo (ex.: crítico e zerado)."""
        catalogo = self.item_repository.list(db)
        estoque_por_item = self.item_repository.somar_estoque_por_item(db)
        lotes_por_item: dict[int, list] = {}
        for lote in self.lote_repository.listar_todos(db):
            if lote.quantidade_atual > 0:
                lotes_por_item.setdefault(lote.item_id, []).append(lote)

        itens = []
        for item in catalogo:
            if not item.ativo:
                continue

            total = estoque_por_item.get(item.id, 0)
            minimo = item.estoque_minimo
            critico = total < minimo
            lotes_do_item = lotes_por_item.get(item.id, [])

            if not lotes_do_item:
                itens.append(
                    RelatorioEstoqueItem(
                        item_id=item.id,
                        codigo=item.codigo,
                        nome=item.nome,
                        categoria=item.categoria,
                        lote_id=None,
                        numero_lote=None,
                        data_validade=None,
                        quantidade_lote=None,
                        estoque_atual=total,
                        estoque_minimo=minimo,
                        critico=critico,
                    )
                )
                continue

            for lote in lotes_do_item:
                itens.append(
                    RelatorioEstoqueItem(
                        item_id=item.id,
                        codigo=item.codigo,
                        nome=item.nome,
                        categoria=item.categoria,
                        lote_id=lote.id,
                        numero_lote=lote.numero_lote,
                        data_validade=lote.data_validade,
                        quantidade_lote=lote.quantidade_atual,
                        estoque_atual=total,
                        estoque_minimo=minimo,
                        critico=critico,
                    )
                )

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
