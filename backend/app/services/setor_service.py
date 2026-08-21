from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.setor import Setor
from app.repositories.setor_repository import SetorRepository
from app.schemas.setor import SetorCreate, SetorUpdate


class SetorService:
    """Cadastro de setores solicitantes — exclusivo do Coordenador
    (docs/00_PROJETO_ALMOXARIFADO.md, seção 3.4)."""

    def __init__(self):
        self.repository = SetorRepository()

    def listar(self, db: Session, incluir_inativos: bool = False) -> list[Setor]:
        return self.repository.list(db, incluir_inativos)

    def listar_publico(self, db: Session) -> list[Setor]:
        return self.repository.list(db, incluir_inativos=False)

    def criar(self, db: Session, dados: SetorCreate) -> Setor:
        if self.repository.get_by_nome(db, dados.nome):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um setor chamado '{dados.nome}'.",
            )

        return self.repository.create(db, dados.nome)

    def atualizar(self, db: Session, setor_id: int, dados: SetorUpdate) -> Setor:
        setor = self.repository.get_by_id(db, setor_id)
        if setor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Setor não encontrado."
            )

        return self.repository.update(db, setor, dados)
