from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.repositories.lote_repository import LoteRepository
from app.schemas.lote import LoteUpdate


class LoteService:
    """Consulta de lotes (estoque físico) — cadastro/baixa de lote
    acontece via Entrada (`ItemService`), Conferência (`PedidoService`)
    e Ajuste (`AjusteService`), não aqui. `atualizar` só corrige metadado
    (valor unitário), nunca `quantidade_atual`."""

    def __init__(self):
        self.repository = LoteRepository()

    def listar(self, db: Session) -> list[Lote]:
        return self.repository.listar_todos(db)

    def atualizar(self, db: Session, lote_id: int, dados: LoteUpdate) -> Lote:
        lote = self.repository.get_by_id(db, lote_id)
        if lote is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado.")

        lote.valor_unitario = dados.valor_unitario
        return self.repository.salvar(db, lote)
