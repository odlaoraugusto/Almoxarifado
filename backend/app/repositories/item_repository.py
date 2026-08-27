from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.lote import Lote
from app.schemas.item import ItemCreate, ItemUpdate


class ItemRepository:

    def create(self, db: Session, dados: ItemCreate) -> Item:
        item = Item(
            codigo=dados.codigo,
            nome=dados.nome,
            apresentacao=dados.apresentacao,
            categoria=dados.categoria,
            estoque_minimo=dados.estoque_minimo,
            fabricante=dados.fabricante,
            ativo=True,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return item

    def get_by_id(self, db: Session, item_id: int) -> Item | None:
        return db.query(Item).filter(Item.id == item_id).first()

    def get_by_codigo(self, db: Session, codigo: str) -> Item | None:
        return db.query(Item).filter(Item.codigo == codigo).first()

    def list(self, db: Session, incluir_inativos: bool = False) -> list[Item]:
        query = db.query(Item)
        if not incluir_inativos:
            query = query.filter(Item.ativo.is_(True))
        return query.order_by(Item.nome).all()

    def list_publico(self, db: Session) -> list[Item]:
        """Só itens ativos — alimenta o formulário público de pedido, sem
        expor estoque (ver ItemPublicoOut)."""
        return db.query(Item).filter(Item.ativo.is_(True)).order_by(Item.nome).all()

    def somar_estoque_por_item(self, db: Session) -> dict[int, int]:
        """`item_id -> soma de Lote.quantidade_atual` de todos os lotes
        daquele item — o saldo em si não é uma coluna de `Item` (mora em
        `Lote`, docs/00_PROJETO_ALMOXARIFADO.md seção 4)."""
        linhas = (
            db.query(Lote.item_id, func.coalesce(func.sum(Lote.quantidade_atual), 0))
            .group_by(Lote.item_id)
            .all()
        )
        return dict(linhas)

    def update(self, db: Session, item: Item, dados: ItemUpdate) -> Item:
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(item, campo, valor)

        db.commit()
        db.refresh(item)

        return item
