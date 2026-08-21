from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.enums import StatusPedidoEnum
from app.models.pedido import Pedido


class PedidoRepository:

    def create(self, db: Session, pedido: Pedido) -> Pedido:
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        return pedido

    def get_by_id(self, db: Session, pedido_id: int) -> Pedido | None:
        return db.query(Pedido).filter(Pedido.id == pedido_id).first()

    def get_by_id_for_update(self, db: Session, pedido_id: int) -> Pedido | None:
        """Trava a linha do pedido enquanto sua finalização (`status`) é
        recalculada em `PedidoService.conferir_item` — evita que duas
        conferências simultâneas do último item pendente marquem
        `executado` em duplicidade/condição de corrida."""
        return db.query(Pedido).filter(Pedido.id == pedido_id).with_for_update().first()

    def salvar(self, db: Session, pedido: Pedido) -> Pedido:
        db.commit()
        db.refresh(pedido)

        return pedido

    def listar(
        self,
        db: Session,
        status: StatusPedidoEnum | None = None,
        setor_id: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> list[Pedido]:
        """Equipe pequena (5 pessoas): todo mundo enxerga a fila inteira,
        sem escopo por usuário — só os filtros de query string."""
        query = db.query(Pedido)

        if status is not None:
            query = query.filter(Pedido.status == status)

        if setor_id is not None:
            query = query.filter(Pedido.setor_id == setor_id)

        if data_inicio is not None:
            query = query.filter(
                Pedido.data_hora >= datetime.combine(data_inicio, datetime.min.time())
            )

        if data_fim is not None:
            query = query.filter(
                Pedido.data_hora <= datetime.combine(data_fim, datetime.max.time())
            )

        return query.order_by(Pedido.data_hora.desc()).all()
