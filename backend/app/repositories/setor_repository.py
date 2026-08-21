from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.setor import Setor
from app.schemas.setor import SetorUpdate


class SetorRepository:

    def create(self, db: Session, nome: str) -> Setor:
        setor = Setor(nome=nome, ativo=True)

        db.add(setor)
        db.commit()
        db.refresh(setor)

        return setor

    def get_by_id(self, db: Session, setor_id: int) -> Setor | None:
        return db.query(Setor).filter(Setor.id == setor_id).first()

    def get_by_nome(self, db: Session, nome: str) -> Setor | None:
        return db.query(Setor).filter(Setor.nome == nome).first()

    def list(self, db: Session, incluir_inativos: bool = False) -> list[Setor]:
        query = db.query(Setor)

        if not incluir_inativos:
            query = query.filter(Setor.ativo.is_(True))

        return query.order_by(Setor.nome).all()

    def update(self, db: Session, setor: Setor, dados: SetorUpdate) -> Setor:
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(setor, campo, valor)

        db.commit()
        db.refresh(setor)

        return setor
