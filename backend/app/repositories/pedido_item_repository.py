from sqlalchemy.orm import Session

from app.models.pedido_item import PedidoItem


class PedidoItemRepository:

    def get_by_id(self, db: Session, pedido_item_id: int) -> PedidoItem | None:
        return db.query(PedidoItem).filter(PedidoItem.id == pedido_item_id).first()

    def get_by_id_for_update(self, db: Session, pedido_item_id: int) -> PedidoItem | None:
        """`SELECT ... FOR UPDATE` — trava a linha até o fim da transação,
        evitando que dois atendentes confiram o mesmo item do pedido ao
        mesmo tempo (ex.: dando baixa em estoque duas vezes)."""
        return (
            db.query(PedidoItem)
            .filter(PedidoItem.id == pedido_item_id)
            .with_for_update()
            .first()
        )

    def listar_por_pedido(self, db: Session, pedido_id: int) -> list[PedidoItem]:
        return (
            db.query(PedidoItem)
            .filter(PedidoItem.pedido_id == pedido_id)
            .order_by(PedidoItem.id)
            .all()
        )

    def salvar(self, db: Session, pedido_item: PedidoItem) -> PedidoItem:
        db.commit()
        db.refresh(pedido_item)

        return pedido_item
