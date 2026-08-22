from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.emprestimo import RegistroEmprestimo
from app.models.enums import DirecaoEmprestimoEnum, OrigemEnum, TipoMovimentacaoEnum
from app.models.lote import Lote
from app.models.movimentacao import Movimentacao
from app.repositories.emprestimo_repository import EmprestimoRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.emprestimo import EmprestimoCreate, EmprestimoDetalheItemOut, EmprestimoOut
from app.schemas.item import ItemResumoOut
from app.schemas.usuario import UsuarioMe
from app.services.consumo_fefo import consumir_fefo


class EmprestimoService:
    """Empréstimo/permuta de material com uma unidade EXTERNA (fora do
    catálogo de `setores`, ver `app/models/emprestimo.py`). `saida`
    consome estoque via FEFO (mesma função compartilhada de
    `PedidoService`); `entrada` cria lote(s) novo(s), `origem='emprestimo'`,
    igual à Entrada por compra/doação registrada em `ItemService`."""

    def __init__(self):
        self.emprestimo_repository = EmprestimoRepository()
        self.item_repository = ItemRepository()
        self.lote_repository = LoteRepository()
        self.movimentacao_repository = MovimentacaoRepository()

    def criar(self, db: Session, usuario: UsuarioMe, dados: EmprestimoCreate) -> EmprestimoOut:
        # Valida todos os itens ANTES de criar qualquer registro — mesma
        # ordem de PedidoService.criar (falha limpa sem deixar um
        # RegistroEmprestimo órfão se um item no meio da lista for
        # inválido).
        for item_dados in dados.itens:
            item = self.item_repository.get_by_id(db, item_dados.item_id)
            if item is None or not item.ativo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item id={item_dados.item_id} não encontrado ou inativo.",
                )

        registro = self.emprestimo_repository.create(
            db,
            RegistroEmprestimo(
                direcao=dados.direcao,
                unidade_origem=dados.unidade_origem.strip(),
                numero_oficio=dados.numero_oficio.strip() if dados.numero_oficio else None,
                usuario_id=usuario.id,
            ),
        )

        if dados.direcao == DirecaoEmprestimoEnum.entrada:
            detalhes = self._processar_entrada(db, usuario, registro, dados)
        else:
            detalhes = self._processar_saida(db, usuario, registro, dados)

        return self._para_out(registro, detalhes)

    def _processar_entrada(
        self,
        db: Session,
        usuario: UsuarioMe,
        registro: RegistroEmprestimo,
        dados: EmprestimoCreate,
    ) -> list[EmprestimoDetalheItemOut]:
        """Devolução ou recebimento em permuta — cria um LOTE novo por
        item (nunca incrementa um lote existente, mesmo padrão da Entrada
        por compra/doação em `ItemService.registrar_entrada`)."""
        detalhes: list[EmprestimoDetalheItemOut] = []

        for item_dados in dados.itens:
            lote = Lote(
                item_id=item_dados.item_id,
                numero_lote=item_dados.numero_lote,
                data_validade=item_dados.data_validade,
                quantidade_atual=item_dados.quantidade,
                valor_unitario=item_dados.valor_unitario,
                origem=OrigemEnum.emprestimo,
                emprestimo_id=registro.id,
                usuario_entrada_id=usuario.id,
            )
            lote = self.lote_repository.create(db, lote)

            movimentacao = Movimentacao(
                tipo=TipoMovimentacaoEnum.entrada,
                lote_id=lote.id,
                quantidade=item_dados.quantidade,
                usuario_id=usuario.id,
            )
            self.movimentacao_repository.create(db, movimentacao)

            detalhes.append(
                EmprestimoDetalheItemOut(
                    item=ItemResumoOut.model_validate(lote.item),
                    quantidade=lote.quantidade_atual,
                    lote_id=lote.id,
                )
            )

        return detalhes

    def _processar_saida(
        self,
        db: Session,
        usuario: UsuarioMe,
        registro: RegistroEmprestimo,
        dados: EmprestimoCreate,
    ) -> list[EmprestimoDetalheItemOut]:
        """Empréstimo enviado pra fora — dá baixa real de estoque via
        FEFO, mesma checagem de estoque insuficiente (400) usada na
        conferência de pedido."""
        for item_dados in dados.itens:
            consumir_fefo(
                db,
                self.lote_repository,
                self.movimentacao_repository,
                usuario.id,
                item_dados.item_id,
                item_dados.quantidade,
                emprestimo_id=registro.id,
            )

        # Relê do banco em vez de acumular em memória: um único item
        # pedido pode ter atravessado mais de um lote (FEFO), gerando
        # mais de uma linha de Movimentacao para o mesmo item_id.
        movimentacoes = self.movimentacao_repository.listar_por_emprestimo(db, registro.id)

        return [
            EmprestimoDetalheItemOut(
                item=ItemResumoOut.model_validate(movimentacao.lote.item),
                quantidade=movimentacao.quantidade,
                movimentacao_id=movimentacao.id,
            )
            for movimentacao in movimentacoes
        ]

    def listar(self, db: Session) -> list[EmprestimoOut]:
        """Histórico completo, mais recentes primeiro — equipe pequena,
        todo mundo enxerga tudo (mesmo critério de `GET /pedidos`)."""
        registros = self.emprestimo_repository.listar(db)
        return [self._para_out(registro, self._detalhes_de(registro)) for registro in registros]

    def _detalhes_de(self, registro: RegistroEmprestimo) -> list[EmprestimoDetalheItemOut]:
        if registro.direcao == DirecaoEmprestimoEnum.entrada:
            return [
                EmprestimoDetalheItemOut(
                    item=ItemResumoOut.model_validate(lote.item),
                    quantidade=lote.quantidade_atual,
                    lote_id=lote.id,
                )
                for lote in registro.lotes_criados
            ]

        return [
            EmprestimoDetalheItemOut(
                item=ItemResumoOut.model_validate(movimentacao.lote.item),
                quantidade=movimentacao.quantidade,
                movimentacao_id=movimentacao.id,
            )
            for movimentacao in registro.movimentacoes
        ]

    @staticmethod
    def _para_out(
        registro: RegistroEmprestimo, detalhes: list[EmprestimoDetalheItemOut]
    ) -> EmprestimoOut:
        return EmprestimoOut(
            id=registro.id,
            direcao=registro.direcao,
            unidade_origem=registro.unidade_origem,
            numero_oficio=registro.numero_oficio,
            usuario_id=registro.usuario_id,
            data_hora=registro.data_hora,
            itens=detalhes,
        )
