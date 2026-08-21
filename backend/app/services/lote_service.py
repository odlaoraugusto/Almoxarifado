from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.repositories.lote_repository import LoteRepository


class LoteService:
    """Consulta de lotes (estoque físico) — cadastro/baixa de lote
    acontece via Entrada (`ItemService`), Conferência (`PedidoService`)
    e Ajuste (`AjusteService`), não aqui."""

    def __init__(self):
        self.repository = LoteRepository()

    def listar(self, db: Session) -> list[Lote]:
        return self.repository.listar_todos(db)
