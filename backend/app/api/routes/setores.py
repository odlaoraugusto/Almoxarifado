from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfis, get_current_user
from app.database.session import get_db
from app.models.enums import PerfilEnum
from app.schemas.setor import SetorCreate, SetorOut, SetorPublicoOut, SetorUpdate
from app.services.setor_service import SetorService

router = APIRouter(prefix="/setores", tags=["Setores"])

service = SetorService()

# Cadastro de setores — exclusivo do Coordenador (matriz de permissões,
# docs/00_PROJETO_ALMOXARIFADO.md seção 3.3).
_PODE_GERIR = exigir_perfis(PerfilEnum.coordenador)


@router.get("/publico", response_model=list[SetorPublicoOut])
def listar_setores_publico(db: Session = Depends(get_db)):
    """Sem autenticação — alimenta o <select> de setor do formulário
    público de pedido."""
    return service.listar_publico(db)


@router.get("", response_model=list[SetorOut], dependencies=[Depends(get_current_user)])
def listar_setores(incluir_inativos: bool = False, db: Session = Depends(get_db)):
    return service.listar(db, incluir_inativos)


@router.post("", response_model=SetorOut, status_code=201, dependencies=[Depends(_PODE_GERIR)])
def criar_setor(dados: SetorCreate, db: Session = Depends(get_db)):
    return service.criar(db, dados)


@router.put("/{setor_id}", response_model=SetorOut, dependencies=[Depends(_PODE_GERIR)])
def atualizar_setor(setor_id: int, dados: SetorUpdate, db: Session = Depends(get_db)):
    return service.atualizar(db, setor_id, dados)
