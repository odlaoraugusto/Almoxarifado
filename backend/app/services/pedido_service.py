from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import StatusPedidoEnum, TipoMovimentacaoEnum
from app.models.movimentacao import Movimentacao
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.repositories.pedido_item_repository import PedidoItemRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.setor_repository import SetorRepository
from app.schemas.pedido import PedidoCreate, PedidoItemConferirCreate
from app.schemas.usuario import UsuarioMe


class PedidoService:
    """Pedido de material — criado pelo formulário PÚBLICO (sem login) e
    conferido item a item pela equipe do almoxarifado
    (docs/00_PROJETO_ALMOXARIFADO.md, seção 4). `pedidos.status` só vira
    `executado` quando TODOS os itens do pedido já foram conferidos."""

    def __init__(self):
        self.pedido_repository = PedidoRepository()
        self.pedido_item_repository = PedidoItemRepository()
        self.setor_repository = SetorRepository()
        self.item_repository = ItemRepository()
        self.lote_repository = LoteRepository()
        self.movimentacao_repository = MovimentacaoRepository()

    def criar(self, db: Session, dados: PedidoCreate) -> Pedido:
        setor = self.setor_repository.get_by_id(db, dados.setor_id)
        if setor is None or not setor.ativo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setor não encontrado ou inativo.",
            )

        itens_pedido: list[PedidoItem] = []
        for item_pedido in dados.itens:
            item = self.item_repository.get_by_id(db, item_pedido.item_id)
            if item is None or not item.ativo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item id={item_pedido.item_id} não encontrado ou inativo.",
                )

            itens_pedido.append(
                PedidoItem(
                    item_id_solicitado=item.id,
                    quantidade_solicitada=item_pedido.quantidade,
                )
            )

        pedido = Pedido(
            setor_id=setor.id,
            responsavel_solicitante=dados.responsavel_solicitante.strip(),
            observacao=dados.observacao.strip() if dados.observacao else None,
            status=StatusPedidoEnum.pendente,
            itens=itens_pedido,
        )

        return self.pedido_repository.create(db, pedido)

    def listar(
        self,
        db: Session,
        status_filtro: StatusPedidoEnum | None,
        setor_id: int | None,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> list[Pedido]:
        """Equipe pequena (5 pessoas): todo mundo enxerga a fila inteira."""
        return self.pedido_repository.listar(db, status_filtro, setor_id, data_inicio, data_fim)

    def obter(self, db: Session, pedido_id: int) -> Pedido:
        pedido = self.pedido_repository.get_by_id(db, pedido_id)
        if pedido is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
            )

        return pedido

    def _consumir_fefo(
        self,
        db: Session,
        usuario: UsuarioMe,
        item_id: int,
        quantidade_necessaria: int,
        pedido_item_id: int,
    ) -> None:
        """Consome `quantidade_necessaria` unidades do item, priorizando o
        lote que vence primeiro (FEFO — First Expire, First Out, mesma
        lógica da farmácia), podendo atravessar mais de um lote. Cada
        lote tocado é travado com `SELECT ... FOR UPDATE` antes de
        decrementar, para não colidir com outra conferência/ajuste
        simultâneo no mesmo lote."""
        lotes_disponiveis = self.lote_repository.listar_fefo(db, item_id)
        total_disponivel = sum(lote.quantidade_atual for lote in lotes_disponiveis)

        if total_disponivel < quantidade_necessaria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Estoque insuficiente para o item id={item_id}: disponível "
                    f"{total_disponivel}, necessário {quantidade_necessaria}."
                ),
            )

        restante = quantidade_necessaria
        for lote_candidato in lotes_disponiveis:
            if restante <= 0:
                break

            # Trava a linha antes de decrementar — a listagem acima já
            # não tem lock, então relê o saldo travado antes de usar.
            lote = self.lote_repository.get_by_id_for_update(db, lote_candidato.id)
            if lote is None or lote.quantidade_atual <= 0:
                continue

            consumido = min(restante, lote.quantidade_atual)
            lote.quantidade_atual -= consumido
            self.lote_repository.salvar(db, lote)

            movimentacao = Movimentacao(
                tipo=TipoMovimentacaoEnum.saida,
                lote_id=lote.id,
                quantidade=consumido,
                pedido_item_id=pedido_item_id,
                usuario_id=usuario.id,
            )
            self.movimentacao_repository.create(db, movimentacao)

            restante -= consumido

        if restante > 0:
            # Condição de corrida rara: outro atendente consumiu saldo
            # entre a listagem e o lock. Falha limpa em vez de deixar o
            # pedido_item marcado como conferido sem baixa completa.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Estoque do item id={item_id} mudou durante a conferência. "
                    "Tente novamente."
                ),
            )

    def conferir_item(
        self,
        db: Session,
        usuario: UsuarioMe,
        pedido_id: int,
        pedido_item_id: int,
        dados: PedidoItemConferirCreate,
    ) -> PedidoItem:
        pedido_item = self.pedido_item_repository.get_by_id_for_update(db, pedido_item_id)
        if pedido_item is None or pedido_item.pedido_id != pedido_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item de pedido não encontrado.",
            )

        if pedido_item.quantidade_entregue is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este item já foi conferido.",
            )

        item_entregue_id = dados.item_id_entregue or pedido_item.item_id_solicitado
        eh_substituicao = item_entregue_id != pedido_item.item_id_solicitado

        if eh_substituicao and not (dados.motivo_substituicao and dados.motivo_substituicao.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="motivo_substituicao é obrigatório ao entregar um item "
                "diferente do solicitado.",
            )

        item_entregue = self.item_repository.get_by_id(db, item_entregue_id)
        if item_entregue is None or not item_entregue.ativo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item id={item_entregue_id} não encontrado ou inativo.",
            )

        # quantidade_entregue=0 registra "não atendido" (item indisponível)
        # sem tocar em estoque.
        if dados.quantidade_entregue > 0:
            self._consumir_fefo(
                db, usuario, item_entregue.id, dados.quantidade_entregue, pedido_item.id
            )

        pedido_item.item_id_entregue = item_entregue.id
        pedido_item.quantidade_entregue = dados.quantidade_entregue
        pedido_item.motivo_substituicao = (
            dados.motivo_substituicao.strip() if eh_substituicao else None
        )
        self.pedido_item_repository.salvar(db, pedido_item)

        self._finalizar_pedido_se_completo(db, usuario, pedido_id)

        return pedido_item

    def executar_direto(self, db: Session, usuario: UsuarioMe, pedido_id: int) -> Pedido:
        """Atalho de "marcar executado sem conferência item a item" — para
        o dia corrido em que o atendente confia que o pedido saiu como
        solicitado. Reaproveita `conferir_item` para cada item ainda não
        conferido (entregue = solicitado, quantidade = solicitada), então
        continua dando baixa real de estoque via FEFO — não é um atalho
        que finge a movimentação, só pula a tela item a item."""
        pedido = self.obter(db, pedido_id)

        itens_pendentes = [
            item for item in pedido.itens if item.quantidade_entregue is None
        ]
        for item in itens_pendentes:
            self.conferir_item(
                db,
                usuario,
                pedido_id,
                item.id,
                PedidoItemConferirCreate(quantidade_entregue=item.quantidade_solicitada),
            )

        return self.obter(db, pedido_id)

    def _finalizar_pedido_se_completo(self, db: Session, usuario: UsuarioMe, pedido_id: int) -> None:
        pedido = self.pedido_repository.get_by_id_for_update(db, pedido_id)
        if pedido is None or pedido.status == StatusPedidoEnum.executado:
            return

        itens = self.pedido_item_repository.listar_por_pedido(db, pedido_id)
        todos_conferidos = all(item.quantidade_entregue is not None for item in itens)

        if todos_conferidos:
            pedido.status = StatusPedidoEnum.executado
            pedido.data_execucao = datetime.now(timezone.utc)
            pedido.usuario_execucao_id = usuario.id
            self.pedido_repository.salvar(db, pedido)
