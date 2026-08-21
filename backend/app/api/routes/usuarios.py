from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfis
from app.database.session import get_db
from app.models.enums import PerfilEnum
from app.schemas.usuario import UsuarioCreate, UsuarioMe, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

service = UsuarioService()

# Gestão de usuários — exclusiva do Coordenador (matriz de permissões,
# docs/00_PROJETO_ALMOXARIFADO.md seção 3.3).
_PODE_GERIR = exigir_perfis(PerfilEnum.coordenador)


@router.get("", response_model=list[UsuarioOut], dependencies=[Depends(_PODE_GERIR)])
def listar_usuarios(incluir_inativos: bool = False, db: Session = Depends(get_db)):
    return service.listar(db, incluir_inativos)


@router.post("", response_model=UsuarioOut, status_code=201, dependencies=[Depends(_PODE_GERIR)])
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    return service.criar(db, dados)


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    usuario: UsuarioMe = Depends(_PODE_GERIR),
    db: Session = Depends(get_db),
):
    return service.atualizar(db, usuario, usuario_id, dados)
