from datetime import date

from sqlalchemy import nulls_last
from sqlalchemy.orm import Session

from app.models.lote import Lote


class LoteRepository:

    def create(self, db: Session, lote: Lote) -> Lote:
        db.add(lote)
        db.commit()
        db.refresh(lote)

        return lote

    def get_by_id(self, db: Session, lote_id: int) -> Lote | None:
        return db.query(Lote).filter(Lote.id == lote_id).first()

    def get_by_id_for_update(self, db: Session, lote_id: int) -> Lote | None:
        """Bloqueia a linha do lote até o fim da transação (`SELECT ...
        FOR UPDATE`) — evita duas conferências/ajustes decrementando o
        mesmo lote ao mesmo tempo.

        `.populate_existing()` é obrigatório aqui: sem ele, se este
        `Lote` já estava carregado na identity map da sessão (ex.:
        `listar_fefo` rodou segundos antes, sem lock, no mesmo request),
        o SQLAlchemy devolve o objeto Python em cache — SEM reler os
        valores da linha que o `FOR UPDATE` acabou de travar/buscar —
        mesmo a trava do Postgres estando correta. Resultado: duas
        requisições concorrentes na mesma linha calculam o decremento em
        cima do MESMO valor "stale", e uma sobrescreve a baixa da outra
        (lost update), apesar do lock a nível de banco ter funcionado
        certinho. Achado real rodando teste de carga com concorrência de
        verdade (não aparece com requisições sequenciais) — ver
        docs/00_PROJETO_ALMOXARIFADO.md ou o histórico do repositório."""
        return (
            db.query(Lote)
            .filter(Lote.id == lote_id)
            .populate_existing()
            .with_for_update()
            .first()
        )

    def listar_fefo(self, db: Session, item_id: int) -> list[Lote]:
        """Lotes com saldo > 0 do item, ordenados FEFO (First Expire,
        First Out) — lotes sem `data_validade` (material que não vence)
        vão por último, consumidos só depois de esgotar os que têm prazo.
        Usado na conferência de pedido para decidir de qual(is) lote(s)
        dar baixa."""
        return (
            db.query(Lote)
            .filter(Lote.item_id == item_id, Lote.quantidade_atual > 0)
            .order_by(nulls_last(Lote.data_validade.asc()))
            .all()
        )

    def listar_todos(self, db: Session) -> list[Lote]:
        """Todos os lotes (qualquer item, incluindo saldo zerado) — usado
        na tela de Estoque para mostrar a lista completa de lotes ao
        pessoal autenticado."""
        return db.query(Lote).order_by(Lote.data_entrada.desc()).all()

    def listar_por_item(self, db: Session, item_id: int) -> list[Lote]:
        return db.query(Lote).filter(Lote.item_id == item_id).order_by(Lote.data_entrada).all()

    def listar_vencimento_proximo(self, db: Session, dias: int) -> list[Lote]:
        from datetime import timedelta

        limite = date.today() + timedelta(days=dias)

        return (
            db.query(Lote)
            .filter(
                Lote.quantidade_atual > 0,
                Lote.data_validade.isnot(None),
                Lote.data_validade <= limite,
            )
            .order_by(Lote.data_validade.asc())
            .all()
        )

    def salvar(self, db: Session, lote: Lote) -> Lote:
        db.commit()
        db.refresh(lote)

        return lote
