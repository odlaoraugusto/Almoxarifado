from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao
from app.database.session import get_db
from app.schemas.movimentacao import DescarteCreate, MovimentacaoDetalhadaOut
from app.schemas.usuario import UsuarioMe
from app.services.descarte_service import DescarteService

router = APIRouter(prefix="/descartes", tags=["Descarte"])

service = DescarteService()

# Baixa por vencimento — controlada pela matriz de permissões (tela
# /permissoes, exclusiva do Admin — app/api/deps.py::exigir_permissao),
# mesmo padrão de ajustar_estoque.
_PODE_DESCARTAR = exigir_permissao("descarte_vencimento")


@router.post("", response_model=MovimentacaoDetalhadaOut)
def descartar(
    dados: DescarteCreate,
    usuario: UsuarioMe = Depends(_PODE_DESCARTAR),
    db: Session = Depends(get_db),
):
    return service.descartar(db, usuario, dados)
