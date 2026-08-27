from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import exigir_permissao
from app.database.session import get_db
from app.schemas.movimentacao import AjusteCreate, MovimentacaoDetalhadaOut
from app.schemas.usuario import UsuarioMe
from app.services.ajuste_service import AjusteService

router = APIRouter(prefix="/ajustes", tags=["Ajustes"])

service = AjusteService()

# Ajuste de estoque — controlado pela matriz de permissões (tela
# /permissoes, exclusiva do Admin — app/api/deps.py::exigir_permissao):
# corrige saldo fora dos fluxos normais (ex. divergência de contagem física).
_PODE_AJUSTAR = exigir_permissao("ajustar_estoque")


@router.post("", response_model=MovimentacaoDetalhadaOut)
def ajustar_estoque(
    dados: AjusteCreate,
    usuario: UsuarioMe = Depends(_PODE_AJUSTAR),
    db: Session = Depends(get_db),
):
    return service.ajustar(db, usuario, dados)
