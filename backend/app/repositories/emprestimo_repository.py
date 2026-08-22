from sqlalchemy.orm import Session

from app.models.emprestimo import RegistroEmprestimo


class EmprestimoRepository:

    def create(self, db: Session, registro: RegistroEmprestimo) -> RegistroEmprestimo:
        db.add(registro)
        db.commit()
        db.refresh(registro)

        return registro

    def get_by_id(self, db: Session, emprestimo_id: int) -> RegistroEmprestimo | None:
        return (
            db.query(RegistroEmprestimo)
            .filter(RegistroEmprestimo.id == emprestimo_id)
            .first()
        )

    def listar(self, db: Session) -> list[RegistroEmprestimo]:
        """Mais recentes primeiro — histórico/rastreabilidade completo,
        sem filtro (equipe pequena, mesmo critério de
        `PedidoRepository.listar`/`GET /pedidos`)."""
        return db.query(RegistroEmprestimo).order_by(RegistroEmprestimo.data_hora.desc()).all()
