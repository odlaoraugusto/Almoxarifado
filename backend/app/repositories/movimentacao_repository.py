from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.enums import TipoMovimentacaoEnum
from app.models.movimentacao import Movimentacao


class MovimentacaoRepository:

    def create(self, db: Session, movimentacao: Movimentacao) -> Movimentacao:
        db.add(movimentacao)
        db.commit()
        db.refresh(movimentacao)

        return movimentacao

    def listar(
        self,
        db: Session,
        tipo: TipoMovimentacaoEnum | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> list[Movimentacao]:
        query = db.query(Movimentacao)

        if tipo is not None:
            query = query.filter(Movimentacao.tipo == tipo)

        if data_inicio is not None:
            query = query.filter(
                Movimentacao.data_hora >= datetime.combine(data_inicio, datetime.min.time())
            )

        if data_fim is not None:
            query = query.filter(
                Movimentacao.data_hora <= datetime.combine(data_fim, datetime.max.time())
            )

        return query.order_by(Movimentacao.data_hora.desc()).all()
