from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import TipoMovimentacaoEnum
from app.models.item import Item
from app.models.lote import Lote
from app.models.movimentacao import Movimentacao
from app.repositories.item_repository import ItemRepository
from app.repositories.lote_repository import LoteRepository
from app.repositories.movimentacao_repository import MovimentacaoRepository
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate
from app.schemas.lote import EntradaCreate
from app.schemas.usuario import UsuarioMe


class ItemService:
    """Catálogo de materiais (cadastro/edição exclusivos do Coordenador) +
    entrada de estoque (qualquer perfil autenticado registra o
    recebimento de uma compra/doação)."""

    def __init__(self):
        self.repository = ItemRepository()
        self.movimentacao_repository = MovimentacaoRepository()
        self.lote_repository = LoteRepository()

    @staticmethod
    def _para_item_out(item: Item, estoque_por_item: dict[int, int]) -> ItemOut:
        return ItemOut(
            id=item.id,
            codigo=item.codigo,
            nome=item.nome,
            apresentacao=item.apresentacao,
            categoria=item.categoria,
            estoque_minimo=item.estoque_minimo,
            ativo=item.ativo,
            fabricante=item.fabricante,
            valor_unitario=item.valor_unitario,
            estoque_atual=estoque_por_item.get(item.id, 0),
        )

    def listar(self, db: Session, incluir_inativos: bool = False) -> list[ItemOut]:
        itens = self.repository.list(db, incluir_inativos)
        estoque_por_item = self.repository.somar_estoque_por_item(db)

        return [self._para_item_out(item, estoque_por_item) for item in itens]

    def listar_publico(self, db: Session) -> list[Item]:
        return self.repository.list_publico(db)

    def obter(self, db: Session, item_id: int) -> Item:
        item = self.repository.get_by_id(db, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado."
            )

        return item

    def criar(self, db: Session, dados: ItemCreate) -> ItemOut:
        if self.repository.get_by_codigo(db, dados.codigo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um item com o código '{dados.codigo}'.",
            )

        item = self.repository.create(db, dados)
        # Item recém-criado nunca tem lote ainda — estoque_atual é sempre 0.
        return self._para_item_out(item, {})

    def atualizar(self, db: Session, item_id: int, dados: ItemUpdate) -> ItemOut:
        item = self.obter(db, item_id)

        if dados.codigo and dados.codigo != item.codigo:
            existente = self.repository.get_by_codigo(db, dados.codigo)
            if existente is not None and existente.id != item_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Já existe um item com o código '{dados.codigo}'.",
                )

        item = self.repository.update(db, item, dados)
        estoque_por_item = self.repository.somar_estoque_por_item(db)
        return self._para_item_out(item, estoque_por_item)

    def registrar_entrada(
        self, db: Session, usuario: UsuarioMe, item_id: int, dados: EntradaCreate
    ) -> Lote:
        """Se já existe um lote com a MESMA identidade física (item + nº
        de lote + validade + origem + NF/AFM), soma nele em vez de criar
        linha nova (2026-09-09, pedido do cliente: "se for o mesmo lote,
        integra aquele estoque") — ver `LoteRepository.buscar_para_merge`
        pro critério exato de "mesmo lote". Cria a `Movimentacao` de
        qualquer forma, então o rastro de auditoria por evento continua
        intacto mesmo quando o lote em si é reaproveitado."""
        item = self.obter(db, item_id)

        if not item.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível registrar entrada para um item inativo.",
            )

        lote = None
        if dados.numero_lote and dados.data_validade:
            lote = self.lote_repository.buscar_para_merge(
                db,
                item.id,
                dados.numero_lote,
                dados.data_validade,
                dados.numero_nota_fiscal,
                dados.numero_afm,
            )

        if lote is not None:
            lote.quantidade_atual += dados.quantidade
            if lote.valor_unitario is None and dados.valor_unitario is not None:
                lote.valor_unitario = dados.valor_unitario
            db.commit()
            db.refresh(lote)
        else:
            lote = Lote(
                item_id=item.id,
                numero_lote=dados.numero_lote,
                data_validade=dados.data_validade,
                quantidade_atual=dados.quantidade,
                valor_unitario=dados.valor_unitario,
                origem=dados.origem,
                numero_nota_fiscal=dados.numero_nota_fiscal,
                numero_afm=dados.numero_afm,
                usuario_entrada_id=usuario.id,
            )
            db.add(lote)
            db.commit()
            db.refresh(lote)

        movimentacao = Movimentacao(
            tipo=TipoMovimentacaoEnum.entrada,
            lote_id=lote.id,
            quantidade=dados.quantidade,
            usuario_id=usuario.id,
        )
        self.movimentacao_repository.create(db, movimentacao)

        return lote
