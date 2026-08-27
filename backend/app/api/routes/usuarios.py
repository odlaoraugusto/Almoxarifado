from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao
from app.database.session import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioMe, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

service = UsuarioService()

# Gestão de usuários — controlada pela matriz de permissões (tela
# /permissoes, exclusiva do Admin — app/api/deps.py::exigir_permissao).
# Promover alguém a Admin, porém, é exclusivo do próprio Admin
# independente dessa matriz (ver UsuarioService.criar/atualizar).
_PODE_GERIR = exigir_permissao("gestao_usuarios")


@router.get("", response_model=list[UsuarioOut], dependencies=[Depends(_PODE_GERIR)])
def listar_usuarios(incluir_inativos: bool = False, db: Session = Depends(get_db)):
    return service.listar(db, incluir_inativos)


@router.post("", response_model=UsuarioOut, status_code=201)
def criar_usuario(
    dados: UsuarioCreate,
    usuario: UsuarioMe = Depends(_PODE_GERIR),
    db: Session = Depends(get_db),
):
    return service.criar(db, usuario, dados)


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    usuario: UsuarioMe = Depends(_PODE_GERIR),
    db: Session = Depends(get_db),
):
    return service.atualizar(db, usuario, usuario_id, dados)
